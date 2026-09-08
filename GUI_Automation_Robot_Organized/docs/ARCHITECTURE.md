# Architecture

## Design goals

- Keep Robot tests focused on test data and intent.
- Keep reusable end-to-end flows in Robot resource files.
- Keep pywinauto implementation separated by responsibility.
- Preserve one shared Studio/terminal session across all keywords.
- Isolate fragile UI Automation selectors from test scenarios.
- Make future target IDEs, build flows, and validation steps easy to add.

## Layers

### 1. Test cases

`tests/*.robot` contains scenario-specific variables and invokes reusable workflows.
The current test supplies board, application, Target IDE, and build folder.

### 2. Robot workflow resources

`resources/studio_workflows.resource` contains the readable business-level sequence:
open Studio, select board, create project, select IDE, build, and validate output.

This keeps repeated test sequences out of individual test files.

### 3. Robot library facade

`library/StudioLibrary.py` combines the keyword modules and owns shared runtime state:

- UIA Desktop connection
- Simplicity Studio window
- Devices search control
- CLI terminal handle

Robot imports one public library while implementation stays modular.

### 4. Keyword modules

- `app_keywords.py`: Studio lifecycle and tab handling.
- `device_keywords.py`: Devices page and board selection.
- `example_keywords.py`: examples page, search, Production validation, and CREATE.
- `project_creation_keywords.py`: Target IDE selection, FINISH, and Open-in target.
- `terminal_keywords.py`: Windows Terminal control, CMake build, and `.s37` validation.

### 5. Helper modules

- `navigation_helpers.py`: tab, device-search, and board-result helpers.
- `wait_helpers.py`: page readiness and state waits.

### 6. Configuration

`config/config.py` owns machine/environment settings such as the Studio executable
path and timeouts. The Studio executable can be overridden with the
`SIMPLICITY_STUDIO_EXE` environment variable.

## Why mixins are used

The original working automation stored state directly on one `StudioLibrary` object.
The mixin structure splits the implementation into focused files while preserving the
same `self.studio`, `self.search_box`, and `self.cli_window_handle` state. This makes
refactoring lower risk than creating multiple independent UI sessions.

## Adding a new IDE

1. Add selection/open-button behavior in `project_creation_keywords.py`.
2. If that IDE has a different build mechanism, add a new focused keyword module.
3. Add/reuse a high-level workflow in `resources/`.
4. Keep scenario-specific values in `tests/`.

## Adding a new output validation

Put build-specific validation beside the build implementation. For example, CMake's
`.s37` verification stays in `terminal_keywords.py` rather than in the Robot test.
