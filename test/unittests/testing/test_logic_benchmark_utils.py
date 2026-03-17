import cProfile
import tempfile
import unittest
from pathlib import Path

from test.performance import logic_benchmark_utils as utils


class TestLogicBenchmarkUtils(unittest.TestCase):
    def test_record_benchmark_result_writes_latest_history_and_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)

            first = utils.record_benchmark_result(
                "event dispatch",
                {"avg_ms": 12.5, "p95_ms": 18.0, "frames": 120},
                summary_type="frame_timing",
                base_dir=base_dir,
            )
            second = utils.record_benchmark_result(
                "event dispatch",
                {"avg_ms": 10.0, "p95_ms": 15.0, "frames": 120},
                summary_type="frame_timing",
                base_dir=base_dir,
            )

            benchmark_dir = base_dir / "results" / "benchmarks" / "event-dispatch"
            latest_json = benchmark_dir / "latest.json"
            history_md = benchmark_dir / "history.md"
            index_md = base_dir / "results" / "index.md"

            self.assertEqual(first["slug"], "event-dispatch")
            self.assertEqual(second["delta_to_previous"]["avg_ms"], -2.5)
            self.assertTrue(latest_json.exists())
            self.assertTrue(history_md.exists())
            self.assertTrue(index_md.exists())
            self.assertIn("avg_ms=-2.50", history_md.read_text(encoding="utf-8"))
            self.assertIn("event dispatch", index_md.read_text(encoding="utf-8"))

    def test_write_profile_stores_output_in_structured_profile_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_base_dir = utils.BASE_DIR
            original_results_dir = utils.RESULTS_DIR
            try:
                utils.BASE_DIR = Path(temp_dir)
                utils.RESULTS_DIR = utils.BASE_DIR / "results"
                profiler = cProfile.Profile()

                filename = utils.write_profile(profiler, "blockable_movement")

                self.assertTrue(filename.exists())
                self.assertEqual(filename.parent.name, "blockable-movement")
                self.assertEqual(filename.parent.parent.name, "profiles")
                self.assertTrue((utils.BASE_DIR / "results" / "profiles" / "index.md").exists())
            finally:
                utils.BASE_DIR = original_base_dir
                utils.RESULTS_DIR = original_results_dir


if __name__ == "__main__":
    unittest.main()