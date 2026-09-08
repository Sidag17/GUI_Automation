import time


from .configuration import PAGE_LOAD_TIMEOUT


class ExampleActions:
    def open_example_projects_and_demos(self):
        self._require_studio()

        print("Looking for EXAMPLE PROJECTS & DEMOS...")

        start_time = time.time()

        while time.time() - start_time < PAGE_LOAD_TIMEOUT:

            window = self.studio.wrapper_object()

            candidates = []

            for element in window.descendants():
                try:
                    name = (
                        element.element_info.name or ""
                    ).strip()

                    control_type = (
                        element.element_info.control_type
                    )

                    normalized = " ".join(
                        name.upper().split()
                    )

                    if (
                        "EXAMPLE PROJECTS" in normalized
                        and "DEMOS" in normalized
                        and element.is_visible()
                    ):
                        candidates.append(element)

                        print(
                            "FOUND:",
                            repr(name),
                            "| Type:",
                            control_type,
                            "| AutomationID:",
                            repr(
                                element.element_info.automation_id
                            )
                        )

                except Exception:
                    pass

            if candidates:

                # Prefer controls that are normally clickable
                priority = {
                    "Hyperlink": 0,
                    "Button": 1,
                    "TabItem": 2,
                    "Text": 3,
                    "Custom": 4,
                }

                candidates.sort(
                    key=lambda element:
                        priority.get(
                            element.element_info.control_type,
                            100
                        )
                )

                target = candidates[0]

                print(
                    "Using:",
                    repr(target.element_info.name),
                    "| Type:",
                    target.element_info.control_type
                )

                # Bring focus to Studio
                self.studio.wrapper_object().set_focus()

                # Click the actual UI element
                target.click_input()

                print(
                    "EXAMPLE PROJECTS & DEMOS clicked."
                )

                # Wait for next page
                self._wait_for_example_filter_page()

                return

            print(
                "EXAMPLE PROJECTS & DEMOS not ready yet..."
            )

            time.sleep(1)

        raise RuntimeError(
            "EXAMPLE PROJECTS & DEMOS was not found."
        )
    def search_application(self, application_name):
        self._require_studio()

        print(f"Searching for application: {application_name}")

        # Wait until Example Projects page is actually ready.
        self._wait_for_example_filter_page()

        filter_box = self.studio.child_window(
            title="Filter on keywords",
            control_type="ComboBox"
        )

        filter_box.wait(
            "exists visible enabled",
            timeout=PAGE_LOAD_TIMEOUT,
            retry_interval=1
        )

        # Use the actual ComboBox wrapper.
        box = filter_box.wrapper_object()

        # Bring Studio to foreground.
        self.studio.wrapper_object().set_focus()

        # Click search/filter box.
        box.click_input()

        time.sleep(0.3)

        # Clear previous search.
        box.type_keys(
            "^a{BACKSPACE}",
            set_foreground=True
        )

        # Search exact application name.
        box.type_keys(
            str(application_name),
            with_spaces=True,
            set_foreground=True
        )

        print(
            f"Application search entered: {application_name}"
        )

        time.sleep(0.3)

        box.type_keys(
            "{ENTER}",
            set_foreground=True
        )

        # Wait until requested application becomes visible.
        self._wait_for_application_visible(
            application_name
        )
    def create_production_application(self, application_name):
        self._require_studio()

        print(f"Looking for application: {application_name}")

        window = self.studio.wrapper_object()

        # --------------------------------------------------------
        # STEP 1: Get UI elements in accessibility/document order
        # --------------------------------------------------------

        elements = window.descendants()

        application_index = None

        for index, element in enumerate(elements):
            try:
                name = (
                    element.element_info.name or ""
                ).strip()

                control_type = (
                    element.element_info.control_type
                )

                if (
                    name.lower() == application_name.lower()
                    and control_type == "Text"
                ):
                    application_index = index
                    break

            except Exception:
                pass

        if application_index is None:
            raise RuntimeError(
                f"Application not found: {application_name}"
            )

        print(
            f"Application found: {application_name}"
        )

        application_element = elements[
            application_index
        ]


        # --------------------------------------------------------
        # STEP 2: Bring application into view
        # --------------------------------------------------------

        try:
            application_element.scroll_into_view()
            print("Application scrolled into view.")
            time.sleep(0.5)

        except Exception as error:
            print(
                "Application scroll_into_view not available:",
                error
            )


        # --------------------------------------------------------
        # IMPORTANT:
        # Re-read UI tree after scrolling because rectangles/UI
        # state may have changed.
        # --------------------------------------------------------

        window = self.studio.wrapper_object()
        elements = window.descendants()

        application_index = None

        for index, element in enumerate(elements):

            try:
                name = (
                    element.element_info.name or ""
                ).strip()

                if (
                    name.lower()
                    == application_name.lower()
                    and
                    element.element_info.control_type
                    == "Text"
                ):
                    application_index = index
                    break

            except Exception:
                pass

        if application_index is None:
            raise RuntimeError(
                "Application disappeared after scrolling."
            )


        # --------------------------------------------------------
        # STEP 3:
        # Search only forward from THIS application.
        #
        # Stop at "View Project Documentation", which marks the
        # end of this application card.
        # --------------------------------------------------------

        production_found = False
        quality_found = None
        create_button = None

        for element in elements[
            application_index + 1:
        ]:

            try:

                name = (
                    element.element_info.name or ""
                ).strip()

                control_type = (
                    element.element_info.control_type
                )

                if not name:
                    continue


                # -----------------------------------------------
                # End of current application's card
                # -----------------------------------------------

                if (
                    name.lower()
                    == "view project documentation"
                ):
                    break


                # -----------------------------------------------
                # Quality tag
                # -----------------------------------------------

                if (
                    name.lower()
                    in {
                        "production",
                        "experimental",
                        "evaluation",
                    }
                    and control_type == "Text"
                ):
                    quality_found = name

                    if name.lower() == "production":
                        production_found = True

                    print(
                        "Application quality:",
                        quality_found
                    )


                # -----------------------------------------------
                # CREATE button
                # -----------------------------------------------

                if (
                    name.upper() == "CREATE"
                    and control_type == "Button"
                ):

                    automation_id = (
                        element.element_info.automation_id
                        or ""
                    )

                    if (
                        automation_id
                        == "resource_item-btn-create"
                    ):
                        create_button = element

                        print(
                            "CREATE button found."
                        )

            except Exception:
                pass


        # --------------------------------------------------------
        # STEP 4: Verify Production is mandatory
        # --------------------------------------------------------

        if not production_found:

            if quality_found:

                raise RuntimeError(
                    f"Application '{application_name}' "
                    f"is '{quality_found}', not Production."
                )

            raise RuntimeError(
                f"Production tag was not found for "
                f"'{application_name}'."
            )


        # --------------------------------------------------------
        # STEP 5: Verify CREATE exists
        # --------------------------------------------------------

        if create_button is None:
            raise RuntimeError(
                f"CREATE button was not found for "
                f"'{application_name}'."
            )


        # --------------------------------------------------------
        # STEP 6: Scroll CREATE into view if necessary
        # --------------------------------------------------------

        try:

            create_button.scroll_into_view()

            print(
                "CREATE button scrolled into view."
            )

            time.sleep(0.5)

        except Exception as error:

            print(
                "CREATE scroll_into_view not available:",
                error
            )


        # --------------------------------------------------------
        # STEP 7: Click CREATE
        # --------------------------------------------------------

        create_button.click_input()

        print(
            f"CREATE clicked for Production application: "
            f"{application_name}"
        )
    
