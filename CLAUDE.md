# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A stdlib-only Python script that computes the dotted import path at the cursor position in a Python file, invoked as a Zed Task. Not a WASM extension. Full design in `SPEC.md`.

## Key Files

- `dotted_path.py` — the script (uses `ast`, `os`, `subprocess`, `pathlib`)
- `SPEC.md` — design spec: root resolution, AST walking, edge cases, UX
- `docs/` — local Zed documentation snapshots

## Running

```sh
ZED_FILE=/path/to/file.py ZED_ROW=25 ZED_WORKTREE_ROOT=/path/to/project python3 dotted_path.py
```

## Zed documentation

Local snapshots (may go stale):
- `docs/zed-tasks.md` — task config, env vars, tags
- `docs/zed-extension-api.md` — what the WASM API can/cannot do
- `docs/zed-keybindings.md` — binding tasks to keys

Upstream (authoritative):
- Tasks: https://zed.dev/docs/tasks
- Keybindings: https://zed.dev/docs/key-bindings
