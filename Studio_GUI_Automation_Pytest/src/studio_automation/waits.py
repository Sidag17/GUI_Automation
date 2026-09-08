import time

from .configuration import PAGE_LOAD_TIMEOUT


class WaitMixin:
    def _wait_for_example_filter_page(self):
        
        print("Waiting for Example Projects & Demos page...")
        self._wait_for_example_page_ready(
            timeout=PAGE_LOAD_TIMEOUT
        )

        filter_box = self.studio.child_window(
            title="Filter on keywords",
            control_type="ComboBox"
        )

        filter_box.wait(
            "exists visible enabled",
            timeout=PAGE_LOAD_TIMEOUT,
            retry_interval=1
        )

        print("Example Projects & Demos page loaded.")

    def _wait_for_example_page_ready(self, timeout=60):

        print("Waiting for Example Projects page to become ready...")

        start_time = time.time()

        while time.time() - start_time < timeout:

            window = self.studio.wrapper_object()

            # --------------------------------------------------
            # 1. Filter must exist and be usable
            # --------------------------------------------------
            try:
                filter_box = self.studio.child_window(
                    title="Filter on keywords",
                    control_type="ComboBox"
                )

                if not filter_box.exists(timeout=1):
                    time.sleep(0.5)
                    continue

                wrapper = filter_box.wrapper_object()

                if not (
                    wrapper.is_visible()
                    and wrapper.is_enabled()
                ):
                    time.sleep(0.5)
                    continue

            except Exception:
                time.sleep(0.5)
                continue

            # --------------------------------------------------
            # 2. Check whether a loader/progress element exists
            # --------------------------------------------------
            loading = False

            for element in window.descendants():

                try:
                    name = (
                        element.element_info.name or ""
                    ).lower()

                    control_type = (
                        element.element_info.control_type
                    )

                    if not element.is_visible():
                        continue

                    if control_type == "ProgressBar":
                        loading = True
                        break

                    if (
                        "loading" in name
                        or "please wait" in name
                    ):
                        loading = True
                        break

                except Exception:
                    pass

            if loading:

                print("Example page is still loading...")
                time.sleep(0.5)
                continue

            print("Example Projects page is ready.")
            return filter_box

        raise RuntimeError(
            "Example Projects page did not become ready."
        )
    
    def _wait_for_project_configuration(self):
        print("Waiting for Project Configuration...")

        start_time = time.time()

        while time.time() - start_time < PAGE_LOAD_TIMEOUT:

            window = self.studio.wrapper_object()

            for element in window.descendants():

                try:

                    name = (
                        element.element_info.name or ""
                    ).strip()

                    if (
                        name == "Project Configuration"
                        and
                        element.element_info.control_type == "Text"
                        and
                        element.is_visible()
                    ):

                        print(
                            "Project Configuration is ready."
                        )

                        return

                except Exception:
                    pass

            print(
                "Project Configuration still loading..."
            )

            time.sleep(0.5)

        raise RuntimeError(
            "Project Configuration did not load."
        )

    def _wait_for_project_configuration_to_close(
        self,
        timeout=120
    ):
        print(
            "Waiting for Project Configuration to close..."
        )

        start_time = time.time()

        while time.time() - start_time < timeout:

            found = False

            try:

                window = self.studio.wrapper_object()

                for element in window.descendants():

                    try:

                        name = (
                            element.element_info.name or ""
                        ).strip()

                        if (
                            name == "Project Configuration"
                            and
                            element.element_info.control_type == "Text"
                            and
                            element.is_visible()
                        ):

                            found = True
                            break

                    except Exception:
                        pass

            except Exception:
                pass

            if not found:

                print(
                    "Project Configuration closed."
                )

                return

            print(
                "Project creation in progress..."
            )

            time.sleep(1)

        raise RuntimeError(
            "Project Configuration did not close "
            "after clicking FINISH."
        )


    def _wait_for_application_visible(self,
    application_name,
    timeout=60
):
        print(f"Waiting for application result: {application_name}")

        start_time = time.time()

        while time.time() - start_time < timeout:
            window = self.studio.wrapper_object()
            for element in window.descendants():
                try:
                    name = (element.element_info.name or "").strip()

                    control_type = (element.element_info.control_type)

                    if ( name.lower() == application_name.lower() and control_type == "Text" and element.is_visible()):
                        print( f"Application result found: " f"{application_name}")
                        return

                except Exception:
                    pass

            print("Waiting for application result..." )
            time.sleep(0.5)

        raise RuntimeError(f"Application '{application_name}' " f"did not become visible.")