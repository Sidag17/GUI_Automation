import subprocess
import time

from pywinauto.keyboard import send_keys
from robot.api.deco import keyword

from config.config import STUDIO_EXE, STUDIO_START_TIMEOUT, STUDIO_TITLE_REGEX


class StudioAppKeywords:
    @keyword("Open Studio")
    def open_studio(self):
        windows = self.desktop.windows(title_re=STUDIO_TITLE_REGEX)

        if windows:
            print("Simplicity Studio is already open.")
            return

        print("Opening Simplicity Studio...")
        subprocess.Popen(STUDIO_EXE)

    @keyword("Wait For Main Screen")
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
                except Exception:
                    pass

            print("Studio is still loading...")
            time.sleep(2)

        raise RuntimeError(
            "Simplicity Studio main screen did not load."
        )

    @keyword("Maximize Studio")
    def maximize_studio(self):
        self._require_studio()

        window = self.studio.wrapper_object()
        window.set_focus()

        try:
            window.maximize()
        except Exception:
            pass

        print("Main Studio window maximized.")

    @keyword("Close Previous Tabs")
    def close_previous_tabs(self):
        self._require_studio()

        print("Checking previous Studio tabs...")

        # Re-scan after every close because the UI tree changes.
        for _ in range(20):
            tabs = self._get_top_tabs()

            names = [
                (tab.element_info.name or "").strip()
                for tab in tabs
            ]
            print("Open top tabs:", names)

            non_home_tabs = [
                tab
                for tab in tabs
                if (tab.element_info.name or "").strip().lower()
                != "home"
            ]

            if not non_home_tabs:
                print("No previous board/project tabs are open.")
                return

            tab = non_home_tabs[-1]
            tab_name = (tab.element_info.name or "").strip()

            print(f"Closing tab: {tab_name}")

            tab.click_input()
            time.sleep(0.5)
            send_keys("^w")

            if not self._wait_for_tab_to_close(
                tab_name,
                timeout=10,
            ):
                raise RuntimeError(
                    f"Tab '{tab_name}' did not close."
                )

            print(f"Tab closed successfully: {tab_name}")

        raise RuntimeError(
            "Could not clean all previous Studio tabs."
        )

