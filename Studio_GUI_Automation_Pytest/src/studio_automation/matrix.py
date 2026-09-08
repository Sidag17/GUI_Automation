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


def load_test_cases(matrix_file=None):
    path = Path(matrix_file) if matrix_file else DEFAULT_MATRIX_FILE

    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    cases = config.get("test_cases", [])
    enabled_cases = []

    for index, case in enumerate(cases, start=1):
        if not case.get("enabled", True):
            continue

        missing = [field for field in REQUIRED_FIELDS if not case.get(field)]
        if missing:
            raise ValueError(
                f"Test case #{index} is missing required field(s): "
                + ", ".join(missing)
            )

        enabled_cases.append(case)

    if not enabled_cases:
        raise ValueError(
            f"No enabled test cases were found in: {path}"
        )

    return enabled_cases
