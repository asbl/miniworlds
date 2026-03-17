import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from test.visualtests.screenshot_tester import ScreenshotTester


class DummyWorld:
    def screenshot(self, path):
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"png")


class NamedVisualTest:
    SCREENSHOT_TITLE = "StableVisualTitle"


class TestScreenshotTester(unittest.TestCase):
    def test_explicit_screenshot_title_overrides_class_name(self):
        tester = ScreenshotTester([1], 1, NamedVisualTest())

        self.assertEqual(tester._get_test_title(), "StableVisualTitle")

    def test_successful_compare_does_not_persist_output_artifact(self):
        tester = ScreenshotTester([1], 1, Mock())
        tester.world = DummyWorld()
        tester.diff = Mock(return_value=0.0)

        with tempfile.TemporaryDirectory() as temp_dir:
            tester.base_path = Path(temp_dir)
            file_test, file_output = tester._get_paths("TestDemo", 1)

            tester.screenshot(1, [1], "TestDemo")

            self.assertFalse(file_test.exists())
            self.assertFalse(file_output.exists())

    def test_successful_compare_keeps_existing_output_file_untouched(self):
        tester = ScreenshotTester([1], 1, Mock())
        tester.world = DummyWorld()
        tester.diff = Mock(return_value=0.0)

        with tempfile.TemporaryDirectory() as temp_dir:
            tester.base_path = Path(temp_dir)
            _, file_output = tester._get_paths("TestDemo", 1)
            file_output.parent.mkdir(parents=True, exist_ok=True)
            file_output.write_bytes(b"stale")

            tester.screenshot(1, [1], "TestDemo")

            self.assertEqual(file_output.read_bytes(), b"stale")

    def test_failed_compare_persists_output_artifact(self):
        tester = ScreenshotTester([1], 1, Mock())
        tester.world = DummyWorld()
        tester.diff = Mock(return_value=1.0)

        with tempfile.TemporaryDirectory() as temp_dir:
            tester.base_path = Path(temp_dir)
            _, file_output = tester._get_paths("TestDemo", 1)

            with self.assertRaises(AssertionError):
                tester.screenshot(1, [1], "TestDemo")

            self.assertTrue(file_output.exists())

    def test_missing_baseline_can_be_generated_when_enabled(self):
        tester = ScreenshotTester([1], 1, Mock())
        tester.world = DummyWorld()
        tester.diff = Mock(return_value=0.0)

        with tempfile.TemporaryDirectory() as temp_dir:
            tester.base_path = Path(temp_dir)
            file_test, file_output = tester._get_paths("TestDemo", 1)

            with patch.dict(os.environ, {"MINIWORLDS_GENERATE_BASELINES": "1"}, clear=False):
                tester.screenshot(1, [1], "TestDemo")

            self.assertTrue(file_test.exists())
            self.assertFalse(file_output.exists())


if __name__ == "__main__":
    unittest.main()