# Zed Tasks Reference

Source: https://zed.dev/docs/tasks

## Overview

Zed tasks spawn commands in the integrated terminal. Two primary actions:
- `task: spawn` — opens modal with all available tasks
- `task: rerun` — reruns the most recently spawned task

## Task definition locations

1. **Global**: `~/.config/zed/tasks.json` — available across all projects
2. **Project**: `.zed/tasks.json` — project-specific
3. **Oneshot**: ad-hoc commands via the task modal
4. **Language extensions**: provided by language support

## Task configuration fields

```json
{
  "label": "task name",
  "command": "shell command",
  "args": [],
  "env": { "VAR": "value" },
  "cwd": "/working/directory",
  "use_new_terminal": false,
  "allow_concurrent_runs": false,
  "reveal": "always",
  "hide": "never",
  "shell": "system",
  "save": "none",
  "tags": []
}
```

## Environment variables (editor context)

Zed automatically populates these when a task runs:

| Variable | Description |
|---|---|
| `ZED_FILE` | Absolute path to currently opened file |
| `ZED_FILENAME` | Just the filename (e.g. `main.rs`) |
| `ZED_DIRNAME` | Directory path without filename |
| `ZED_RELATIVE_FILE` | File path relative to project root |
| `ZED_RELATIVE_DIR` | Directory path relative to project root |
| `ZED_STEM` | Filename without extension |
| `ZED_ROW` | Current cursor line number (1-indexed) |
| `ZED_COLUMN` | Current cursor column (1-indexed) |
| `ZED_SYMBOL` | Currently selected symbol from breadcrumb |
| `ZED_SELECTED_TEXT` | Currently highlighted text |
| `ZED_LANGUAGE` | Language of current buffer |
| `ZED_WORKTREE_ROOT` | Absolute project root path |
| `ZED_CUSTOM_RUST_PACKAGE` | Parent package name (Rust-specific) |

## Variable syntax

- Basic: `$VAR_NAME`
- With default: `${ZED_FILE:default_value}`
- Tasks containing undefined variables (without defaults) are filtered from the spawn modal.

## Keybinding a task

In `~/.config/zed/keymap.json`:

```json
{
  "context": "Workspace",
  "bindings": {
    "alt-g": ["task::Spawn", { "task_name": "task label" }]
  }
}
```

## Tags and code actions

The `tags` field controls inline runnable indicators. Tasks with matching tags appear in the code actions dropdown (`ctrl-.` / `cmd-.`). For example, a task tagged `"rust-test"` appears when the cursor is on a Rust test.

## Hide behavior

- `"hide": "never"` — always show terminal
- `"hide": "always"` — always hide terminal
- `"hide": "on_success"` — hide only if exit code is 0
