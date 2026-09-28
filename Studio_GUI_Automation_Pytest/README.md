# Simplicity Studio GUI Automation - pytest + YAML

Pytest-based Windows GUI automation for creating and building Simplicity
Studio applications with `pywinauto`.

This version replaces the Robot Framework orchestration with pytest while
preserving the working GUI automation flow: board selection, Production
example creation, Target IDE selection, Windows Terminal detection, CMake
workflow execution, and final `.s37` binary verification.

## Project layout

```text
Studio_GUI_Automation_Pytest/
|-- config/
|   |-- settings.yaml
|   `-- test_matrix.yaml
|-- src/studio_automation/
|   |-- automation.py
|   |-- app.py
|   |-- devices.py
|   |-- examples.py
|   |-- projects.py
|   |-- terminal.py
|   |-- navigation.py
|   |-- waits.py
|   |-- uia_helpers.py
|   |-- configuration.py
|   `-- matrix.py
|-- tests/
|   |-- conftest.py
|   `-- test_studio_build.py
|-- docs/ARCHITECTURE.md
|-- reports/
|-- pytest.ini
|-- requirements.txt
|-- pyproject.toml
`-- run_tests.ps1
```

## 1. Create/activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Optional (editable install):
python -m pip install -e ".[test]"
```

## 2. Configure Simplicity Studio

Set the Studio executable (required unless `config/settings.yaml` has a path):

```powershell
$env:SIMPLICITY_STUDIO_EXE = "C:\path\to\studio.exe"
```

Optional timeout overrides:

```powershell
$env:STUDIO_START_TIMEOUT = "120"
$env:PAGE_LOAD_TIMEOUT = "60"
$env:BOARD_SEARCH_TIMEOUT = "60"
```

## 3. Add test cases in YAML

Edit only `config/test_matrix.yaml` for normal board/application changes.

By default only the smoke case (`brd2601b_blink_cmake`) is enabled.
Set `enabled: true` on additional blocks for broader coverage.

```yaml
test_cases:
  - name: brd2601b_blink_cmake
    enabled: true
    board: "2601B"
    application: "AI/ML - SoC Blink EFR32"
    target_ide: "CMake (GCC/IAR/LLVM)"
    build_folder: "cmake_gcc"
    count_ml_apps: false
```

Build verification currently supports **CMake targets only**. Invalid IDE
values fail at matrix load time (before GUI work starts).

## 4. Run

Basic (uses `pythonpath = src` from `pytest.ini`):

```powershell
python -m pytest
```

With generated reports:

```powershell
.\run_tests.ps1
```

Reports are generated in `reports/`:

- `report.html`
- `junit.xml`

## Current pass condition

The CMake test passes when all of the following succeed:

1. Studio starts and the configured board is selected.
2. The configured Production application is created.
3. The configured CMake Target IDE is selected.
4. `cmake --workflow --preset project` completes successfully.
5. `build/base` exists.
6. At least one `*.s37` binary exists in `build/base`.

Any failed step raises an exception and pytest reports the test as FAILED.

## Screen-independence rules

- Locate controls by AutomationId / accessible name / control type.
- Interact with the resolved UIA wrapper (`click_input` / invoke).
- Do **not** use absolute screen coordinates or tools like `pyautogui`.
- Prefer condition waits over fixed `sleep` calls.
- Tab discovery uses the UIA tree (Home tab sibling Groups), not pixel bands.

## Important

These tests control the real Windows desktop. Run them sequentially. Do not
use `pytest-xdist` against the same desktop/Studio session.
