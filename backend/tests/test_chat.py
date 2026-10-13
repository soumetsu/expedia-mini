"""Mocked contract tests for the two-stage Gemini hotel assistant."""

import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from unittest import TestCase
from unittest.mock import patch

from app.config import GEMINI_FALLBACK_MODEL, GEMINI_MODEL
from app.controllers.chat import (
    GEMINI_API_ROOT,
    GEMINI_FALLBACK_MAX_ATTEMPTS,
    GEMINI_MAX_ATTEMPTS,
    GEMINI_TIMEOUT_SECONDS,
    ChatConfigurationError,
    ChatProviderError,
    request_support_reply,
)
from app.controllers.database import initialize_database
from app.models import ChatRequest


PROPOSED_SQL = """SELECT
    sh.name,
    sz.searched_postcode,
    dn.stay_date,
    dn.nightly_rate_cents / 100.0 AS nightly_rate_usd,
    dn.rooms_available
FROM saved_hotels AS sh
JOIN saved_hotel_zips AS sz ON sz.hotel_id = sh.hotel_id
JOIN demo_hotel_nights AS dn ON dn.hotel_id = sh.hotel_id
WHERE sz.searched_postcode = '16803'
  AND dn.stay_date = '2026-10-11'
  AND dn.rooms_available > 0
ORDER BY dn.nightly_rate_cents, sh.name
LIMIT 3"""


class MockResponse:
    def __init__(self, payload: object) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "MockResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def provider_response(text: str, prompt_tokens: int, response_tokens: int) -> MockResponse:
    return MockResponse(
        {
            "candidates": [{"content": {"parts": [{"text": text}]}}],
            "usageMetadata": {
                "promptTokenCount": prompt_tokens,
                "candidatesTokenCount": response_tokens,
                "totalTokenCount": prompt_tokens + response_tokens,
            },
        }
    )


