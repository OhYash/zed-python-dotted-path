"""Tests for dotted_path.py."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path so we can import the module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import dotted_path


class TestGetEnv(unittest.TestCase):
    """Tests for environment variable validation."""

    def _run_script(self, env_override):
        """Run dotted_path.py with given env vars, return (returncode, stderr)."""
        env = {k: v for k, v in env_override.items() if v is not None}
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "dotted_path.py")],
            capture_output=True, text=True, env=env,
        )
        return result.returncode, result.stderr

    def test_missing_zed_file(self):
        rc, err = self._run_script({"ZED_ROW": "1", "ZED_WORKTREE_ROOT": "/tmp"})
        self.assertEqual(rc, 1)
        self.assertIn("ZED_FILE", err)

    def test_missing_zed_row(self):
        with tempfile.NamedTemporaryFile(suffix=".py") as f:
            rc, err = self._run_script({"ZED_FILE": f.name, "ZED_WORKTREE_ROOT": "/tmp"})
        self.assertEqual(rc, 1)
        self.assertIn("ZED_ROW", err)

    def test_invalid_zed_row(self):
        with tempfile.NamedTemporaryFile(suffix=".py") as f:
            rc, err = self._run_script({
                "ZED_FILE": f.name, "ZED_ROW": "abc", "ZED_WORKTREE_ROOT": "/tmp",
            })
        self.assertEqual(rc, 1)
        self.assertIn("not an integer", err)

    def test_negative_zed_row(self):
        with tempfile.NamedTemporaryFile(suffix=".py") as f:
            rc, err = self._run_script({
                "ZED_FILE": f.name, "ZED_ROW": "0", "ZED_WORKTREE_ROOT": "/tmp",
            })
        self.assertEqual(rc, 1)
        self.assertIn(">= 1", err)


class TestResolveProjectRoot(unittest.TestCase):
    """Tests for the 5-level root resolution chain."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _make(self, rel_path, content=""):
        """Create a file with optional content."""
        p = self.root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def test_priority1_tool_dotted_path(self):
        self._make("pyproject.toml", '[tool.dotted-path]\nroot = "src"\n')
        self._make("src/pkg/__init__.py")
        target = self._make("src/pkg/mod.py")
        root, _ = dotted_path.resolve_project_root(target.resolve(), self.root.resolve())
        self.assertEqual(root, (self.root / "src").resolve())

    def test_priority2_setuptools_where(self):
        self._make("pyproject.toml",
                    '[tool.setuptools.packages.find]\nwhere = ["src"]\n')
        self._make("src/pkg/__init__.py")
        target = self._make("src/pkg/mod.py")
        root, _ = dotted_path.resolve_project_root(target.resolve(), self.root.resolve())
        self.assertEqual(root, (self.root / "src").resolve())

    def test_priority3_manage_py(self):
        self._make("manage.py")
        self._make("myapp/__init__.py")
        target = self._make("myapp/views.py")
        root, _ = dotted_path.resolve_project_root(target.resolve(), self.root.resolve())
        self.assertEqual(root, self.root.resolve())

    def test_priority3_setup_py(self):
        self._make("setup.py")
        self._make("pkg/__init__.py")
        target = self._make("pkg/mod.py")
        root, _ = dotted_path.resolve_project_root(target.resolve(), self.root.resolve())
        self.assertEqual(root, self.root.resolve())

    def test_priority4_init_heuristic(self):
        self._make("src/pkg/__init__.py")
        self._make("src/pkg/sub/__init__.py")
        target = self._make("src/pkg/sub/mod.py")
        root, _ = dotted_path.resolve_project_root(target.resolve(), self.root.resolve())
        self.assertEqual(root, (self.root / "src").resolve())

    def test_priority5_worktree_fallback(self):
        target = self._make("scripts/run.py")
        root, _ = dotted_path.resolve_project_root(target.resolve(), self.root.resolve())
        self.assertEqual(root, self.root.resolve())

    def test_pyproject_without_config_falls_through(self):
        """pyproject.toml exists but has no relevant config — fall through."""
        self._make("pyproject.toml", "[project]\nname = 'foo'\n")
        self._make("manage.py")
        self._make("app/__init__.py")
        target = self._make("app/mod.py")
        root, _ = dotted_path.resolve_project_root(target.resolve(), self.root.resolve())
        # Should find manage.py (priority 3), not worktree root
        self.assertEqual(root, self.root.resolve())

    def test_monorepo_closest_pyproject(self):
        """In a monorepo, the closest pyproject.toml to the file wins."""
        self._make("pyproject.toml", '[tool.dotted-path]\nroot = "."\n')
        self._make("services/api/pyproject.toml", '[tool.dotted-path]\nroot = "src"\n')
        self._make("services/api/src/api/__init__.py")
        target = self._make("services/api/src/api/views.py")
        root, _ = dotted_path.resolve_project_root(target.resolve(), self.root.resolve())
        self.assertEqual(root, (self.root / "services/api/src").resolve())

    def test_skip_fixtures_config(self):
        self._make("pyproject.toml",
                    '[tool.dotted-path]\nroot = "."\nskip_fixtures = true\n')
        target = self._make("mod.py")
        _, config = dotted_path.resolve_project_root(target.resolve(), self.root.resolve())
        self.assertTrue(config["skip_fixtures"])

    def test_skip_fixtures_default_false(self):
        target = self._make("mod.py")
        _, config = dotted_path.resolve_project_root(target.resolve(), self.root.resolve())
        self.assertFalse(config["skip_fixtures"])



