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
- `matrix.py`: validates and loads enabled YAML test cases.
- `configuration.py`: machine/runtime settings with environment overrides.

## Design rule

Keep test data in YAML, orchestration in pytest, and UI implementation in
`src/studio_automation`. New test cases should normally not require Python
code changes.

## Parallel execution

Do not use pytest-xdist for these GUI tests on one desktop session. Two
workers would fight over keyboard focus and the same Simplicity Studio UI.
