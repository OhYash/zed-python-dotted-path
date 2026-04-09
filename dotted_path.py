"""Compute the dotted import path at the cursor position in a Python file.

Invoked as a Zed Task. Reads ZED_FILE, ZED_ROW, and ZED_WORKTREE_ROOT
from environment variables.
"""

import ast
import os
import sys
from pathlib import Path


def get_env():
    """Read and validate required environment variables.

    Returns (file, row, worktree_root) or prints an error and exits.
    """
    zed_file = os.environ.get("ZED_FILE")
    zed_row = os.environ.get("ZED_ROW")
    zed_worktree_root = os.environ.get("ZED_WORKTREE_ROOT")

    if not zed_file:
        print("Error: ZED_FILE not set", file=sys.stderr)
        sys.exit(1)
    if not zed_row:
        print("Error: ZED_ROW not set", file=sys.stderr)
        sys.exit(1)
    if not zed_worktree_root:
        print("Error: ZED_WORKTREE_ROOT not set", file=sys.stderr)
        sys.exit(1)

    try:
        row = int(zed_row)
    except ValueError:
        print(f"Error: ZED_ROW is not an integer: {zed_row}", file=sys.stderr)
        sys.exit(1)

    if row < 1:
        print(f"Error: ZED_ROW must be >= 1, got {row}", file=sys.stderr)
        sys.exit(1)

    file_path = Path(zed_file)
    if not file_path.is_file():
        print(f"Error: ZED_FILE does not exist: {zed_file}", file=sys.stderr)
        sys.exit(1)

    worktree_root = Path(zed_worktree_root)
    if not worktree_root.is_dir():
        print(f"Error: ZED_WORKTREE_ROOT is not a directory: {zed_worktree_root}", file=sys.stderr)
        sys.exit(1)

    return file_path.resolve(), row, worktree_root.resolve()


def _find_pyproject(file_path, worktree_root):
    """Walk up from file_path to worktree_root looking for pyproject.toml."""
    current = file_path.parent
    while True:
        candidate = current / "pyproject.toml"
        if candidate.is_file():
            return candidate
        if current == worktree_root:
            break
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _parse_toml_value(raw):
    """Minimal TOML string/array parser for the values we care about.

    Handles: bare strings, quoted strings, and single-element arrays of strings.
    """
    raw = raw.strip()
    # Array: ["src"] or ["src", "lib"]
    if raw.startswith("["):
        inner = raw.strip("[]").strip()
        if not inner:
            return []
        # Split on commas, take first element
        first = inner.split(",")[0].strip().strip("'\"")
        return [first]
    # Quoted string
    if raw.startswith(("'", '"')):
        return raw.strip("'\"")
    return raw


def _root_from_pyproject(pyproject_path):
    """Try to extract project root from pyproject.toml.

    Returns resolved root Path or None.
    Priority 1: [tool.dotted-path] root = "..."
    Priority 2: [tool.setuptools.packages.find] where = [...]
    """
    pyproject_dir = pyproject_path.parent
    try:
        text = pyproject_path.read_text(encoding="utf-8")
    except OSError:
        return None

    # Parse TOML manually (stdlib has tomllib only in 3.11+).
    # We only need two specific keys, so we do a simple section-aware scan.
    current_section = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and not stripped.startswith("[["):
            current_section = stripped.strip("[] ").lower()
            continue
        if "=" not in stripped:
            continue
        key, _, val = stripped.partition("=")
        key = key.strip().lower()
        val = val.strip()

        if current_section == "tool.dotted-path" and key == "root":
            parsed = _parse_toml_value(val)
            if isinstance(parsed, list):
                parsed = parsed[0] if parsed else None
            if parsed:
                return (pyproject_dir / parsed).resolve()

        if current_section == "tool.setuptools.packages.find" and key == "where":
            parsed = _parse_toml_value(val)
            if isinstance(parsed, list) and parsed:
                return (pyproject_dir / parsed[0]).resolve()
            if isinstance(parsed, str) and parsed:
                return (pyproject_dir / parsed).resolve()

    return None


def _root_from_markers(file_path, worktree_root):
    """Walk up from file looking for marker files (manage.py, setup.py, setup.cfg)."""
    markers = ("manage.py", "setup.py", "setup.cfg")
    current = file_path.parent
    while True:
        for marker in markers:
            if (current / marker).is_file():
                return current
        if current == worktree_root:
            break
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _root_from_init_heuristic(file_path, worktree_root):
    """Find topmost dir with __init__.py; its parent is the root."""
    topmost_pkg = None
    current = file_path.parent
    while True:
        if (current / "__init__.py").is_file():
            topmost_pkg = current
        else:
            # Gap in __init__.py chain — stop
            if topmost_pkg is not None:
                break
        if current == worktree_root:
            break
        parent = current.parent
        if parent == current:
            break
        current = parent
    if topmost_pkg is not None:
        return topmost_pkg.parent
    return None


def resolve_project_root(file_path, worktree_root):
    """Resolve the Python project root using the 5-level priority chain."""
    # Priority 1 & 2: pyproject.toml
    pyproject = _find_pyproject(file_path, worktree_root)
    if pyproject:
        root = _root_from_pyproject(pyproject)
        if root:
            return root

    # Priority 3: marker files
    root = _root_from_markers(file_path, worktree_root)
    if root:
        return root

    # Priority 4: __init__.py heuristic
    root = _root_from_init_heuristic(file_path, worktree_root)
    if root:
        return root

    # Priority 5: fallback
    return worktree_root


def compute_module_path(file_path, project_root):
    """Convert file path to dotted module path relative to project root."""
    try:
        rel = file_path.relative_to(project_root)
    except ValueError:
        # File is outside project root — use filename stem
        return file_path.stem

    parts = list(rel.with_suffix("").parts)
    # Strip __init__ from tail
    if parts and parts[-1] == "__init__":
        parts.pop()
    if not parts:
        # Edge case: project root itself is an __init__.py
        return file_path.parent.name
    return ".".join(parts)


def resolve_scope(file_path, row):
    """Parse file and find the class/function scope chain enclosing the given row."""
    try:
        source = file_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error: cannot read file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        print(f"Error: cannot parse file: {e}", file=sys.stderr)
        sys.exit(1)

    scope_chain = []
    _walk_scope(tree, row, scope_chain)
    return scope_chain


def _walk_scope(node, row, chain):
    """Recursively find the innermost scope enclosing the row."""
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # Use the line of the def/class keyword, not decorators
        start = child.lineno
        end = child.end_lineno
        if end is None:
            continue
        if start <= row <= end:
            chain.append(child.name)
            _walk_scope(child, row, chain)
            return


def main():
    file_path, row, worktree_root = get_env()
    project_root = resolve_project_root(file_path, worktree_root)
    module_path = compute_module_path(file_path, project_root)
    scope_chain = resolve_scope(file_path, row)
    parts = [module_path] + scope_chain if module_path else scope_chain
    dotted_path = ".".join(parts)
    # TODO: copy to clipboard
    print(dotted_path)


if __name__ == "__main__":
    main()
