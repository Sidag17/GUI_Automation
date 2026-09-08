from pywinauto import Desktop

from .app import StudioAppActions
from .devices import DeviceActions
from .examples import ExampleActions
from .navigation import NavigationMixin
from .projects import ProjectActions
from .terminal import TerminalActions
from .waits import WaitMixin


class StudioAutomation(
    StudioAppActions,
    DeviceActions,
    ExampleActions,
    ProjectActions,
    TerminalActions,
    NavigationMixin,
    WaitMixin,
):
    """Single shared Simplicity Studio UI automation session.

    The class intentionally exposes Python methods rather than Robot
    Framework keywords so it can be used directly by pytest fixtures/tests.
    """

    def __init__(self):
        self.desktop = Desktop(backend="uia")
        self.studio = None
        self.search_box = None
        self.cli_window_handle = None
