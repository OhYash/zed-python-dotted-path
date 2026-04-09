# Build Plan

Incremental build plan for `dotted_path.py`. Each step is a self-contained commit.

## Steps

- [x] **1. Scaffold CLI entry point**
  Read `ZED_FILE`, `ZED_ROW`, `ZED_WORKTREE_ROOT` from env. Validate (file exists, row is int). Print error + exit 1 on bad input. Stub `main()`.

- [ ] **2. Project root resolution**
  Implement the 5-level priority chain:
  1. `[tool.dotted-path]` root in `pyproject.toml`
  2. `[tool.setuptools.packages.find]` where in `pyproject.toml`
  3. Marker files (`manage.py`, `setup.py`, `setup.cfg`) walking up from file
  4. `__init__.py` heuristic (topmost dir with `__init__.py`, parent is root)
  5. `ZED_WORKTREE_ROOT` fallback

  `pyproject.toml` search: walk up from `ZED_FILE` to `ZED_WORKTREE_ROOT`, stop at first found.

- [ ] **3. Dotted module path computation**
  Convert file path to dotted module path relative to resolved root. Strip `__init__` from tail. Handle file outside any package (use filename stem).

- [ ] **4. AST scope resolution**
  Parse with `ast.parse()`. Walk AST for `ClassDef`, `FunctionDef`, `AsyncFunctionDef` enclosing `ZED_ROW`. Build outermost→innermost chain. Handle nested scopes, decorated functions, module-level cursor.

- [ ] **5. Clipboard copy and output**
  Combine module path + scope chain. Platform clipboard detection (xclip → xsel → pbcopy → clip.exe → stdout-only fallback). Print result, exit 0/1.

- [ ] **6. Tests**
  `tests/` with unittest. Cover: env var validation, all 5 root resolution levels, module path edge cases, AST scope cases (nested, async, decorated, module-level), unparseable files. Use temp directories.

## Dependencies

```
1 → 2 → 3 ─┐
1 → 4 ──────┤→ 5 → 6
```

Steps 2 and 4 can be worked in parallel after step 1.
