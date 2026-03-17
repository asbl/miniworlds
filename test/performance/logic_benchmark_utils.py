from __future__ import annotations

import json
import re
import statistics
import time
from datetime import datetime
from collections.abc import Mapping
from pathlib import Path
import cProfile
import pstats


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"


def slugify_benchmark_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "benchmark"


def _format_float(value: float) -> str:
    return f"{value:.2f}"


def _format_value(value) -> str:
    if isinstance(value, float):
        return _format_float(value)
    return str(value)


def _format_delta(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}"


def _benchmark_results_dir(base_dir: Path, name: str) -> Path:
    return base_dir / "results" / "benchmarks" / slugify_benchmark_name(name)


def _profiles_dir(base_dir: Path, stem: str) -> Path:
    return base_dir / "results" / "profiles" / slugify_benchmark_name(stem)


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_history_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _numeric_delta(previous_values: Mapping[str, int | float], current_values: Mapping[str, int | float]) -> dict[str, float]:
    delta = {}
    for key, value in current_values.items():
        previous = previous_values.get(key)
        if isinstance(previous, (int, float)) and isinstance(value, (int, float)):
            delta[key] = round(float(value) - float(previous), 4)
    return delta


def _build_frame_values(frame_times_ms: list[float], metrics: Mapping[str, int]) -> dict[str, int | float]:
    average = statistics.fmean(frame_times_ms)
    minimum = min(frame_times_ms)
    maximum = max(frame_times_ms)
    p95 = percentile(frame_times_ms, 0.95)
    p99 = percentile(frame_times_ms, 0.99)
    values: dict[str, int | float] = {
        "frames": len(frame_times_ms),
        "avg_ms": round(average, 4),
        "min_ms": round(minimum, 4),
        "p95_ms": round(p95, 4),
        "p99_ms": round(p99, 4),
        "max_ms": round(maximum, 4),
    }
    for key, value in sorted(metrics.items()):
        values[f"metric_{key}"] = value
    return values


def _measurement_summary_for_index(values: Mapping[str, int | float]) -> str:
    important_keys = [key for key in values.keys() if not key.startswith("metric_")][:4]
    return ", ".join(f"{key}={_format_value(values[key])}" for key in important_keys)


def _frame_summary_for_index(values: Mapping[str, int | float]) -> str:
    parts = []
    for key in ("avg_ms", "p95_ms", "max_ms"):
        if key in values:
            parts.append(f"{key}={_format_value(values[key])}")
    return ", ".join(parts)


def _delta_summary_for_index(delta: Mapping[str, float]) -> str:
    important_keys = [key for key in ("avg_ms", "p95_ms", "max_ms") if key in delta]
    if not important_keys:
        important_keys = list(delta.keys())[:3]
    if not important_keys:
        return "-"
    return ", ".join(f"{key}={_format_delta(delta[key])}" for key in important_keys)


