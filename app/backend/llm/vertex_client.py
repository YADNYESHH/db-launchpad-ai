"""Vertex AI Gemini client for RM-brief narrative generation ONLY.

Per doc ARCH-01 ("separate deterministic scoring from LLM-generated
narrative"), this module never influences a score or a priority band — it
only rephrases already-computed, already-approved-shape content into fluent
prose. If Vertex AI is unavailable for any reason (no credentials locally,
model not enabled, network error), `generate_narrative` returns `(None,
False)` and the caller renders the deterministic template instead. The
system's correctness never depends on this module succeeding.
"""
import logging
import os

logger = logging.getLogger(__name__)

_PROJECT_ID = os.environ.get("PROJECT_ID", "hack-team-toruk-makto")
_LOCATION = os.environ.get("VERTEX_LOCATION", "europe-west1")
_MODEL_NAME = os.environ.get("VERTEX_MODEL", "gemini-2.5-flash")

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    from google import genai

    _client = genai.Client(vertexai=True, project=_PROJECT_ID, location=_LOCATION)
    return _client


def generate_narrative(prompt: str) -> tuple[str | None, bool]:
    try:
        client = _get_client()
        response = client.models.generate_content(model=_MODEL_NAME, contents=prompt)
        text = (response.text or "").strip()
        if not text:
            return None, False
        return text, True
    except Exception:
        logger.warning("Vertex AI narrative generation failed; falling back to deterministic template.", exc_info=True)
        return None, False
