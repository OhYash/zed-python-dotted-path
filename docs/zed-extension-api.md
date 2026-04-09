# Zed Extension API Reference

Source: https://docs.rs/zed_extension_api/0.7.0/zed_extension_api/

## Overview

Zed extensions are Rust crates compiled to WebAssembly (`wasm32-wasip1`). Version: 0.7.0.

## Prerequisites

- Rust installed via **rustup** (not homebrew or system package managers)
- WASM target: `rustup target add wasm32-wasip1`

## Minimal project structure

```
my-extension/
  extension.toml    # Extension metadata
  Cargo.toml        # Rust dependencies
  src/
    lib.rs          # Entry point
```

### extension.toml

```toml
id = "my-extension"
name = "My extension"
version = "0.0.1"
schema_version = 1
authors = ["Your Name <you@example.com>"]
description = "Example extension"
repository = "https://github.com/your-name/my-zed-extension"
```

### Cargo.toml

```toml
[package]
name = "my-extension"
version = "0.0.1"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
zed_extension_api = "0.7.0"
```

### src/lib.rs

```rust
use zed_extension_api as zed;

struct MyExtension;

impl zed::Extension for MyExtension {
    fn new() -> Self {
        MyExtension
    }
}

zed::register_extension!(MyExtension);
```

## Extension trait — all methods

### Required

- `new() -> Self` — constructor

### Optional (language servers)

- `language_server_command()` — command to launch an LSP
- `language_server_initialization_options()` — JSON init options for LSP
- `language_server_workspace_configuration()` — workspace settings for LSP
- `language_server_additional_initialization_options()` — supplementary init config for inter-server communication
- `language_server_additional_workspace_configuration()` — extra workspace settings for inter-server communication

### Optional (code presentation)

- `label_for_completion()` — custom labels for autocomplete items
- `label_for_symbol()` — custom labels for symbols in outline/navigation

### Optional (slash commands — AI chat)

- `complete_slash_command_argument()` — argument completions for slash commands
- `run_slash_command()` — execute a slash command

### Optional (context servers)

- `context_server_command()` — executable for context server
- `context_server_configuration()` — context server config

### Optional (docs)

- `suggest_docs_packages()` — package suggestions for `/docs`
- `index_docs()` — index docs into key-value store

### Optional (debug adapters)

- `get_dap_binary()` — locate debug adapter executable
- `dap_request_kind()` — launch vs attach
- `dap_config_to_scenario()` — convert debug config to adapter scenario
- `dap_locator_create_scenario()` — build task → debug scenario
- `run_dap_locator()` — discover debuggee artifact

## Key structs

| Struct | Purpose |
|---|---|
| `Project` | A Zed project |
| `Worktree` | A Zed worktree (has `id()`, `root_path()`, `read_text_file()`, `which()`, `shell_env()`) |
| `KeyValueStore` | Persistent key-value storage |
| `SlashCommand` | Slash command definition (name, description, tooltip_text, requires_argument) |
| `SlashCommandOutput` | Result of running a slash command |
| `CodeLabel` | Styled code label for completions/symbols |
| `Command` | Subprocess builder (command, args, env → output) |
| `TaskTemplate` | Task template definition |

## What the API CANNOT do (as of v0.7.0)

- Register editor commands / command palette entries
- Access cursor position or buffer contents
- Add right-click context menu items
- Copy to clipboard
- Show notifications/toasts
- Register keybindings

## Capabilities system

Extensions can request:
1. `process:exec` — run external commands
2. `download_file` — download from specified hosts
3. `npm:install` — install npm packages

Users can restrict these via `granted_extension_capabilities` setting.

## Debugging extensions

- `println!` / `dbg!` output goes to the Zed process stdout
- Launch Zed with `zed --foreground` to see output in terminal
- Check `Zed.log` via `zed: open log` action

## Installing dev extensions

1. In Zed: `Extensions > Install Dev Extension` (or action `zed: install dev extension`)
2. Point to the extension directory
3. If a published version exists, it shows "Overridden by dev extension"
