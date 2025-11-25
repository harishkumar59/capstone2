"use strict";

const form = document.getElementById("video-form");
const promptInput = document.getElementById("prompt");
const negativeInput = document.getElementById("negative_prompt");
const aspectSelect = document.getElementById("aspect_ratio");
const resolutionSelect = document.getElementById("resolution");
const statusEl = document.getElementById("status");
const generateBtn = document.getElementById("generate-btn");
const downloadBtn = document.getElementById("download-btn");
const videoEl = document.getElementById("result-video");
const placeholderEl = document.getElementById("placeholder");

let currentObjectUrl = null;

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#ff7b7b" : "#c7cfe2";
}

function toggleLoading(isLoading) {
  generateBtn.disabled = isLoading;
  generateBtn.textContent = isLoading ? "Generating..." : "Generate video";
  downloadBtn.disabled = isLoading || !videoEl.src;
}

function showVideo(blob) {
  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
  }

  currentObjectUrl = URL.createObjectURL(blob);
  videoEl.src = currentObjectUrl;
  videoEl.hidden = false;
  placeholderEl.hidden = true;
  downloadBtn.disabled = false;
}

downloadBtn.addEventListener("click", () => {
  if (!currentObjectUrl) return;

  const link = document.createElement("a");
  link.href = currentObjectUrl;
  link.download = "ai-generated-video.mp4";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const prompt = promptInput.value.trim();
  if (!prompt) {
    setStatus("Please enter a prompt.", true);
    return;
  }

  toggleLoading(true);
  setStatus("Spinning up the Veo model. This can take up to a minute...");

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt,
        negative_prompt: negativeInput.value,
        aspect_ratio: aspectSelect.value,
        resolution: resolutionSelect.value,
      }),
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.error || "Generation failed.");
    }

    const blob = await response.blob();
    showVideo(blob);
    setStatus("Done! Enjoy your new clip.");
  } catch (error) {
    console.error(error);
    setStatus(error.message || "Something went wrong.", true);
  } finally {
    toggleLoading(false);
  }
});

