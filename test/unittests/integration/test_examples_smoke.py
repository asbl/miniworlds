from __future__ import annotations

import os
import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from miniworlds import App
from miniworlds.worlds.world import World
from test.unittests import REPO_ROOT, UNITTESTS_ROOT_FILE


class TestExamplesSmoke(unittest.TestCase):
    ROOT = REPO_ROOT

    EXAMPLE_SCRIPTS = [
        ROOT / "examples" / "processing" / "01.py",
        ROOT / "examples" / "objects_first" / "crazy_machines" / "crazy_machines.py",
        ROOT / "examples" / "objects_first" / "geometry_soccer" / "geometry_soccer.py",
        ROOT / "examples" / "classes_first" / "crazy_machines" / "crazy_machines.py",
    ]

    def setUp(self):
        App.reset(unittest=True, file=str(UNITTESTS_ROOT_FILE))

    def tearDown(self):
        App.reset(unittest=True, file=str(UNITTESTS_ROOT_FILE))

    def _cleanup_imports(self, script_dir: Path, existing_modules: dict[str, object]) -> None:
        script_dir = script_dir.resolve()
        for module_name, module in list(sys.modules.items()):
            if module_name in existing_modules:
                continue
            module_file = getattr(module, "__file__", None)
            if not module_file:
                continue
            try:
                if Path(module_file).resolve().is_relative_to(script_dir):
                    sys.modules.pop(module_name, None)
            except FileNotFoundError:
                continue

    def _run_example(self, script_path: Path) -> None:
        original_run = World.run
        observed_frames = []

        def smoke_run(world, *args, **kwargs):
            world.app._unittest = True

            @world.register
            def act(self):
                if self.frame >= 3:
                    self.quit()

            result = original_run(world, *args, **kwargs)
            observed_frames.append(world.frame)
            return result

        old_cwd = os.getcwd()
        old_path = list(sys.path)
        existing_modules = dict(sys.modules)
        script_dir = script_path.parent

        try:
            App.reset(unittest=True, file=os.fspath(script_path))
            os.chdir(script_dir)
            script_dir_str = os.fspath(script_dir)
            if script_dir_str not in sys.path:
                sys.path.insert(0, script_dir_str)

            with patch.object(App, "check_for_run_method", return_value=None):
                with patch.object(World, "run", smoke_run):
                    runpy.run_path(os.fspath(script_path), run_name="__main__")
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            self._cleanup_imports(script_dir, existing_modules)
            App.reset(unittest=True, file=str(UNITTESTS_ROOT_FILE))

        self.assertTrue(observed_frames)
        self.assertGreaterEqual(observed_frames[-1], 1)

    def test_examples_run_for_a_few_frames(self):
        for script_path in self.EXAMPLE_SCRIPTS:
            with self.subTest(example=os.fspath(script_path.relative_to(self.ROOT))):
                self._run_example(script_path)