"""Mocked contract tests for the Gemini support-chat controller."""

import json
import os
from urllib.error import HTTPError, URLError
from unittest import TestCase
from unittest.mock import patch

from app.config import GEMINI_MODEL
from app.controllers.chat import (
    GEMINI_API_ROOT,
    GEMINI_TIMEOUT_SECONDS,
    ChatConfigurationError,
    ChatProviderError,
    request_support_reply,
)
from app.models import ChatHistoryMessage, ChatRequest


class MockResponse:
    def __init__(self, payload: object) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "MockResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class ChatControllerTests(TestCase):
    def test_support_reply_uses_backend_key_model_and_bounded_history(self) -> None:
        payload = ChatRequest(
            message="How do I search by ZIP?",
            history=[
                ChatHistoryMessage(role="user", content="Can you help?"),
                ChatHistoryMessage(role="assistant", content="Yes."),
            ],
        )
        provider_response = {
            "candidates": [
                {"content": {"parts": [{"text": "Enter a five-digit U.S. ZIP."}]}}
            ],
            "usageMetadata": {
                "promptTokenCount": 42,
                "candidatesTokenCount": 9,
                "totalTokenCount": 51,
            },
        }
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-only-key"},
            clear=True,
        ), patch(
            "app.controllers.chat.urlopen",
            return_value=MockResponse(provider_response),
        ) as mocked_urlopen:
            response = request_support_reply(payload)

        self.assertEqual(response.reply, "Enter a five-digit U.S. ZIP.")
        self.assertEqual(response.model, GEMINI_MODEL)
        self.assertEqual(response.usage.prompt_tokens, 42)
        self.assertEqual(response.usage.response_tokens, 9)
        self.assertEqual(response.usage.total_tokens, 51)
        request, = mocked_urlopen.call_args.args
        self.assertEqual(
            request.full_url,
            f"{GEMINI_API_ROOT}/{GEMINI_MODEL}:generateContent",
        )
        self.assertNotIn("test-only-key", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "test-only-key")
        sent = json.loads(request.data.decode("utf-8"))
        self.assertEqual(
            [item["role"] for item in sent["contents"]],
            ["user", "model", "user"],
        )
        self.assertEqual(
            sent["contents"][-1]["parts"][0]["text"],
            "How do I search by ZIP?",
        )
        mocked_urlopen.assert_called_once_with(
            request,
            timeout=GEMINI_TIMEOUT_SECONDS,
        )

    def test_missing_key_is_a_configuration_error(self) -> None:
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(
            ChatConfigurationError
        ):
            request_support_reply(ChatRequest(message="Hello"))

    def test_provider_and_invalid_response_errors_are_sanitized(self) -> None:
        payload = ChatRequest(message="Hello")
        for provider_result in (URLError("secret provider detail"), MockResponse({})):
            with self.subTest(provider_result=type(provider_result).__name__), patch.dict(
                os.environ,
                {"GEMINI_API_KEY": "test-only-key"},
                clear=True,
            ), patch(
                "app.controllers.chat.urlopen",
                side_effect=provider_result if isinstance(provider_result, Exception) else None,
                return_value=None if isinstance(provider_result, Exception) else provider_result,
            ), self.assertRaises(ChatProviderError):
                request_support_reply(payload)

    def test_transient_provider_failure_is_retried_once(self) -> None:
        payload = ChatRequest(message="Hello")
        provider_response = {
            "candidates": [{"content": {"parts": [{"text": "Hello!"}]}}]
        }
        transient_error = HTTPError(
            url="https://example.test",
            code=503,
            msg="high demand",
            hdrs=None,
            fp=None,
        )
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-only-key"},
            clear=True,
        ), patch(
            "app.controllers.chat.urlopen",
            side_effect=[transient_error, MockResponse(provider_response)],
        ) as mocked_urlopen, patch("app.controllers.chat.time.sleep") as mocked_sleep:
            response = request_support_reply(payload)

        self.assertEqual(response.reply, "Hello!")
        self.assertIsNone(response.usage)
        self.assertEqual(mocked_urlopen.call_count, 2)
        mocked_sleep.assert_called_once_with(0.5)
