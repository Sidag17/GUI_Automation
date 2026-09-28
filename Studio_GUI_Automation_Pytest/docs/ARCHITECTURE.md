# Architecture

## Execution flow

```text
config/test_matrix.yaml
          |
          v
       pytest
          |
          v
tests/test_studio_build.py
          |
          v
   StudioAutomation
          |
   +------+------------------------------+
   |      |        |         |           |
  app   devices  examples  projects   terminal
   |      |        |         |           |
   +------+--------+---------+-----------+
                     |
                     v
                 pywinauto
                     |
                     v
              Simplicity Studio
                     |
                     v
             CLI CMake workflow
                     |
                     v
              build/base/*.s37
```

## Module responsibilities

- `automation.py`: single public automation facade and shared UI state.
- `app.py`: launch Studio, wait for main UI, maximize, close old tabs.
- `devices.py`: open Devices, search/select the requested board.
- `examples.py`: open examples, filter and create a Production application.
- `projects.py`: target IDE selection, Finish, Open in IDE/CLI.
- `terminal.py`: Windows Terminal detection, CMake workflow, `.s37` validation.
- `navigation.py` and `waits.py`: low-level navigation/wait helpers.
- `uia_helpers.py`: shared screen-independent UIA helpers and match scoring.
- `matrix.py`: validates and loads enabled YAML test cases (CMake-only build).
- `configuration.py`: machine/runtime settings with environment overrides.

## Design rules

Keep test data in YAML, orchestration in pytest, and UI implementation in
`src/studio_automation`. New test cases should normally not require Python
code changes.

### Screen independence (mandatory)

1. Locate controls by AutomationId, accessible name, and/or control type.
2. Interact only through the resolved UIA wrapper (`click_input` / invoke).
3. Never click absolute screen coordinates; never use `pyautogui`.
4. Prefer condition waits (`exists` / visible / enabled / title markers)
   over fixed sleeps.
5. Tab discovery must use the UIA tree (sibling Groups of the Home tab),
   not pixel Y banding or DPI-dependent geometry for targeting.
6. Bounding rectangles may be used only for visibility checks or relative
   ordering among already-identified siblings — never as click targets.

### Session recovery

The Studio process is session-scoped for speed. Before each test case,
`prepare_for_test_case()` activates Home and closes leftover project tabs
so a failed case cannot poison the next one.

## Parallel execution

Do not use pytest-xdist for these GUI tests on one desktop session. Two
workers would fight over keyboard focus and the same Simplicity Studio UI.
