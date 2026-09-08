import sys
from pathlib import Path

from pywinauto import Desktop

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from library.studio.app_keywords import StudioAppKeywords
from library.studio.device_keywords import DeviceKeywords
from library.studio.example_keywords import ExampleKeywords
from library.studio.navigation_helpers import NavigationHelpersMixin
from library.studio.project_creation_keywords import ProjectCreationKeywords
from library.studio.terminal_keywords import TerminalKeywords
from library.studio.wait_helpers import WaitHelpersMixin


class StudioLibrary(
    StudioAppKeywords,
    DeviceKeywords,
    ExampleKeywords,
    ProjectCreationKeywords,
    TerminalKeywords,
    NavigationHelpersMixin,
    WaitHelpersMixin,
):

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self.desktop = Desktop(backend="uia")
        self.studio = None
        self.search_box = None
        self.cli_window_handle = None
