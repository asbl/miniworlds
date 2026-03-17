import tempfile
import time
from pathlib import Path

from miniworlds.base.app import App
from miniworlds.base.manager.app_file_manager import FileManager
from logic_benchmark_utils import record_measurement_summary


def profile_resource_lookup(iterations: int = 50000):
    App.reset()
    with tempfile.TemporaryDirectory() as temp_dir:
        image_dir = Path(temp_dir) / "images"
        image_dir.mkdir(parents=True, exist_ok=True)
        (image_dir / "ship.png").write_bytes(b"png")

        App._state.set_path(temp_dir)
        App._sync_class_state()

        start = time.perf_counter()
        for _ in range(iterations):
            FileManager.get_path_with_file_ending("ship", ["png"])
        elapsed = time.perf_counter() - start

    App.reset()
    print(
        f"resource lookup: {iterations} lookups in {elapsed * 1000:.2f} ms "
        f"({iterations / elapsed:.0f} lookups/s)"
    )
    record_measurement_summary(
        "resource lookup",
        {
            "iterations": iterations,
            "lookup_ms": round(elapsed * 1000, 4),
            "lookups_per_s": round(iterations / elapsed, 4),
        },
    )


if __name__ == "__main__":
    profile_resource_lookup()