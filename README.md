# DesktopTester

A Cypress-like UAT testing tool for desktop applications. Record, edit, and play back automated tests against native macOS (and eventually Windows) apps using accessibility APIs.

## Requirements

- Python 3.10+
- macOS (primary platform; Windows support planned)
- Accessibility permissions enabled in **System Settings > Privacy & Security > Accessibility** for your terminal/IDE

## Installation

```bash
# Clone the repo
git clone https://github.com/your-org/DesktopTester.git
cd DesktopTester

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with macOS extras
pip install -e ".[macos]"

# Or install with dev tools included
pip install -e ".[macos,dev]"
```

## Quick Start

### 1. Create a project

**Via CLI:**

```bash
desktop-tester init my_project --name "My App Tests" --target "com.apple.calculator"
```

This creates a project directory with the following structure:

```
my_project/
├── project.yaml       # Project configuration
├── tests/             # Test YAML files go here
├── fixtures/          # Test data / fixtures
├── screenshots/       # Auto-captured screenshots
└── reports/           # Generated HTML/JSON reports
```

**Via GUI:**

```bash
desktop-tester gui
```

Then use **File > New Project** and fill in the project name and target application.

### 2. Configure the target application

Edit `project.yaml` to point at your app:

```yaml
name: My App Tests
version: "1.0"
target_app:
  name: Calculator
  bundle_id: com.apple.calculator
settings:
  screenshot_on_failure: true
  screenshot_on_step: false
  default_timeout: 5.0
directories:
  tests: tests
  screenshots: screenshots
  reports: reports
```

### 3. Record a test

1. Launch the GUI: `desktop-tester gui`
2. Open your project via **File > Open Project**
3. Make sure the target app is running (or let the tool launch it)
4. Click **Record** in the toolbar
5. Interact with the target application — clicks and keystrokes are captured as steps
6. Click **Stop** when done
7. Save with **Ctrl+S** (or **File > Save**)

The recorded test is saved as a YAML file in your project's `tests/` directory.

### 4. Edit tests

Tests are human-readable YAML files. You can edit them in any text editor or use the GUI's step editor.

```yaml
name: "Basic Addition"
description: "Verify that 2 + 3 equals 5"
tags:
  - smoke
  - arithmetic

setup:
  - id: setup_1
    action: launch_app
    description: "Launch Calculator"
  - id: setup_2
    action: wait_for_window
    title: "Calculator"
    timeout: 10

steps:
  - id: step_1
    description: "Click the 2 button"
    action: click
    target:
      type: accessibility_id
      value: "Two"

  - id: step_2
    description: "Click the + button"
    action: click
    target:
      type: accessibility_id
      value: "Add"

  - id: step_3
    description: "Click the 3 button"
    action: click
    target:
      type: accessibility_id
      value: "Three"

  - id: step_4
    description: "Click equals"
    action: click
    target:
      type: accessibility_id
      value: "Equals"

  - id: step_5
    description: "Verify result is 5"
    action: assert
    assertion:
      type: element_text
      target:
        type: text_content
        value: "5"
      operator: equals
      expected: "5"

teardown:
  - id: teardown_1
    action: close_app
    description: "Close Calculator"
```

**In the GUI**, you can also:

- Click **+ Add Step** to add steps manually
- Use the **Pick Element** button on assertion steps to click an element in the target app and auto-populate the target and expected value
- Right-click a test in the explorer to delete it

### 5. Run tests

**Via GUI:**

- **Run** (Ctrl+Enter) — runs the currently loaded test
- **Run All** — runs every test in the project

Results appear in the **Results** tab, grouped by test with collapsible sections. Each step shows pass/fail status and duration. Failed steps show error details on hover.

**Via CLI:**

