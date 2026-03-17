import imgcompare # type: ignore
import os
from pathlib import Path
import shutil
import tempfile


class ScreenshotTester:
    def __init__(self, test_frames, quit_frame, unittest):
        self.test_frames = test_frames
        self.quit_frame = quit_frame
        self.unittest = unittest
        self.test_frame = 0
        self.world = None  # Set in setup
        self.base_path = Path(__file__).resolve().parent
        self.diff_threshold = 0.05

    def _get_test_title(self):
        return getattr(self.unittest, "SCREENSHOT_TITLE", self.unittest.__class__.__name__)

    def _should_generate_missing_baselines(self):
        return os.environ.get("MINIWORLDS_GENERATE_BASELINES") == "1"

    def setup(self, world):
        self.world = world
        self.world.test_title = self._get_test_title()
        self.world.tester = self

        @world.register
        def on_setup(self):
            self.init_test()

        @world.register
        def act(self):
            self.test()
            if hasattr(self, "act_test"):
                self.act_test()

        self.unittest.world = world

        @world.register
        def init_test(self):
            world.test_frame = 0

        @world.register
        def test(self):
            self.tester.test_frame = self.tester.test_frame + 1
            self.tester.screenshot_test(
                self.tester.test_frame,
                self.tester.quit_frame,
                self.tester.test_frames,
                self.test_title,
                self.tester,
            )
            
        @world.register
        def attach_world(self, world2):
            world2.tester = self.tester
            world2.test_title = self.test_title
            
            @world2.register
            def test(self):
                self.tester.test_frame = self.tester.test_frame + 1
                self.tester.screenshot_test(
                    self.tester.test_frame,
                    self.tester.quit_frame,
                    self.tester.test_frames,
                    self.test_title,
                    self.tester,
                )

    def diff(self, ia, ib):
        percentage = imgcompare.image_diff_percent(ia, ib)
        return percentage

    def compare_files(self, file_test, file_output):
        d = self.diff(file_test, file_output)
        assert 0 <= d <= self.diff_threshold, (
            f"Screenshot diff {d:.4f} exceeds threshold {self.diff_threshold:.4f}"
        )

    def _get_paths(self, test_title, frame):
        file_test = self.base_path / "testfiles" / f"{test_title}_testfile_{frame}.png"
        file_output = self.base_path / "outputfiles" / f"{test_title}_tmp_outputfile{frame}.png"
        return file_test, file_output

    def _capture_frame(self, target_path: Path):
        self.world.screenshot(os.fspath(target_path))

    def _capture_temp_frame(self, test_title, frame):
        with tempfile.NamedTemporaryFile(
            prefix=f"{test_title}_{frame}_",
            suffix=".png",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
        self._capture_frame(temp_path)
        return temp_path

    def screenshot(self, frame, test_frames, test_title):
        if frame not in test_frames:
            return False
        file_test, file_output = self._get_paths(test_title, frame)
        temp_reference = None
        if file_test.is_file():
            reference_path = file_test
        elif self._should_generate_missing_baselines():
            temp_output = self._capture_temp_frame(test_title, frame)
            try:
                file_test.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(temp_output, file_test)
            finally:
                if temp_output.is_file():
                    temp_output.unlink()
            return True
        else:
            temp_reference = self._capture_temp_frame(f"{test_title}_reference", frame)
            reference_path = temp_reference

        temp_output = self._capture_temp_frame(test_title, frame)
        try:
            self.compare_files(os.fspath(reference_path), os.fspath(temp_output))
        except AssertionError:
            file_output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(temp_output, file_output)
            raise
        finally:
            if temp_output.is_file():
                temp_output.unlink()
            if temp_reference and temp_reference.is_file():
                temp_reference.unlink()
        return True

    def check_quit(
        self,
        frame,
    ):
        if frame > self.quit_frame:
            self.world.quit()

    def screenshot_test(self, frame, quit_frame, test_frames, test_title, test):
        self.screenshot(frame, test_frames, test_title)
        self.check_quit(frame)
