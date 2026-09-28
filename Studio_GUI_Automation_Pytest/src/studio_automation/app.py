import subprocess
import time

from pywinauto.keyboard import send_keys

from .configuration import (
    STUDIO_START_TIMEOUT,
    STUDIO_TITLE_REGEX,
    require_studio_exe,
)
from .uia_helpers import UIA_TRANSIENT_ERRORS, is_usable


class StudioAppActions:
    
    def open_studio(self):
        """
        Reuse an existing Simplicity Studio window if one
        is already open.

        Only launch Studio when no usable Studio window exists.

        Returns:
            True  -> Studio was launched now.
            False -> Existing Studio was reused.
        """

        print("Checking for existing Simplicity Studio...")

        windows = self.desktop.windows(
            title_re=STUDIO_TITLE_REGEX
        )

        # ========================================================
        # CASE 1:
        # Studio is already running
        # ========================================================

        usable_windows = []

        for wrapper in windows:

            try:

                if not is_usable(wrapper):
                    continue

                usable_windows.append(wrapper)

            except UIA_TRANSIENT_ERRORS:
                continue

        if usable_windows:

            # Prefer the largest Studio window.
            # This avoids accidentally attaching to a splash/dialog.
            usable_windows.sort(
                key=lambda window: (
                    window.rectangle().width()
                    * window.rectangle().height()
                ),
                reverse=True
            )

            existing = usable_windows[0]

            self.studio = self.desktop.window(
                handle=existing.handle
            )

            print(
                "Using already-open Simplicity Studio:",
                repr(existing.window_text()),
                "| Handle:",
                existing.handle
            )

            try:
                self.studio.wrapper_object().set_focus()
            except UIA_TRANSIENT_ERRORS:
                pass

            return False

        # ========================================================
        # CASE 2:
        # Studio is NOT running
        # ========================================================

        studio_exe = require_studio_exe()

        print(
            "Simplicity Studio is not open. "
            "Launching Studio..."
        )
        print("Executable:", studio_exe)

        subprocess.Popen(studio_exe)

        return True

    def ensure_studio_session(self):
        """
        Make sure this automation object is connected to
        Simplicity Studio.

        Existing Studio:
            attach to it and continue.

        Studio not running:
            launch it and wait for initial Home screen.
        """

        # ========================================================
        # First check whether we already have a valid Studio
        # connection from this pytest session.
        # ========================================================

        if self.studio is not None:

            try:

                studio_window = (
                    self.studio.wrapper_object()
                )

                if (
                    studio_window.exists()
                    and studio_window.is_visible()
                ):

                    print(
                        "Reusing current Simplicity Studio session."
                    )

                    return

            except Exception:

                print(
                    "Stored Studio connection is no longer valid. "
                    "Searching again..."
                )

                self.studio = None

        # ========================================================
        # Find existing Studio or launch a new one.
        # ========================================================

        launched_now = self.open_studio()

        # Always normalize to a usable main screen, whether Studio
        # was just launched or attached mid-session / mid-dialog.
        if launched_now:
            print(
                "Studio was launched by automation. "
                "Waiting for initial main screen..."
            )
        else:
            print(
                "Existing Studio session attached. "
                "Normalizing to main screen..."
            )

        self.wait_for_main_screen()

        # ========================================================
        # Keep Studio maximized
        # ========================================================

        try:

            window = self.studio.wrapper_object()

            window.set_focus()

            window.maximize()

        except UIA_TRANSIENT_ERRORS as error:

            print(
                "Could not maximize Studio:",
                error
            )

    

    def wait_for_main_screen(self):
        print("Waiting for Simplicity Studio main screen...")

        start_time = time.time()

        while time.time() - start_time < STUDIO_START_TIMEOUT:
            windows = self.desktop.windows(title_re=STUDIO_TITLE_REGEX)

            for wrapper in windows:
                try:
                    studio = self.desktop.window(handle=wrapper.handle)

                    devices = studio.child_window(
                        title="DEVICES",
                        control_type="Hyperlink",
                    )

                    # Splash/loading screen does not contain DEVICES.
                    if devices.exists(timeout=1):
                        self.studio = studio
                        print(
                            "Main Studio screen ready:",
                            repr(wrapper.window_text()),
                        )
                        return
                except UIA_TRANSIENT_ERRORS:
                    continue

            print("Studio is still loading...")
            time.sleep(2)

        raise RuntimeError(
            "Simplicity Studio main screen did not load."
        )

    def maximize_studio(self):
        self._require_studio()

        window = self.studio.wrapper_object()
        window.set_focus()

        try:
            window.maximize()
        except UIA_TRANSIENT_ERRORS:
            pass

        print("Main Studio window maximized.")

    def close_previous_tabs(self):
        """
        Close only actual board/project tabs.

        Never close permanent Studio navigation items such as:
        HOME, PROJECTS, DEVICES, TOOLS, PACKAGES, SETTINGS.
        """

        self._require_studio()

        print(
            "Checking previous Studio tabs..."
        )

        # Permanent Studio navigation controls.
        # These must NEVER be closed using Ctrl+W.
        protected_names = {
            "home",
            "projects",
            "devices",
            "tools",
            "packages",
            "settings",
            "ask ai",
        }

        # Re-scan after every close because Chromium/UI tree changes.
        for _ in range(20):

            tabs = self._get_top_tabs()

            names = [
                (
                    tab.element_info.name
                    or ""
                ).strip()
                for tab in tabs
            ]

            print(
                "Open top tabs:",
                names
            )

            # --------------------------------------------------------
            # Only board/project/application tabs are candidates.
            # Permanent navigation items are ignored.
            # --------------------------------------------------------

            closable_tabs = []

            for tab in tabs:

                try:

                    name = (
                        tab.element_info.name
                        or ""
                    ).strip()

                    if not name:
                        continue

                    if name.lower() in protected_names:
                        continue

                    closable_tabs.append(
                        tab
                    )

                except UIA_TRANSIENT_ERRORS:
                    continue

            # --------------------------------------------------------
            # Nothing else to close
            # --------------------------------------------------------

            if not closable_tabs:

                print(
                    "No previous board/project tabs are open."
                )

                self.search_box = None

                return

            # Close last application/project tab first.
            tab = closable_tabs[-1]

            tab_name = (
                tab.element_info.name
                or ""
            ).strip()

            print(
                f"Closing tab: {tab_name}"
            )

            self.studio.wrapper_object().set_focus()

            tab.click_input()

            # Wait until the tab is focused enough that Ctrl+W applies.
            time.sleep(0.2)

            send_keys("^w")

            if not self._wait_for_tab_to_close(
                tab_name,
                timeout=10,
            ):

                raise RuntimeError(
                    f"Tab '{tab_name}' did not close."
                )

            print(
                f"Tab closed successfully: "
                f"{tab_name}"
            )

            self.search_box = None

        raise RuntimeError(
            "Could not clean all previous Studio tabs."
        )
