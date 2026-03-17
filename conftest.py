import os
from pathlib import Path
import sys
import warnings

import pytest


ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = ROOT / "source"
PHYSICS_SOURCE_ROOT = ROOT / "physics" / "source"
PHYSICS_TEST_ROOT = ROOT / "physics" / "test"

for import_root in [SOURCE_ROOT, PHYSICS_SOURCE_ROOT]:
    import_root_str = str(import_root)
    if import_root.exists() and import_root_str not in sys.path:
        sys.path.insert(0, import_root_str)


def pytest_configure(config):
    print("Setup vor allen Tests wird ausgeführt.")
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ["MINIWORLDS_TEST_FAST"] = "1"
    warnings.filterwarnings(
        "ignore",
        message=r".*\.run\(\) was not found in your code.*",
        category=UserWarning,
        module=r"miniworlds\.base\.app",
    )


def pytest_collection_modifyitems(items):
    for item in items:
        file_path = Path(str(item.fspath)).resolve()
        parts = file_path.parts
        if file_path.is_relative_to(PHYSICS_TEST_ROOT) or "visualtests" in parts:
            item.add_marker(pytest.mark.visual)
        elif "unittests" in parts:
            item.add_marker(pytest.mark.unit)