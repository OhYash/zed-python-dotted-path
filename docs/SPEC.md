# Spec: zed-python-dotted-path

## Goal

Given a cursor position in a Python file, compute the full dotted import path — e.g. `mypackage.submodule.MyClass.my_method` — and copy it to the clipboard. Invoked from Zed via a keybinding.

## Why not a WASM extension?

The Zed extension API (v0.7.0) has **no way** to register editor commands or access cursor position/buffer contents. It only supports language servers, debug adapters, slash commands (AI chat), themes, and snippets.

**Zed Tasks**, however, expose exactly the context we need as environment variables:

| Variable             | Description                          | Used? |
|----------------------|--------------------------------------|-------|
| `ZED_FILE`           | Absolute path to the current file    | Yes   |
| `ZED_ROW`            | Cursor line number (1-indexed)       | Yes   |
| `ZED_WORKTREE_ROOT`  | Absolute path to the project root    | Yes   |

## Architecture

```
┌─────────────────────────────────────┐
│  Zed Task (keybinding: user-chosen) │
│  runs: python dotted_path.py        │
│  env:  ZED_FILE, ZED_ROW,           │
│        ZED_WORKTREE_ROOT            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  dotted_path.py                     │
│  1. Read ZED_FILE, ZED_ROW from env │
│  2. Parse file with ast module      │
│  3. Walk AST to find enclosing      │
│     scope(s) at ZED_ROW             │
│  4. Compute module dotted path      │
│     relative to ZED_WORKTREE_ROOT   │
│  5. Combine: module + class/func    │
│  6. Copy to clipboard               │
│  7. Print result to terminal        │
└─────────────────────────────────────┘
```

### Single file: `dotted_path.py`

No dependencies beyond the Python stdlib. Uses `ast` for parsing and `subprocess` for clipboard (xclip/xsel on Linux, pbcopy on macOS, clip.exe on WSL/Windows).

## Project root resolution

The "project root" determines where the dotted module path starts. Getting this right is critical — in a Django project, the root is where `manage.py` lives, not necessarily `ZED_WORKTREE_ROOT`.

### Priority order

1. **User override via `pyproject.toml`** (highest priority)

   ```toml
   [tool.dotted-path]
   root = "src"          # relative to pyproject.toml location
   ```

   The `root` value is a path relative to the directory containing `pyproject.toml`. This handles src-layout projects and monorepos where the Python root isn't the repo root.

2. **Auto-detect from `pyproject.toml` setuptools config**

   If `[tool.dotted-path]` is absent, check for:

   ```toml
   [tool.setuptools.packages.find]
   where = ["src"]
   ```

   Use the first entry of `where` as the root, relative to `pyproject.toml` location.

3. **Auto-detect from marker files**

   Walk up from `ZED_FILE` toward `ZED_WORKTREE_ROOT`, looking for (in order):
   - `manage.py` — Django project root
   - `setup.py` or `setup.cfg` — legacy project root

   Use the directory containing the first marker found. (`pyproject.toml` is not a marker here — it's already handled by priorities 1-2.)

4. **`__init__.py` heuristic** (fallback)

   Walk up from the file looking for the topmost directory that contains `__init__.py`. The parent of that directory is the root.

   ```
   /home/user/myproject/src/mypackage/__init__.py  ✓
   /home/user/myproject/src/__init__.py            ✗

   → root: /home/user/myproject/src/
   ```

5. **`ZED_WORKTREE_ROOT`** (last resort)

### Config file search

To find `pyproject.toml`, walk up from `ZED_FILE` toward (and including) `ZED_WORKTREE_ROOT`. Stop at the first `pyproject.toml` found. Do not search above `ZED_WORKTREE_ROOT`.

## Dotted path resolution

### Step 1: Module path

Convert the file path to a dotted module path relative to the resolved project root.

```
project root = /home/user/myproject/src/    (from pyproject.toml [tool.dotted-path] root = "src")
ZED_FILE     = /home/user/myproject/src/mypackage/utils/helpers.py

→ mypackage.utils.helpers
```

Strip `__init__` from the tail — `mypackage/__init__.py` becomes just `mypackage`.

### Step 2: Scope at cursor

Parse the file with `ast.parse()`. Walk the AST to find all `ClassDef` and `FunctionDef`/`AsyncFunctionDef` nodes whose line range encloses `ZED_ROW`. Build a chain from outermost to innermost:

```python
# ZED_ROW = 25, which falls inside:
class MyClass:          # line 10-50
    def my_method(self):  # line 20-30
        ...               # ← cursor here

→ scope chain: ["MyClass", "my_method"]
```

### Step 3: Combine

```
mypackage.utils.helpers.MyClass.my_method
```

Copy to clipboard, print to terminal.

## Edge cases

- **Cursor on module-level code** (not inside any class/function): return just the module path.
- **Nested classes/functions**: include the full nesting chain.
- **`__init__.py`**: module path should end at the package name, not `__init__`.
- **Decorated functions**: use the `def` line range, not the decorator line.
- **File outside any package** (no `__init__.py` anywhere): use filename stem as module name.
- **No `pyproject.toml` found**: fall through the priority chain to `__init__.py` heuristic then `ZED_WORKTREE_ROOT`.
- **`pyproject.toml` exists but no `[tool.dotted-path]` or setuptools config**: use `pyproject.toml` directory as root, then check `__init__.py` heuristic.
- **Monorepo with multiple `pyproject.toml`**: the first one found walking up from the file wins (closest to the file).

## UX: How the user invokes it

The Zed extension API (v0.7.0) does not support registering command palette entries or right-click context menu items. These are the available integration points, from most seamless to least:

### Primary: Keybinding (recommended)

One keypress, no menus. Add to `~/.config/zed/keymap.json`:

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

### Secondary: Task spawn modal

Open the command palette (`ctrl-shift-p`), type `task: spawn`, then select "Copy Python dotted path" from the list. Two steps, but discoverable without memorizing a keybinding.

### Tertiary: Code actions menu (`ctrl-.`)

Tasks with a matching `tags` value appear in the lightbulb / code actions dropdown. This is the closest thing to a context menu. Requires the task to have a tag that Zed recognizes for Python files.

### Not possible today

- **Command palette entry**: Extensions cannot register custom actions that appear directly in the command palette.
- **Right-click context menu item**: No API for injecting into context menus.

If Zed adds extension command registration in the future, this project should adopt it.

## Installation

Users add to `~/.config/zed/tasks.json` (global) or `.zed/tasks.json` (project):

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

## Clipboard strategy

Try in order:
1. **Linux**: `xclip -selection clipboard` or `xsel --clipboard --input`
2. **macOS**: `pbcopy`
3. **WSL/Windows**: `clip.exe`
4. **Fallback**: print to stdout only (no clipboard), exit 0

## Output

On success, print the dotted path to the terminal so the user sees confirmation, then exit 0.

On failure (e.g. file not parseable), print an error message and exit 1.

## Files to create

```
zed-python-dotted-path/
├── dotted_path.py       # The script (stdlib-only)
├── tests/               # Tests (unittest, no external deps)
├── docs/                # Local Zed documentation snapshots (already exists)
├── SPEC.md              # This file (already exists)
├── README.md            # Usage and installation (already exists)
├── LICENSE              # MIT (already exists)
└── CLAUDE.md            # Dev guidance (already exists)
```
