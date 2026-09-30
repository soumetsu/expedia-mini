"""Backend configuration loaded from the project-root environment file."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=False)


def geoapify_api_key_configured() -> bool:
    """Return whether a non-blank Geoapify API key is available."""

    return get_geoapify_api_key() is not None


def get_geoapify_api_key() -> str | None:
    """Return the configured Geoapify key for backend provider requests only."""

    value = (os.getenv("GEOAPIFY_API_KEY") or "").strip()
    return value or None
