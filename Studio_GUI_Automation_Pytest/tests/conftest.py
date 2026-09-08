import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from studio_automation import StudioAutomation


@pytest.fixture(scope="session")
def studio():
    """One GUI automation session for the complete pytest run.

    GUI automation is intentionally sequential; multiple tests must not
    control the same Windows desktop in parallel.
    """
    return StudioAutomation()
