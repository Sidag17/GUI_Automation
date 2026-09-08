"""Load machine/runtime settings from config/settings.yaml.

Environment variables override YAML values for CI or developer-specific
installations without requiring repository changes.
"""

import os
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILE = PROJECT_ROOT / "config" / "settings.yaml"


def _load_settings():
    with SETTINGS_FILE.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data.get("studio", {})


_SETTINGS = _load_settings()

STUDIO_EXE = os.getenv(
    "SIMPLICITY_STUDIO_EXE",
    _SETTINGS.get(
        "executable",
        r"C:\Users\siagrawa\.silabs\slt\installs\archive\v6-base-v6.2.1-289\SimplicityStudio-6\studio.exe",
    ),
)

STUDIO_TITLE_REGEX = os.getenv(
    "SIMPLICITY_STUDIO_TITLE_REGEX",
    _SETTINGS.get("title_regex", r"^Simplicity Studio.*"),
)

STUDIO_START_TIMEOUT = int(
    os.getenv(
        "STUDIO_START_TIMEOUT",
        str(_SETTINGS.get("start_timeout_seconds", 120)),
    )
)

PAGE_LOAD_TIMEOUT = int(
    os.getenv(
        "PAGE_LOAD_TIMEOUT",
        str(_SETTINGS.get("page_load_timeout_seconds", 60)),
    )
)

BOARD_SEARCH_TIMEOUT = int(
    os.getenv(
        "BOARD_SEARCH_TIMEOUT",
        str(_SETTINGS.get("board_search_timeout_seconds", 60)),
    )
)