class TestComputeModulePath(unittest.TestCase):
    """Tests for file path → dotted module path conversion."""

    def test_normal_file(self):
        root = Path("/project/src")
        f = Path("/project/src/pkg/utils/helpers.py")
        self.assertEqual(dotted_path.compute_module_path(f, root), "pkg.utils.helpers")

    def test_init_file(self):
        root = Path("/project")
        f = Path("/project/pkg/__init__.py")
        self.assertEqual(dotted_path.compute_module_path(f, root), "pkg")

    def test_nested_init(self):
        root = Path("/project")
        f = Path("/project/pkg/sub/__init__.py")
        self.assertEqual(dotted_path.compute_module_path(f, root), "pkg.sub")

    def test_file_outside_root(self):
        root = Path("/project")
        f = Path("/other/script.py")
        self.assertEqual(dotted_path.compute_module_path(f, root), "script")

    def test_top_level_file(self):
        root = Path("/project")
        f = Path("/project/main.py")
        self.assertEqual(dotted_path.compute_module_path(f, root), "main")


class TestResolveScope(unittest.TestCase):
    """Tests for AST scope resolution."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write(self, code):
        p = Path(self.tmpdir) / "test.py"
        p.write_text(code, encoding="utf-8")
        return p

    def test_module_level(self):
        f = self._write("x = 1\ny = 2\n")
        self.assertEqual(dotted_path.resolve_scope(f, 1), [])

    def test_simple_function(self):
        f = self._write("def foo():\n    pass\n")
        self.assertEqual(dotted_path.resolve_scope(f, 2), ["foo"])

    def test_simple_class(self):
        f = self._write("class Foo:\n    x = 1\n")
        self.assertEqual(dotted_path.resolve_scope(f, 2), ["Foo"])

    def test_method(self):
        f = self._write("class Foo:\n    def bar(self):\n        pass\n")
        self.assertEqual(dotted_path.resolve_scope(f, 3), ["Foo", "bar"])

    def test_nested_class(self):
        code = "class Outer:\n    class Inner:\n        x = 1\n"
        f = self._write(code)
        self.assertEqual(dotted_path.resolve_scope(f, 3), ["Outer", "Inner"])

    def test_async_function(self):
        f = self._write("async def handler():\n    pass\n")
        self.assertEqual(dotted_path.resolve_scope(f, 2), ["handler"])

    def test_decorated_function(self):
        code = "@decorator\ndef foo():\n    pass\n"
        f = self._write(code)
        # Row 3 is inside foo's body
        self.assertEqual(dotted_path.resolve_scope(f, 3), ["foo"])
        # Row 1 is the decorator — outside the def
        self.assertEqual(dotted_path.resolve_scope(f, 1), [])

    def test_deeply_nested(self):
        code = (
            "class A:\n"
            "    class B:\n"
            "        def c(self):\n"
            "            pass\n"
        )
        f = self._write(code)
        self.assertEqual(dotted_path.resolve_scope(f, 4), ["A", "B", "c"])

    def test_cursor_on_def_line(self):
        f = self._write("def foo():\n    pass\n")
        self.assertEqual(dotted_path.resolve_scope(f, 1), ["foo"])

    def test_syntax_error(self):
        f = self._write("def foo(\n")
        with self.assertRaises(SystemExit):
            dotted_path.resolve_scope(f, 1)


class TestStripFixtures(unittest.TestCase):
    """Tests for fixture method stripping."""

    def test_strips_setUp(self):
        self.assertEqual(
            dotted_path.strip_fixtures(["TestFoo", "setUp"]),
            ["TestFoo"],
        )

    def test_strips_tearDown(self):
        self.assertEqual(
            dotted_path.strip_fixtures(["TestFoo", "tearDown"]),
            ["TestFoo"],
        )

    def test_strips_setUpClass(self):
        self.assertEqual(
            dotted_path.strip_fixtures(["TestFoo", "setUpClass"]),
            ["TestFoo"],
        )

    def test_strips_pytest_setup_method(self):
        self.assertEqual(
            dotted_path.strip_fixtures(["TestFoo", "setup_method"]),
            ["TestFoo"],
        )

    def test_keeps_test_method(self):
        self.assertEqual(
            dotted_path.strip_fixtures(["TestFoo", "test_bar"]),
            ["TestFoo", "test_bar"],
        )

    def test_keeps_non_test_class(self):
        """setUp in a non-Test class is not stripped."""
        self.assertEqual(
            dotted_path.strip_fixtures(["MyClass", "setUp"]),
            ["MyClass", "setUp"],
        )

    def test_keeps_module_level_fixture_name(self):
        """A top-level function named setUp is not stripped."""
        self.assertEqual(
            dotted_path.strip_fixtures(["setUp"]),
            ["setUp"],
        )

    def test_empty_chain(self):
        self.assertEqual(dotted_path.strip_fixtures([]), [])


class TestEndToEnd(unittest.TestCase):
    """End-to-end tests running the script as a subprocess."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.script = Path(__file__).resolve().parent.parent / "dotted_path.py"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _make(self, rel_path, content=""):
        p = self.root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def _run(self, file_path, row):
        env = {
            "PATH": os.environ.get("PATH", ""),
            "DISPLAY": os.environ.get("DISPLAY", ""),
            "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY", ""),
            "ZED_FILE": str(file_path),
            "ZED_ROW": str(row),
            "ZED_WORKTREE_ROOT": str(self.root),
        }
        result = subprocess.run(
            [sys.executable, str(self.script)],
            capture_output=True, text=True, env=env,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    def test_class_method(self):
        self._make("pkg/__init__.py")
        f = self._make("pkg/utils.py",
                       "class MyClass:\n    def my_method(self):\n        pass\n")
        rc, out, _ = self._run(f, 3)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "pkg.utils.MyClass.my_method")

    def test_module_level(self):
        self._make("pkg/__init__.py")
        f = self._make("pkg/utils.py", "x = 1\n")
        rc, out, _ = self._run(f, 1)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "pkg.utils")

    def test_init_file_with_class(self):
        f = self._make("pkg/__init__.py", "class Outer:\n    class Inner:\n        pass\n")
        rc, out, _ = self._run(f, 3)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "pkg.Outer.Inner")

    def test_pyproject_src_layout(self):
        self._make("pyproject.toml", '[tool.dotted-path]\nroot = "src"\n')
        self._make("src/mylib/__init__.py")
        f = self._make("src/mylib/core.py",
                       "def process():\n    pass\n")
        rc, out, _ = self._run(f, 2)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "mylib.core.process")

    def test_django_layout(self):
        self._make("manage.py")
        self._make("myapp/__init__.py")
        f = self._make("myapp/views.py",
                       "class UserView:\n    def get(self):\n        pass\n")
        rc, out, _ = self._run(f, 3)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "myapp.views.UserView.get")

    def test_unparseable_file(self):
        f = self._make("bad.py", "def broken(\n")
        rc, _, err = self._run(f, 1)
        self.assertEqual(rc, 1)
        self.assertIn("cannot parse", err)

    def test_skip_fixtures_strips_setUp(self):
        self._make("pyproject.toml", '[tool.dotted-path]\nskip_fixtures = true\n')
        self._make("tests/__init__.py")
        f = self._make("tests/test_views.py",
                       "class TestUser:\n    def setUp(self):\n        pass\n")
        rc, out, _ = self._run(f, 3)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "tests.test_views.TestUser")

    def test_skip_fixtures_keeps_test_method(self):
        self._make("pyproject.toml", '[tool.dotted-path]\nskip_fixtures = true\n')
        self._make("tests/__init__.py")
        f = self._make("tests/test_views.py",
                       "class TestUser:\n    def test_get(self):\n        pass\n")
        rc, out, _ = self._run(f, 3)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "tests.test_views.TestUser.test_get")

    def test_no_skip_fixtures_keeps_setUp(self):
        self._make("tests/__init__.py")
        f = self._make("tests/test_views.py",
                       "class TestUser:\n    def setUp(self):\n        pass\n")
        rc, out, _ = self._run(f, 3)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "tests.test_views.TestUser.setUp")


if __name__ == "__main__":
    unittest.main()
