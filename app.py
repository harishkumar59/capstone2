import io
import os
import tempfile
import time
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from google import genai
from google.genai import types
from google.genai.version import __version__ as genai_version


load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")

MIN_GENAI_VERSION = (1, 50, 0)


def _parse_version(version_str: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in version_str.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            break
    return tuple(parts)


def _ensure_dependencies():
    if _parse_version(genai_version) < MIN_GENAI_VERSION:
        raise RuntimeError(
            "google-genai >= 1.50.0 is required for video generation. "
            f"Detected version {genai_version}. "
            "Run `pip install --upgrade google-genai` inside your virtual env."
        )

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing GOOGLE_API_KEY. Set it in a .env file or as an environment variable."
        )

    return api_key


GOOGLE_API_KEY = _ensure_dependencies()
client = genai.Client(api_key=GOOGLE_API_KEY)


def wait_for_operation(operation, timeout: int = 600, poll_interval: int = 5):
    """Polls the Google GenAI operation until it completes or the timeout is hit."""
    deadline = time.time() + timeout

    while not operation.done:
        if time.time() > deadline:
            raise TimeoutError("Video generation operation timed out.")

        time.sleep(poll_interval)
        operation = client.operations.get(operation)

    return operation


def build_config(
    negative_prompt: Optional[str], aspect_ratio: Optional[str], resolution: Optional[str]
):
    """Constructs the GenerateVideosConfig with sane defaults."""
    config_kwargs = {}

    if negative_prompt:
        config_kwargs["negative_prompt"] = negative_prompt

    if aspect_ratio:
        config_kwargs["aspect_ratio"] = aspect_ratio

    if resolution:
        config_kwargs["resolution"] = resolution

    return types.GenerateVideosConfig(**config_kwargs)


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/generate")
def generate_video():
    data = request.get_json(force=True, silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400

    aspect_ratio = data.get("aspect_ratio") or "9:16"
    resolution = data.get("resolution") or "720p"
    negative_prompt = (data.get("negative_prompt") or "").strip() or None
    model = data.get("model") or "veo-3.1-fast-generate-preview"

    try:
        operation = client.models.generate_videos(
            model=model,
            prompt=prompt,
            config=build_config(
                negative_prompt=negative_prompt,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
            ),
        )

        operation = wait_for_operation(operation)
        generated_videos = getattr(operation.response, "generated_videos", [])

        if not generated_videos:
            return jsonify({"error": "No video returned from the model."}), 502

        generated_video = generated_videos[0]
        client.files.download(file=generated_video.video)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        generated_video.video.save(tmp_path)

        with open(tmp_path, "rb") as video_file:
            video_bytes = video_file.read()

        os.remove(tmp_path)

        buffer = io.BytesIO(video_bytes)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype="video/mp4",
            as_attachment=False,
            download_name="ai-generated-video.mp4",
        )

    except TimeoutError as err:
        return jsonify({"error": str(err)}), 504
    except Exception as err:  # pylint: disable=broad-except
        return jsonify({"error": f"Video generation failed: {err}"}), 500


if __name__ == "__main__":
    app.run(debug=True)

