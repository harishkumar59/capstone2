# AI Video Generator

A lightweight Flask application that turns text prompts into short videos using Google's Veo 3.1 fast preview model from the `google-genai` SDK.

## Prerequisites

- Python 3.11+
- Google AI Studio API key with access to video generation (set as `GOOGLE_API_KEY`)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
copy env.example .env          # then edit with your key
```

If you already created the virtual environment before this update, be sure to
upgrade `google-genai` to at least `1.50.1`, otherwise the Veo video endpoint
isn't available:

```bash
pip install --upgrade google-genai
```

Update `.env` with your API key:

```
GOOGLE_API_KEY=your-key-here
```

## Run the app

```bash
flask --app app run
```

Open `http://127.0.0.1:5000` and enter a prompt. Generation can take 30–60 seconds. When it finishes, the video preview and download button will be enabled.

## Notes

- The backend keeps the request open while it waits for the model to finish. For production, switch to an async worker or background job queue.
- Generated videos are streamed back to the browser and never written permanently to disk.

