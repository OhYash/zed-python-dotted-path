# zed-python-dotted-path

Copy the Python dotted import path at your cursor position in [Zed](https://zed.dev).

Place your cursor inside a class or function, trigger the task, and get `mypackage.utils.helpers.MyClass.my_method` copied to your clipboard.

## Installation

1. Download `dotted_path.py` somewhere on your system (e.g. `~/.local/bin/dotted_path.py`).

2. Add a task to `~/.config/zed/tasks.json` (global) or `.zed/tasks.json` (per-project):

```json
[
  {
    "label": "Copy Python dotted path",
    "command": "python3",
    "args": ["/path/to/dotted_path.py"],
    "reveal": "never",
    "hide": "always",
    "tags": ["python-dotted-path"]
  }
]
```

3. (Optional) Bind a key in `~/.config/zed/keymap.json`:

**Linux/Windows** — matches PyCharm's "Copy Reference" shortcut:

```json
[
  {
    "context": "Editor && extension==py",
    "bindings": {
      // PyCharm: Ctrl+Shift+Alt+C = Copy Reference
      "ctrl-shift-alt-c": ["task::Spawn", { "task_name": "Copy Python dotted path" }]
    }
  }
]
```

**macOS**:

```json
[
  {
    "context": "Editor && extension==py",
    "bindings": {
      // PyCharm: Cmd+Shift+Alt+C = Copy Reference
      "cmd-shift-alt-c": ["task::Spawn", { "task_name": "Copy Python dotted path" }]
    }
  }
]
```

## How it works

Zed tasks expose editor context via environment variables (`ZED_FILE`, `ZED_ROW`, `ZED_WORKTREE_ROOT`). The script:

1. Resolves the Python project root — checks `[tool.dotted-path]` in `pyproject.toml`, then setuptools config, then marker files (`manage.py`, `setup.py`), then the `__init__.py` chain, then falls back to the Zed worktree root
2. Converts the file path to a dotted module path relative to that root
3. Parses the file with `ast` to find the class/function enclosing the cursor line
4. Combines them and copies the result to the clipboard

## Configuration

To set a custom project root (e.g. for src-layout or Django projects), add to your `pyproject.toml`:

```toml
[tool.dotted-path]
root = "src"          # relative to pyproject.toml location
skip_fixtures = true  # strip setUp/tearDown from test classes
```

`skip_fixtures` omits known test fixture methods (`setUp`, `tearDown`, `setUpClass`, `tearDownClass`, and their pytest equivalents) when the cursor is inside a `Test*` class, returning just the class path instead.

Without `root`, the script auto-detects using marker files and `__init__.py` heuristics.

## Requirements

- Python 3 (stdlib only, no dependencies)
- A clipboard utility: `xclip` or `xsel` (Linux), `pbcopy` (macOS), `clip.exe` (WSL)

## Examples

| Cursor position | Output |
|---|---|
| Inside `MyClass.my_method` in `pkg/utils.py` | `pkg.utils.MyClass.my_method` |
| Module-level code in `pkg/utils.py` | `pkg.utils` |
| Inside nested class in `pkg/__init__.py` | `pkg.OuterClass.InnerClass` |

## FAQ

**Nothing happens when I trigger the task.**

The recommended config uses `"reveal": "never"` which hides the terminal completely. To debug, temporarily change to `"reveal": "always"` and `"hide": "never"` in your `tasks.json` to see the script output. Common issues:

- **Missing clipboard utility**: install `xclip` or `xsel` (`sudo apt install xclip` on Debian/Ubuntu, `sudo pacman -S xclip` on Arch). The path still prints to the terminal but won't reach your clipboard without one.
- **Wrong Python path**: make sure the `args` path in `tasks.json` points to where you actually saved `dotted_path.py`.
- **File not in a Python project**: if there's no `__init__.py`, `pyproject.toml`, or marker files, the script falls back to the Zed worktree root, which may not produce the path you expect. Add a `[tool.dotted-path]` section to your `pyproject.toml` to set the root explicitly.

**The path includes `setUp` / `tearDown` instead of the test class.**

Add to the `pyproject.toml` closest to your source files:

```toml
[tool.dotted-path]
skip_fixtures = true
```

This strips known fixture methods when the cursor is inside a `Test*` class. If your project has multiple `pyproject.toml` files (e.g. a monorepo), add it to the one closest to your test files.

**How do I know the path was copied?**

Zed tasks don't support in-editor notifications. The path is silently copied to your clipboard. If you want visual confirmation, change the task config to `"reveal": "no_focus"` — the terminal tab will briefly appear in the background without stealing focus.

## License

MIT
