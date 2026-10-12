"""Tests for project-root backend configuration loading."""

import os
from pathlib import Path
import unittest
from unittest.mock import patch

from app.config import (
    GEMINI_MODEL,
    PROJECT_ROOT,
    gemini_api_key_configured,
    get_gemini_api_key,
    get_geoapify_api_key,
    geoapify_api_key_configured,
)


class ConfigTests(unittest.TestCase):
    def test_project_root_is_derived_from_helper_location(self) -> None:
        self.assertEqual(PROJECT_ROOT, Path(__file__).resolve().parents[2])

    def test_absent_key_is_not_configured(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(geoapify_api_key_configured())

    def test_empty_and_whitespace_keys_are_not_configured(self) -> None:
        for value in ("", "   ", "\t\n"):
            with self.subTest(value_length=len(value)), patch.dict(
                os.environ,
                {"GEOAPIFY_API_KEY": value},
                clear=True,
            ):
                self.assertFalse(geoapify_api_key_configured())

    def test_non_blank_key_is_configured(self) -> None:
        with patch.dict(
            os.environ,
            {"GEOAPIFY_API_KEY": "test-only-value"},
            clear=True,
        ):
            self.assertTrue(geoapify_api_key_configured())
            self.assertEqual(get_geoapify_api_key(), "test-only-value")

    def test_gemini_uses_the_approved_lightweight_model(self) -> None:
        self.assertEqual(GEMINI_MODEL, "gemini-3.5-flash-lite")

    def test_gemini_key_status_does_not_expose_the_key(self) -> None:
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-only-gemini-value"},
            clear=True,
        ):
            self.assertTrue(gemini_api_key_configured())
            self.assertEqual(get_gemini_api_key(), "test-only-gemini-value")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "  "}, clear=True):
            self.assertFalse(gemini_api_key_configured())
            self.assertIsNone(get_gemini_api_key())


if __name__ == "__main__":
    unittest.main()
