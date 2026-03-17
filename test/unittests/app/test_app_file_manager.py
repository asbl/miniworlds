import os
import tempfile
import unittest
from pathlib import Path

from miniworlds.base.app import App
from miniworlds.base.manager.app_file_manager import FileManager


class TestAppFileManager(unittest.TestCase):
    def setUp(self):
        App.reset()

    def tearDown(self):
        App.reset()

    def test_get_path_with_file_ending_resolves_relative_image_from_app_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_dir = Path(temp_dir) / "images"
            image_dir.mkdir(parents=True, exist_ok=True)
            image_path = image_dir / "ship.png"
            image_path.write_bytes(b"png")

            App._state.set_path(temp_dir)
            App._sync_class_state()

            resolved_path = FileManager.get_path_with_file_ending("ship", ["png"])

            self.assertEqual(resolved_path, os.fspath(image_path))

    def test_get_image_path_returns_path_for_existing_absolute_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "player.png"
            image_path.write_bytes(b"png")

            resolved_path = FileManager.get_image_path(os.fspath(image_path))

            self.assertEqual(resolved_path, image_path)


if __name__ == "__main__":
    unittest.main()