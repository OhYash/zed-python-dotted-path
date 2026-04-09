# Zed Keybindings Reference

Source: https://zed.dev/docs/key-bindings

## Binding a task to a key

In `~/.config/zed/keymap.json`:

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

## Context expressions

Keybindings use context expressions to control when they're active:

- `Editor` — any editor is focused
- `Workspace` — any workspace context
- `extension==py` — file extension is `.py`
- Combine with `&&`: `"Editor && extension==py"`

## Actions

Almost all Zed functionality is exposed as actions. Actions are invoked by name:

- `task::Spawn` — open task picker or spawn a named task
- `task::Rerun` — rerun most recent task
- `editor::Copy` — copy selection
- `workspace::SendKeystrokes` — simulate keypresses

## Task spawn with args

```json
["task::Spawn", { "task_name": "my task" }]
```

The `task_name` must match the `label` field in the task definition exactly.
