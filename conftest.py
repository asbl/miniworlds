import os
from pathlib import Path
import sys
import warnings

import pytest


ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = ROOT / "source"
PHYSICS_SOURCE_ROOT = ROOT / "physics" / "source"
PHYSICS_TEST_ROOT = ROOT / "physics" / "test"
DOC_EXAMPLE_TEST_ROOT = ROOT / "test" / "generated" / "docs_examples"
DOCKER_MARKER = Path("/.dockerenv")

for import_root in [SOURCE_ROOT, PHYSICS_SOURCE_ROOT]:
    import_root_str = str(import_root)
    if import_root.exists() and import_root_str not in sys.path:
        sys.path.insert(0, import_root_str)


def pytest_configure(config):
    docker_invoke_run = (
        os.environ.get("MINIWORLDS_TESTS_IN_DOCKER") == "1"
        and DOCKER_MARKER.exists()
    )
    allow_local_override = os.environ.get("MINIWORLDS_ALLOW_LOCAL_TESTS") == "1"

    if not docker_invoke_run and not allow_local_override:
        pytest.exit(
            "Run tests through the Docker-backed invoke tasks, for example "
            "`invoke tests.cached`, `invoke tests.visual`, or "
            "`invoke docs.test-examples`. Local pytest runs are blocked "
            "because results can differ between operating systems.",
            returncode=2,
        )
    if allow_local_override:
        warnings.warn(
            "Running tests outside the Docker-backed invoke tasks. Results can "
            "differ between operating systems; use this only for local debugging.",
            RuntimeWarning,
        )
    print("Setup vor allen Tests wird ausgeführt.")
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ["MINIWORLDS_TEST_FAST"] = "1"
    warnings.filterwarnings(
        "ignore",
        message=r".*\.run\(\) was not found in your code.*",
        category=UserWarning,
        module=r"miniworlds\.base\.app",
    )


def pytest_ignore_collect(collection_path, config):
    path = Path(collection_path).resolve()
    if (
        path.is_relative_to(DOC_EXAMPLE_TEST_ROOT)
        and os.environ.get("MINIWORLDS_INCLUDE_DOC_EXAMPLES") != "1"
    ):
        return True
    return None


def pytest_collection_modifyitems(items):
    for item in items:
        file_path = Path(str(item.fspath)).resolve()
        parts = file_path.parts
        if file_path.is_relative_to(PHYSICS_TEST_ROOT) or "visualtests" in parts:
            item.add_marker(pytest.mark.visual)
        elif "unittests" in parts:
            item.add_marker(pytest.mark.unit)
