from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"
SOLUTIONS_DIR = ROOT / "solutions"


def _load_file(path):
    spec = spec_from_file_location(path.stem, path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_student_examples_are_importable_but_not_solved_yet():
    for path in sorted(EXAMPLES_DIR.glob("[0-9][0-9]_*.py")):
        module = _load_file(path)

        assert module.world.run() is False


def test_solutions_match_target_world_configuration():
    for path in sorted(SOLUTIONS_DIR.glob("[0-9][0-9]_*.py")):
        module = _load_file(path)

        assert module.world.run() is True