```bash
# Run all tests in a project
desktop-tester run my_project

# Run specific test files
desktop-tester run my_project -t tests/test_login.yaml

# Run with an HTML report
desktop-tester run my_project --report html

# Run with slow mode (pause between steps)
desktop-tester run my_project --slow-mode 0.5

# Verbose output
desktop-tester run my_project -v
```

Exit codes: `0` = all passed, `1` = failures or errors.

### 6. Generate reports

Reports are generated automatically after a CLI run. You can also generate them separately:

```bash
desktop-tester report results.json --format html --output report.html
```

HTML reports are self-contained (screenshots embedded as base64) and can be shared directly.

## Test YAML Reference

### Actions

| Action | Description | Key Fields |
|---|---|---|
| `click` | Left-click an element | `target` |
| `double_click` | Double-click an element | `target` |
| `right_click` | Right-click an element | `target` |
| `type_text` | Type text into the focused element | `text` |
| `key_combo` | Press a key combination | `keys` (e.g. `["cmd", "c"]`) |
| `clear_field` | Clear a text field | `target` |
| `select_menu` | Select a menu item | `target` |
| `launch_app` | Launch the target application | |
| `close_app` | Close the target application | |
| `wait` | Wait a fixed duration | `duration` (seconds) |
| `wait_for_element` | Wait until an element appears | `target`, `timeout` |
| `wait_for_element_gone` | Wait until an element disappears | `target`, `timeout` |
| `wait_for_window` | Wait for a window by title | `title`, `timeout` |
| `assert` | Assert a condition on an element | `assertion` |

### Locator Types

Elements are found using a `target` block:

```yaml
target:
  type: accessibility_id    # Primary locator
  value: "MyButton"
  fallback:                 # Optional fallback
    type: role_label
    value: "Submit"
    role: button
```

| Type | Description |
|---|---|
| `accessibility_id` | The element's accessibility identifier |
| `role_label` | Match by role + label (e.g. button named "OK") |
| `role_title` | Match by role + title |
| `text_content` | Find element containing specific text |
| `path` | Accessibility tree path |

### Assertion Types

```yaml
assertion:
  type: element_text       # What to check
  operator: equals         # How to compare
  expected: "5"            # Expected value
```

| Type | Description |
|---|---|
| `element_exists` | Element is present in the UI |
| `element_not_exists` | Element is not present |
| `element_text` | Compare the element's visible text |
| `element_value` | Compare the element's value attribute |
| `element_enabled` | Check if the element is enabled |
| `element_visible` | Check if the element is visible |

| Operator | Description |
|---|---|
| `equals` / `not_equals` | Exact match |
| `contains` / `not_contains` | Substring match |
| `starts_with` / `ends_with` | Prefix/suffix match |
| `greater_than` / `less_than` | Numeric comparison |
| `matches_regex` | Regular expression match |

### Test Structure

Each test file supports three sections that run in order:

- **setup** — runs before the main steps; aborts the test if any step fails
- **steps** — the main test body; failures stop execution (unless `continue_on_failure: true`)
- **teardown** — always runs, even if steps fail (use for cleanup like closing the app)

## GUI Overview

The GUI has a 3-panel layout inspired by Cypress:

| Panel | Purpose |
|---|---|
| **Left — Test Explorer** | Browse and select test files in your project |
| **Center — Command Log** | View the ordered list of steps; live status during runs |
| **Right — Detail Tabs** | Step editor, screenshot viewer, YAML code view, and results |

## Troubleshooting

**"Accessibility permissions" error on macOS**

Go to **System Settings > Privacy & Security > Accessibility** and add your terminal app (Terminal, iTerm2, VS Code, etc.).

**Element picker doesn't select anything**

Make sure the target application is in the foreground and not obscured. The picker uses the accessibility API to resolve the element under your cursor.

**Tests fail on the first step after a previous test closed the app**

This is handled automatically — the runner reconnects to or relaunches the target app between tests. Make sure your `project.yaml` has the correct `bundle_id` or `name` for the target app.

## License

MIT
