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
    "hide": "on_success",
    "tags": ["python-dotted-path"]
  }
]
```

3. (Optional) Bind a key in `~/.config/zed/keymap.json`:

```json
[
  {
    "context": "Editor && extension==py",
    "bindings": {
      "ctrl-shift-c": ["task::Spawn", { "task_name": "Copy Python dotted path" }]
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
root = "src"   # relative to pyproject.toml location
```

Without this, the script auto-detects using marker files and `__init__.py` heuristics.

## Requirements

- Python 3 (stdlib only, no dependencies)
- A clipboard utility: `xclip` or `xsel` (Linux), `pbcopy` (macOS), `clip.exe` (WSL)

## Examples

| Cursor position | Output |
|---|---|
| Inside `MyClass.my_method` in `pkg/utils.py` | `pkg.utils.MyClass.my_method` |
| Module-level code in `pkg/utils.py` | `pkg.utils` |
| Inside nested class in `pkg/__init__.py` | `pkg.OuterClass.InnerClass` |

## License

MIT
