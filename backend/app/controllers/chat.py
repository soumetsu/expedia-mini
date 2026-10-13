"""Backend-only two-stage Gemini and local SQLite hotel assistant."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import random
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

from ..config import GEMINI_FALLBACK_MODEL, GEMINI_MODEL, get_gemini_api_key
from ..models import ChatRequest, ChatResponse, ChatUsageMetrics
from .database import (
    DATABASE_PATH,
    DataAccessError,
    HotelQueryExecutionError,
    HotelQueryValidationError,
    execute_read_only_hotel_query,
    record_conversation_message,
    record_conversation_trace,
)


GEMINI_API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_TIMEOUT_SECONDS = 30.0
GEMINI_MAX_ATTEMPTS = 3
GEMINI_FALLBACK_MAX_ATTEMPTS = 2
GEMINI_BACKOFF_BASE_SECONDS = 1.0
GEMINI_BACKOFF_CAP_SECONDS = 8.0
GEMINI_RETRY_AFTER_CAP_SECONDS = 30.0
GEMINI_JITTER_RATIO = 0.25
TRANSIENT_PROVIDER_STATUSES = {429, 500, 502, 503, 504}
FALLBACK_PROVIDER_STATUSES = {500, 502, 503, 504}
HOTEL_ASSISTANT_PROMPT_PATH = (
    Path(__file__).resolve().parents[3] / "prompts" / "hotel-assistant.md"
)
_hotel_assistant_prompt: str | None = None


class ChatConfigurationError(RuntimeError):
    """Raised when the Gemini credential or assistant prompt is unavailable."""


class ChatProviderError(RuntimeError):
    """Raised when Gemini cannot return a usable workflow response."""


class ChatProviderUnavailableError(ChatProviderError):
    """Raised when transient provider availability retries are exhausted."""


def load_hotel_assistant_prompt(
    prompt_path: Path = HOTEL_ASSISTANT_PROMPT_PATH,
) -> str:
    """Load the durable assistant instructions during application startup."""

    global _hotel_assistant_prompt
    try:
        prompt = prompt_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ChatConfigurationError("The hotel assistant prompt is unavailable.") from exc
    if not prompt:
        raise ChatConfigurationError("The hotel assistant prompt is empty.")
    _hotel_assistant_prompt = prompt
    return prompt


def _prompt() -> str:
    return _hotel_assistant_prompt or load_hotel_assistant_prompt()


def _api_key() -> str:
    key = get_gemini_api_key()
    if key is None:
        raise ChatConfigurationError("Gemini is not configured.")
    return key


def _reply_text(payload: Any) -> str:
    if not isinstance(payload, dict):
        raise ChatProviderError("Gemini returned an invalid response.")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ChatProviderError("Gemini did not return a reply.")
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
        raise ChatProviderError("Gemini did not return a reply.")
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
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in values
    ):
        return None
    return ChatUsageMetrics(
        prompt_tokens=values[0],
        response_tokens=values[1],
        total_tokens=values[2],
    )


def _combined_usage(*metrics: ChatUsageMetrics | None) -> ChatUsageMetrics | None:
    available = [metric for metric in metrics if metric is not None]
    if not available:
        return None
    return ChatUsageMetrics(
        prompt_tokens=sum(metric.prompt_tokens for metric in available),
        response_tokens=sum(metric.response_tokens for metric in available),
        total_tokens=sum(metric.total_tokens for metric in available),
    )


def _retry_after_seconds(headers: Any) -> float | None:
    """Return a bounded Retry-After delay from seconds or an HTTP date."""

    if headers is None:
        return None
    retry_after = headers.get("Retry-After")
    if not isinstance(retry_after, str) or not retry_after.strip():
        return None
    value = retry_after.strip()
    try:
        seconds = float(value)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()
    return min(max(seconds, 0.0), GEMINI_RETRY_AFTER_CAP_SECONDS)


def _retry_delay_seconds(attempt: int, headers: Any = None) -> float:
    """Calculate capped exponential backoff with positive random jitter."""

    exponential_delay = min(
        GEMINI_BACKOFF_BASE_SECONDS * (2**attempt),
        GEMINI_BACKOFF_CAP_SECONDS,
    )
    retry_after = _retry_after_seconds(headers)
    base_delay = max(exponential_delay, retry_after or 0.0)
    jitter = random.uniform(0.0, base_delay * GEMINI_JITTER_RATIO)
    return min(base_delay + jitter, GEMINI_RETRY_AFTER_CAP_SECONDS)


def _request_gemini(
    system_instruction: str,
    contents: list[dict[str, Any]],
    max_output_tokens: int,
    model: str = GEMINI_MODEL,
    max_attempts: int = GEMINI_MAX_ATTEMPTS,
) -> tuple[str, ChatUsageMetrics | None]:
    request_body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": max_output_tokens,
        },
    }
    request = Request(
        f"{GEMINI_API_ROOT}/{quote(model, safe='')}:generateContent",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": _api_key(),
        },
        method="POST",
    )
    provider_payload: Any = None
    for attempt in range(max_attempts):
        try:
            with urlopen(request, timeout=GEMINI_TIMEOUT_SECONDS) as response:
                provider_payload = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as exc:
            if (
                exc.code in TRANSIENT_PROVIDER_STATUSES
                and attempt + 1 < max_attempts
            ):
                time.sleep(_retry_delay_seconds(attempt, exc.headers))
                continue
            error_type = (
                ChatProviderUnavailableError
                if exc.code in FALLBACK_PROVIDER_STATUSES
                else ChatProviderError
            )
            raise error_type("Gemini could not provide a reply.") from exc
        except (URLError, TimeoutError) as exc:
            if attempt + 1 < max_attempts:
                time.sleep(_retry_delay_seconds(attempt))
                continue
            raise ChatProviderUnavailableError(
                "Gemini could not provide a reply."
            ) from exc
        except json.JSONDecodeError as exc:
            raise ChatProviderError("Gemini could not provide a reply.") from exc
    return _reply_text(provider_payload), _usage_metrics(provider_payload)


def _request_gemini_with_fallback(
    system_instruction: str,
    contents: list[dict[str, Any]],
    max_output_tokens: int,
) -> tuple[str, ChatUsageMetrics | None, str]:
    """Use the primary model, then one lighter fallback availability pool."""

    try:
        reply, usage = _request_gemini(
            system_instruction,
            contents,
            max_output_tokens,
            model=GEMINI_MODEL,
            max_attempts=GEMINI_MAX_ATTEMPTS,
        )
        return reply, usage, GEMINI_MODEL
    except ChatProviderUnavailableError as primary_error:
        try:
            reply, usage = _request_gemini(
                system_instruction,
                contents,
                max_output_tokens,
                model=GEMINI_FALLBACK_MODEL,
                max_attempts=GEMINI_FALLBACK_MAX_ATTEMPTS,
            )
            return reply, usage, GEMINI_FALLBACK_MODEL
        except ChatProviderUnavailableError as fallback_error:
            raise ChatProviderError(
                "Gemini primary and fallback models were unavailable."
            ) from fallback_error


def _model_label(*models: str) -> str:
    """Return a stable visible label for every model used in the workflow."""

    used = set(models)
    ordered = [
        model
        for model in (GEMINI_MODEL, GEMINI_FALLBACK_MODEL)
        if model in used
    ]
    ordered.extend(model for model in models if model not in ordered)
    return " + ".join(ordered)


def _sql_from_reply(reply: str) -> str:
    normalized = reply.strip()
    if normalized == "NO_QUERY":
        return normalized
    if normalized.startswith("```") and normalized.endswith("```"):
        lines = normalized.splitlines()
        if lines and lines[0].strip().lower() in {"```", "```sql", "```sqlite"}:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        normalized = "\n".join(lines).strip()
    return normalized


def _result_summary(rows: list[dict[str, object]]) -> str:
    columns = list(rows[0]) if rows else []
    return json.dumps(
        {
            "row_count": len(rows),
            "columns": columns,
            "status": "matches retrieved" if rows else "no matching saved records",
            "rows": rows,
        },
        separators=(",", ":"),
    )


def _record_error(
    conversation_id: str,
    error: Exception,
    database_path: Path,
) -> None:
    try:
        record_conversation_trace(
            conversation_id,
            "error",
            f"{type(error).__name__}: {error}",
            database_path,
        )
    except DataAccessError:
        pass


def request_support_reply(
    payload: ChatRequest,
    database_path: Path = DATABASE_PATH,
) -> ChatResponse:
    """Run proposed SQL, checked retrieval, and a grounded second model call."""

    conversation_id = payload.conversation_id or str(uuid4())
    record_conversation_message(
        conversation_id,
        "user",
        payload.message,
        database_path,
    )
    try:
        instructions = _prompt()
        proposal_contents = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Propose the one allowed SQL query for this question. "
                            "Follow the SQL proposal rules exactly.\n\n"
                            f"Question: {payload.message}"
                        )
                    }
                ],
            }
        ]
        proposal_reply, proposal_usage, proposal_model = _request_gemini_with_fallback(
            instructions,
            proposal_contents,
            768,
        )
        generated_sql = _sql_from_reply(proposal_reply)
        record_conversation_trace(
            conversation_id,
            "generated_sql",
            generated_sql,
            database_path,
        )

        if generated_sql == "NO_QUERY":
            retrieval_mode = "support_only"
            executed_sql = None
            rows: list[dict[str, object]] = []
            record_conversation_trace(
                conversation_id,
                "executed_sql",
                "NOT_EXECUTED: the question did not require saved-hotel retrieval",
                database_path,
            )
        else:
            retrieval_mode = "sql_query"
            try:
                executed_sql, rows = execute_read_only_hotel_query(
                    generated_sql,
                    database_path,
                )
            except (HotelQueryValidationError, HotelQueryExecutionError) as exc:
                raise ChatProviderError(
                    "Gemini proposed a query that the backend could not safely execute."
                ) from exc
            record_conversation_trace(
                conversation_id,
                "executed_sql",
                executed_sql,
                database_path,
            )

        summary = _result_summary(rows)
        record_conversation_trace(
            conversation_id,
            "result_summary",
            summary,
            database_path,
        )
        grounding_payload = {
            "original_question": payload.message,
            "retrieval_mode": retrieval_mode,
            "generated_sql": generated_sql,
            "executed_sql": executed_sql,
            "result_summary": json.loads(summary),
            "retrieved_rows": rows,
        }
        answer_contents = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Answer the original question using the grounded-answer rules. "
                            "The JSON below is supplied by the checked backend workflow.\n\n"
                            f"{json.dumps(grounding_payload, default=str)}"
                        )
                    }
                ],
            }
        ]
        answer, answer_usage, answer_model = _request_gemini_with_fallback(
            instructions,
            answer_contents,
            768,
        )
        record_conversation_message(
            conversation_id,
            "assistant",
            answer,
            database_path,
        )
        return ChatResponse(
            reply=answer,
            model=_model_label(proposal_model, answer_model),
            usage=_combined_usage(proposal_usage, answer_usage),
            conversation_id=conversation_id,
            retrieval_mode=retrieval_mode,
            generated_sql=generated_sql,
            executed_sql=executed_sql,
            result_summary=summary,
            retrieved_rows=rows,
        )
    except (ChatConfigurationError, ChatProviderError, DataAccessError) as exc:
        _record_error(conversation_id, exc, database_path)
        raise