class ChatControllerTests(TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        initialize_database(self.database_path)
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute(
                """
                INSERT INTO saved_hotels (
                    hotel_id, name, address, latitude, longitude
                ) VALUES ('hotel-1', 'Campus Hotel', 'State College, PA', 40.8, -77.86)
                """
            )
            connection.execute(
                """
                INSERT INTO saved_hotel_zips (
                    hotel_id, searched_postcode, center_locality, center_state,
                    center_latitude, center_longitude, search_scope,
                    hotel_city, hotel_state, hotel_postcode, distance_meters,
                    distance_miles, inside_searched_postcode
                ) VALUES (
                    'hotel-1', '16803', 'State College', 'Pennsylvania',
                    40.8, -77.86, 'postcode boundary', 'State College',
                    'Pennsylvania', '16803', 123, 0.08, 1
                )
                """
            )
            connection.execute(
                """
                INSERT INTO demo_hotel_nights (
                    hotel_id, stay_date, nightly_rate_cents, rooms_available
                ) VALUES ('hotel-1', '2026-10-11', 12345, 2)
                """
            )
            connection.commit()
        finally:
            connection.close()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_two_stage_reply_uses_prompt_checked_sql_rows_and_backend_key(self) -> None:
        payload = ChatRequest(
            message=(
                "What are the three cheapest available saved hotels near ZIP 16803 "
                "for October 11, 2026?"
            )
        )
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-only-key"},
            clear=True,
        ), patch(
            "app.controllers.chat.urlopen",
            side_effect=[
                provider_response(PROPOSED_SQL, 40, 20),
                provider_response(
                    "Campus Hotel is $123.45 for October 11, with 2 simulated rooms.",
                    80,
                    18,
                ),
            ],
        ) as mocked_urlopen:
            response = request_support_reply(payload, self.database_path)

        self.assertEqual(response.model, GEMINI_MODEL)
        self.assertEqual(response.retrieval_mode, "sql_query")
        self.assertEqual(response.generated_sql, PROPOSED_SQL)
        self.assertEqual(response.retrieved_rows[0]["name"], "Campus Hotel")
        self.assertEqual(response.retrieved_rows[0]["nightly_rate_usd"], 123.45)
        self.assertEqual(response.usage.prompt_tokens, 120)
        self.assertEqual(response.usage.response_tokens, 38)
        self.assertEqual(response.usage.total_tokens, 158)
        self.assertEqual(mocked_urlopen.call_count, 2)

        first_request = mocked_urlopen.call_args_list[0].args[0]
        second_request = mocked_urlopen.call_args_list[1].args[0]
        self.assertEqual(
            first_request.full_url,
            f"{GEMINI_API_ROOT}/{GEMINI_MODEL}:generateContent",
        )
        self.assertNotIn("test-only-key", first_request.full_url)
        self.assertEqual(first_request.get_header("X-goog-api-key"), "test-only-key")
        first_body = json.loads(first_request.data.decode("utf-8"))
        second_body = json.loads(second_request.data.decode("utf-8"))
        self.assertIn("saved_hotel_zips", first_body["systemInstruction"]["parts"][0]["text"])
        self.assertIn("retrieved_rows", second_body["contents"][0]["parts"][0]["text"])
        self.assertIn("Campus Hotel", second_body["contents"][0]["parts"][0]["text"])
        for call in mocked_urlopen.call_args_list:
            self.assertEqual(call.kwargs["timeout"], GEMINI_TIMEOUT_SECONDS)

        connection = sqlite3.connect(self.database_path)
        try:
            messages = connection.execute(
                "SELECT role, content FROM conversation_history ORDER BY message_id"
            ).fetchall()
            traces = connection.execute(
                "SELECT stage, content FROM conversation_traces ORDER BY trace_id"
            ).fetchall()
        finally:
            connection.close()
        self.assertEqual([row[0] for row in messages], ["user", "assistant"])
        self.assertEqual(
            [row[0] for row in traces],
            ["generated_sql", "executed_sql", "result_summary"],
        )

    def test_missing_key_records_an_error(self) -> None:
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(
            ChatConfigurationError
        ):
            request_support_reply(ChatRequest(message="Hello"), self.database_path)

        connection = sqlite3.connect(self.database_path)
        try:
            stages = connection.execute(
                "SELECT stage FROM conversation_traces ORDER BY trace_id"
            ).fetchall()
        finally:
            connection.close()
        self.assertEqual(stages, [("error",)])

    def test_provider_and_invalid_response_errors_are_sanitized(self) -> None:
        payload = ChatRequest(message="Hello")
        for provider_result in (URLError("secret provider detail"), MockResponse({})):
            with self.subTest(provider_result=type(provider_result).__name__), patch.dict(
                os.environ,
                {"GEMINI_API_KEY": "test-only-key"},
                clear=True,
            ), patch(
                "app.controllers.chat.urlopen",
                side_effect=(
                    provider_result if isinstance(provider_result, Exception) else None
                ),
                return_value=(
                    None if isinstance(provider_result, Exception) else provider_result
                ),
            ), patch(
                "app.controllers.chat.time.sleep"
            ), self.assertRaises(ChatProviderError):
                request_support_reply(payload, self.database_path)

    def test_transient_provider_failures_use_retry_after_and_exponential_backoff(
        self,
    ) -> None:
        payload = ChatRequest(message="Hello")
        transient_error = HTTPError(
            url="https://example.test",
            code=503,
            msg="high demand",
            hdrs={"Retry-After": "3"},
            fp=None,
        )
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-only-key"},
            clear=True,
        ), patch(
            "app.controllers.chat.urlopen",
            side_effect=[
                transient_error,
                URLError("temporary connection failure"),
                provider_response("NO_QUERY", 10, 1),
                provider_response("Enter a five-digit U.S. ZIP.", 20, 8),
            ],
        ) as mocked_urlopen, patch("app.controllers.chat.time.sleep") as mocked_sleep:
            with patch("app.controllers.chat.random.uniform", return_value=0.0):
                response = request_support_reply(payload, self.database_path)

        self.assertEqual(response.retrieval_mode, "support_only")
        self.assertEqual(response.reply, "Enter a five-digit U.S. ZIP.")
        self.assertEqual(mocked_urlopen.call_count, 4)
        self.assertEqual(
            [call.args[0] for call in mocked_sleep.call_args_list],
            [3.0, 2.0],
        )

    def test_transient_provider_failure_stops_after_primary_and_fallback(self) -> None:
        payload = ChatRequest(message="Hello")
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-only-key"},
            clear=True,
        ), patch(
            "app.controllers.chat.urlopen",
            side_effect=HTTPError(
                url="https://example.test",
                code=503,
                msg="high demand",
                hdrs=None,
                fp=None,
            ),
        ) as mocked_urlopen, patch(
            "app.controllers.chat.time.sleep"
        ) as mocked_sleep, patch(
            "app.controllers.chat.random.uniform", return_value=0.0
        ), self.assertRaises(ChatProviderError):
            request_support_reply(payload, self.database_path)

        self.assertEqual(
            mocked_urlopen.call_count,
            GEMINI_MAX_ATTEMPTS + GEMINI_FALLBACK_MAX_ATTEMPTS,
        )
        self.assertEqual(
            [call.args[0] for call in mocked_sleep.call_args_list],
            [1.0, 2.0, 1.0],
        )
        request_urls = [call.args[0].full_url for call in mocked_urlopen.call_args_list]
        self.assertTrue(
            all(GEMINI_MODEL in url for url in request_urls[:GEMINI_MAX_ATTEMPTS])
        )
        self.assertTrue(
            all(
                GEMINI_FALLBACK_MODEL in url
                for url in request_urls[GEMINI_MAX_ATTEMPTS:]
            )
        )

    def test_fallback_model_recovers_after_primary_503_exhaustion(self) -> None:
        payload = ChatRequest(message="Hello")
        transient_errors = [
            HTTPError(
                url="https://example.test",
                code=503,
                msg="high demand",
                hdrs=None,
                fp=None,
            )
            for _ in range(GEMINI_MAX_ATTEMPTS)
        ]
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-only-key"},
            clear=True,
        ), patch(
            "app.controllers.chat.urlopen",
            side_effect=[
                *transient_errors,
                provider_response("NO_QUERY", 10, 1),
                provider_response("Enter a five-digit U.S. ZIP.", 20, 8),
            ],
        ) as mocked_urlopen, patch(
            "app.controllers.chat.time.sleep"
        ) as mocked_sleep, patch(
            "app.controllers.chat.random.uniform", return_value=0.0
        ):
            response = request_support_reply(payload, self.database_path)

        self.assertEqual(response.retrieval_mode, "support_only")
        self.assertEqual(
            response.model,
            f"{GEMINI_MODEL} + {GEMINI_FALLBACK_MODEL}",
        )
        self.assertEqual(mocked_urlopen.call_count, GEMINI_MAX_ATTEMPTS + 2)
        self.assertEqual(
            [call.args[0] for call in mocked_sleep.call_args_list],
            [1.0, 2.0],
        )
        fallback_request = mocked_urlopen.call_args_list[GEMINI_MAX_ATTEMPTS].args[0]
        self.assertIn(GEMINI_FALLBACK_MODEL, fallback_request.full_url)
