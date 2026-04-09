"""Compute the dotted import path at the cursor position in a Python file.

Invoked as a Zed Task. Reads ZED_FILE, ZED_ROW, and ZED_WORKTREE_ROOT
from environment variables.
"""

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


def main():
    file_path, row, worktree_root = get_env()
    # TODO: resolve project root
    # TODO: compute dotted module path
    # TODO: resolve AST scope at cursor
    # TODO: combine and copy to clipboard
    print(f"file={file_path} row={row} root={worktree_root}")


if __name__ == "__main__":
    main()
