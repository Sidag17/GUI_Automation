"""YAML-driven pytest test-matrix loader."""

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRIX_FILE = PROJECT_ROOT / "config" / "test_matrix.yaml"

REQUIRED_FIELDS = (
    "name",
    "board",
    "application",
    "target_ide",
    "build_folder",
)

# Build verification currently supports CMake workflows only.
SUPPORTED_BUILD_IDE_PREFIXES = ("cmake",)


def _normalize_ide(value: str) -> str:
    return str(value or "").strip().lower()


def validate_case(case, index):
    missing = [field for field in REQUIRED_FIELDS if not case.get(field)]
    if missing:
        raise ValueError(
            f"Test case #{index} ({case.get('name', '<unnamed>')}) "
            f"is missing required field(s): {', '.join(missing)}"
        )

    ide = _normalize_ide(case["target_ide"])
    if not any(ide.startswith(prefix) for prefix in SUPPORTED_BUILD_IDE_PREFIXES):
        raise ValueError(
            f"Test case #{index} ({case['name']}): "
            f"target_ide '{case['target_ide']}' is not supported for "
            f"build verification. Use a CMake target "
            f"(e.g. 'CMake (GCC/IAR/LLVM)')."
        )

    return case


def load_test_cases(matrix_file=None):
    path = Path(matrix_file) if matrix_file else DEFAULT_MATRIX_FILE

    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    cases = config.get("test_cases", [])
    enabled_cases = []

    for index, case in enumerate(cases, start=1):
        if not case.get("enabled", True):
            continue

        enabled_cases.append(validate_case(case, index))

    if not enabled_cases:
        raise ValueError(
            f"No enabled test cases were found in: {path}"
        )

    return enabled_cases
