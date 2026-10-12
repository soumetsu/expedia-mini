"""Backend-only Gemini support-chat integration."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from ..config import GEMINI_MODEL, get_gemini_api_key
from ..models import ChatRequest, ChatResponse, ChatUsageMetrics


GEMINI_API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_TIMEOUT_SECONDS = 20.0
GEMINI_MAX_ATTEMPTS = 2
TRANSIENT_PROVIDER_STATUSES = {429, 500, 502, 503, 504}
SUPPORT_SYSTEM_INSTRUCTION = (
    "You are the Expedia-Mini support assistant. Give concise help about the "
    "application's five-digit U.S. ZIP hotel search, saved local hotel subset, "
    "demo accounts, search history, and fictional booking sandbox. Clearly "
    "distinguish live Geoapify place data from fictional classroom data. Live "
    "results contain provider place details and distance but no price, room, "
    "availability, rating, review, amenity, or booking data. Saved local hotels "
    "may show clearly labeled fictional October 10-14, 2026 demo-night values, "
    "while the separate booking sandbox contains fixed fictional stays. Never "
    "invent unsupported facts or booking confirmation. Reply in plain text "
    "without Markdown. If the application does not support a request, say so "
    "and suggest an available action."
)


class ChatConfigurationError(RuntimeError):
    """Raised when the Gemini backend credential is unavailable."""


class ChatProviderError(RuntimeError):
    """Raised when Gemini cannot return a usable support reply."""


def _api_key() -> str:
    key = get_gemini_api_key()
    if key is None:
        raise ChatConfigurationError("Gemini is not configured.")
    return key


def _contents(payload: ChatRequest) -> list[dict[str, Any]]:
    contents = [
        {
            "role": "model" if item.role == "assistant" else "user",
            "parts": [{"text": item.content}],
        }
        for item in payload.history
    ]
    contents.append({"role": "user", "parts": [{"text": payload.message}]})
    return contents


def _reply_text(payload: Any) -> str:
    if not isinstance(payload, dict):
        raise ChatProviderError("Gemini returned an invalid response.")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ChatProviderError("Gemini did not return a support reply.")
    candidate = candidates[0]
    content = candidate.get("content") if isinstance(candidate, dict) else None
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        raise ChatProviderError("Gemini returned an invalid response.")
    reply = "\n".join(
        part["text"].strip()
        for part in parts
        if isinstance(part, dict)
        and isinstance(part.get("text"), str)
        and part["text"].strip()
    ).strip()
    if not reply:
        raise ChatProviderError("Gemini did not return a support reply.")
    return reply


def _usage_metrics(payload: Any) -> ChatUsageMetrics | None:
    if not isinstance(payload, dict):
        return None
    usage = payload.get("usageMetadata")
    if not isinstance(usage, dict):
        return None
    values = (
        usage.get("promptTokenCount"),
        usage.get("candidatesTokenCount"),
        usage.get("totalTokenCount"),
    )
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
        return None
    return ChatUsageMetrics(
        prompt_tokens=values[0],
        response_tokens=values[1],
        total_tokens=values[2],
    )


def request_support_reply(payload: ChatRequest) -> ChatResponse:
    """Send a bounded support conversation to Gemini and return its text reply."""

    request_body = {
        "systemInstruction": {"parts": [{"text": SUPPORT_SYSTEM_INSTRUCTION}]},
        "contents": _contents(payload),
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 512,
        },
    }
    request = Request(
        f"{GEMINI_API_ROOT}/{quote(GEMINI_MODEL, safe='')}:generateContent",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": _api_key(),
        },
        method="POST",
    )
    provider_payload: Any = None
    for attempt in range(GEMINI_MAX_ATTEMPTS):
        try:
            with urlopen(request, timeout=GEMINI_TIMEOUT_SECONDS) as response:
                provider_payload = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as exc:
            if exc.code in TRANSIENT_PROVIDER_STATUSES and attempt + 1 < GEMINI_MAX_ATTEMPTS:
                time.sleep(0.5)
                continue
            raise ChatProviderError("Gemini could not provide a support reply.") from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ChatProviderError("Gemini could not provide a support reply.") from exc

    return ChatResponse(
        reply=_reply_text(provider_payload),
        model=GEMINI_MODEL,
        usage=_usage_metrics(provider_payload),
    )
