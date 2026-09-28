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


def _discover_studio_exe() -> str:
    """Find the newest studio.exe under the local SLT installs tree."""
    roots = [
        Path.home() / ".silabs" / "slt" / "installs",
        Path(r"C:\SiliconLabs"),
        Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        / "SiliconLabs",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "SiliconLabs",
    ]

    matches = []
    for root in roots:
        if not root.exists():
            continue
        try:
            matches.extend(root.rglob("studio.exe"))
        except OSError:
            continue

    existing = [path for path in matches if path.is_file()]
    if not existing:
        return ""

    # Prefer the most recently modified install (handles SLT version bumps).
    existing.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return str(existing[0])


def _resolve_studio_exe() -> str:
    env_value = os.getenv("SIMPLICITY_STUDIO_EXE", "").strip()
    if env_value and Path(env_value).is_file():
        return env_value

    yaml_value = str(_SETTINGS.get("executable") or "").strip()
    if yaml_value and Path(yaml_value).is_file():
        return yaml_value

    discovered = _discover_studio_exe()
    if discovered:
        return discovered

    # Keep an explicit configured path for clearer error messages even when
    # the file is missing (stale YAML / env after an SLT upgrade).
    return env_value or yaml_value


STUDIO_EXE = _resolve_studio_exe()

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


def require_studio_exe() -> str:
    """Return a valid Studio executable path or raise a clear error."""
    if STUDIO_EXE and Path(STUDIO_EXE).is_file():
        return STUDIO_EXE

    configured = STUDIO_EXE or "(not set)"
    raise RuntimeError(
        "Simplicity Studio executable was not found.\n"
        f"  Configured path: {configured}\n"
        "Set SIMPLICITY_STUDIO_EXE to a valid studio.exe, update "
        "studio.executable in config/settings.yaml, or install Studio "
        "under %USERPROFILE%\\.silabs\\slt\\installs."
    )
