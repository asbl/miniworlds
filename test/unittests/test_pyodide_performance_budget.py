"""Keep the CI performance gate from silently accepting incomplete results."""

import importlib.util
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.unit
spec = importlib.util.spec_from_file_location(
    "pyodide_runner", Path(__file__).parents[1] / "pyodidetests" / "run.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.fixture
def budget(tmp_path, monkeypatch):
    path = tmp_path / "budget.json"
    path.write_text(json.dumps({"headroom": 6, "budgets": {"frames": 0.5}}))
    monkeypatch.setattr(runner, "BUDGET_FILE", path)
    return path


def measurements(**overrides):
    return [
        {"name": runner.CALIBRATION, "elapsed_ms": 100},
        {"name": "frames", "elapsed_ms": 200, "avg_ms": 20, **overrides},
    ]


def test_budget_uses_average_frame_cost(budget):
    assert runner.check_budget(measurements()) == 0
    assert runner.check_budget(measurements(avg_ms=60)) == 1


def test_missing_and_unbudgeted_measurements_fail(budget):
    assert runner.check_budget(measurements()[:1]) == 1
    assert runner.check_budget(measurements(name="new benchmark")) == 1


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_invalid_calibration_is_rejected(value):
    items = measurements()
    items[0]["elapsed_ms"] = value
    with pytest.raises(RuntimeError, match="calibration"):
        runner._ratios(items)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_invalid_measurement_is_rejected(value):
    with pytest.raises(RuntimeError, match="Invalid performance measurement"):
        runner._ratios(measurements(avg_ms=value))


def test_duplicate_measurements_are_rejected():
    items = measurements()
    with pytest.raises(RuntimeError, match="duplicate"):
        runner._ratios(items + items[1:])


def test_write_budget_applies_headroom(budget):
    runner.write_budget(measurements())
    assert json.loads(budget.read_text())["budgets"] == {"frames": 1.2}


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_invalid_budget_is_rejected(budget, value):
    budget.write_text(json.dumps({"budgets": {"frames": value}}))
    assert runner.check_budget(measurements()) == 1
