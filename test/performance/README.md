# Performance Benchmarks

Benchmark scripts live in this directory.

Generated results are written to `results/`:

- `results/index.md`: overview of the latest values and deltas per benchmark
- `results/benchmarks/<name>/latest.md`: latest run for one benchmark
- `results/benchmarks/<name>/history.md`: historical values for one benchmark
- `results/profiles/index.md`: latest cProfile artifacts

Legacy flat `.txt` artifacts were moved to `legacy/`.

Useful tasks from `tasks.py`:

- `invoke benchmarks.list`: show benchmark groups and names
- `invoke benchmarks.run`: run the default `quick` benchmark group
- `invoke benchmarks.run --selection=world`: run a full benchmark group
- `invoke benchmarks.run --selection=blockable_movement_cprofile`: run one benchmark
- `invoke benchmarks.hotspots`: run the full benchmark suite
