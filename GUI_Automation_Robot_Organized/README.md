# Simplicity Studio GUI Automation

A modular Robot Framework + pywinauto automation project for creating and building
Simplicity Studio applications through the GUI.

## What the current workflow does

1. Opens Simplicity Studio.
2. Waits for the main screen and closes old tabs.
3. Opens **Devices**, searches for the requested board, and selects it.
4. Opens **Example Projects & Demos**.
5. Searches for the exact application and verifies it is **Production** quality.
6. Creates the project.
7. Selects the requested Target IDE.
8. Finishes project creation.
9. Opens the project in the selected IDE/CLI target.
10. For CMake, runs the workflow and verifies that an `.s37` binary exists.

## Project structure

```text
GUI_Automation_Robot_Organized/
├── config/
│   └── config.py
├── docs/
│   └── ARCHITECTURE.md
├── library/
│   ├── StudioLibrary.py
│   └── studio/
│       ├── app_keywords.py
│       ├── device_keywords.py
│       ├── example_keywords.py
│       ├── project_creation_keywords.py
│       ├── terminal_keywords.py
│       ├── navigation_helpers.py
│       └── wait_helpers.py
├── resources/
│   └── studio_workflows.resource
├── results/
├── tests/
│   └── select_board.robot
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── run.ps1
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell shows the downloaded-script warning for `run.ps1`, unblock it once:

```powershell
Unblock-File .\run.ps1
```

## Run

```powershell
.\run.ps1
```

Or directly:

```powershell
python -m robot -d results tests\select_board.robot
```

## Change board/application/IDE

Edit only the Robot variables in `tests/select_board.robot`:

```robot
${BOARD}          2601B
${APPLICATION}    AI/ML - SoC Blink EFR32
${TARGET_IDE}     CMake (GCC/IAR/LLVM)
${BUILD_FOLDER}   cmake_gcc
```

Machine-specific Simplicity Studio paths and timeouts belong in `config/config.py`.
You can also override the Studio executable without modifying source code:

```powershell
$env:SIMPLICITY_STUDIO_EXE = "C:\path\to\studio.exe"
```

## Maintenance rule

Keep Robot tests readable and business-level. Put UI implementation details in
`library/studio/`. Do not add new 200-line methods to `StudioLibrary.py`; it is only
the public facade that composes the keyword modules.
