# Simplicity Studio GUI Automation - Robot Framework

## Structure

- `tests/select_board.robot` -> readable task definition
- `library/StudioLibrary.py` -> pywinauto implementation
- `config/config.py` -> Studio path and timeouts
- `results/` -> Robot Framework reports

## Setup

From PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
robot -d results tests/select_board.robot
```

Or:

```powershell
.\run.ps1
```

## Change board

Edit:

```robot
${BOARD}    2601B
```

in `tests/select_board.robot`.

The Robot file describes WHAT to do.
The Python library contains HOW to do it.