def _write_history_markdown(path: Path, entries: list[dict]) -> None:
    if not entries:
        path.write_text("# Benchmark History\n", encoding="utf-8")
        return

    value_keys = sorted({key for entry in entries for key in entry["values"].keys()})
    header = ["recorded_at", *value_keys, "delta"]
    lines = [
        f"# {entries[-1]['name']}",
        "",
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for entry in entries:
        delta_summary = ", ".join(
            f"{key}={_format_delta(value)}" for key, value in sorted(entry.get("delta_to_previous", {}).items())
        ) or "-"
        row = [entry["recorded_at"]]
        row.extend(_format_value(entry["values"].get(key, "")) for key in value_keys)
        row.append(delta_summary)
        lines.append("| " + " | ".join(row) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_latest_markdown(path: Path, entry: dict) -> None:
    lines = [
        f"# {entry['name']}",
        "",
        f"Last run: {entry['recorded_at']}",
        f"Summary type: {entry['summary_type']}",
        "",
        "## Current Values",
    ]
    for key, value in sorted(entry["values"].items()):
        lines.append(f"- {key}: {_format_value(value)}")

    lines.append("")
    lines.append("## Delta To Previous Run")
    delta = entry.get("delta_to_previous", {})
    if delta:
        for key, value in sorted(delta.items()):
            lines.append(f"- {key}: {_format_delta(value)}")
    else:
        lines.append("- no previous run")

    lines.append("")
    lines.append("## Files")
    lines.append("- history.jsonl")
    lines.append("- history.md")
    lines.append("- latest.json")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_results_index(results_root: Path) -> None:
    benchmark_root = results_root / "benchmarks"
    benchmark_root.mkdir(parents=True, exist_ok=True)
    latest_entries = []
    for latest_file in sorted(benchmark_root.glob("*/latest.json")):
        latest_entries.append(json.loads(latest_file.read_text(encoding="utf-8")))

    lines = [
        "# Performance Results",
        "",
        "Open the per-benchmark `latest.md` or `history.md` files for detailed changes.",
        "",
        "| Benchmark | Last Run | Summary | Delta | Directory |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in sorted(latest_entries, key=lambda item: item["name"]):
        values = entry["values"]
        if entry["summary_type"] == "frame_timing":
            summary = _frame_summary_for_index(values)
        else:
            summary = _measurement_summary_for_index(values)
        delta = _delta_summary_for_index(entry.get("delta_to_previous", {}))
        directory = f"benchmarks/{entry['slug']}"
        lines.append(
            f"| {entry['name']} | {entry['recorded_at']} | {summary or '-'} | {delta} | {directory} |"
        )
    (results_root / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def record_benchmark_result(
    name: str,
    values: Mapping[str, int | float],
    *,
    summary_type: str,
    base_dir: Path = BASE_DIR,
) -> dict:
    benchmark_dir = _benchmark_results_dir(base_dir, name)
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    latest_path = benchmark_dir / "latest.json"
    history_path = benchmark_dir / "history.jsonl"
    previous_entry = _read_json(latest_path)
    previous_values = previous_entry["values"] if previous_entry else {}
    entry = {
        "name": name,
        "slug": slugify_benchmark_name(name),
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
        "summary_type": summary_type,
        "values": dict(sorted(values.items())),
        "delta_to_previous": _numeric_delta(previous_values, values),
    }

    _write_json(latest_path, entry)
    history_path.write_text(
        (history_path.read_text(encoding="utf-8") if history_path.exists() else "")
        + json.dumps(entry, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    entries = _read_history_entries(history_path)
    _write_history_markdown(benchmark_dir / "history.md", entries)
    _write_latest_markdown(benchmark_dir / "latest.md", entry)
    _write_results_index(base_dir / "results")
    return entry


def record_measurement_summary(
    name: str,
    values: Mapping[str, int | float],
    *,
    base_dir: Path = BASE_DIR,
) -> dict:
    entry = record_benchmark_result(
        name,
        values,
        summary_type="measurements",
        base_dir=base_dir,
    )
    print(f"{name}: results saved to {base_dir / 'results' / 'benchmarks' / entry['slug'] / 'latest.md'}")
    return entry


def configure_world(world) -> None:
    world.app.register_path(str(BASE_DIR))
    world.add_background("images/clouds.png")
    world.background.is_scaled = False


def record_frame_time(world) -> None:
    now = time.perf_counter()
    started_at = getattr(world, "_benchmark_frame_started_at", None)
    if started_at is not None:
        world.frame_times_ms.append((now - started_at) * 1000)
    world._benchmark_frame_started_at = now


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * fraction))
    return ordered[index]


def print_summary(name: str, frame_times_ms: list[float], metrics: Mapping[str, int]) -> None:
    if not frame_times_ms:
        print(f"{name}: no frame timings recorded")
        return

    values = _build_frame_values(frame_times_ms, metrics)
    print(
        f"{name}: frames={values['frames']} avg={_format_float(values['avg_ms'])} ms "
        f"min={_format_float(values['min_ms'])} ms p95={_format_float(values['p95_ms'])} ms "
        f"p99={_format_float(values['p99_ms'])} ms max={_format_float(values['max_ms'])} ms"
    )
    if metrics:
        metric_summary = " ".join(
            f"{key}={value}" for key, value in sorted(metrics.items())
        )
        print(f"{name}: metrics {metric_summary}")
    entry = record_benchmark_result(name, values, summary_type="frame_timing", base_dir=BASE_DIR)
    print(f"{name}: results saved to {BASE_DIR / 'results' / 'benchmarks' / entry['slug'] / 'latest.md'}")


def get_unique_profile_filename(stem: str, ext: str = "txt") -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    profile_dir = _profiles_dir(BASE_DIR, stem)
    profile_dir.mkdir(parents=True, exist_ok=True)
    return profile_dir / f"{timestamp}.{ext}"


def write_profile(profile: cProfile.Profile, stem: str) -> Path:
    filename = get_unique_profile_filename(stem)
    with open(filename, "w", encoding="utf-8") as handle:
        profile.create_stats()
        if not getattr(profile, "stats", None):
            handle.write("No profiling data recorded.\n")
        else:
            stats = pstats.Stats(profile, stream=handle)
            stats.sort_stats("time")
            stats.print_stats()
    profiles_root = BASE_DIR / "results" / "profiles"
    index_lines = [
        "# Profile Artifacts",
        "",
        "| Benchmark | Latest Profile |",
        "| --- | --- |",
    ]
    for profile_dir in sorted(path for path in profiles_root.iterdir() if path.is_dir()):
        latest_profile = sorted(profile_dir.glob("*.txt"))[-1]
        index_lines.append(f"| {profile_dir.name} | profiles/{profile_dir.name}/{latest_profile.name} |")
    (profiles_root / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    return filename