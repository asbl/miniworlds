# Performance Benchmarks

Benchmark scripts live in this directory.

Generated results are written to `results/`:

- `results/index.md`: overview of the latest values and deltas per benchmark
- `results/benchmarks/<name>/latest.md`: latest run for one benchmark
- `results/benchmarks/<name>/history.md`: historical values for one benchmark
- `results/profiles/index.md`: latest cProfile artifacts

Legacy flat `.txt` artifacts were moved to `legacy/`.

Useful tasks from `tasks.py`:

- `invoke list-benchmarks`: show benchmark groups and names
- `invoke run-benchmarks`: run the default `quick` benchmark group
- `invoke run-benchmarks --selection=world`: run a full benchmark group
- `invoke run-benchmarks --selection=blockable_movement_cprofile`: run one benchmark
- `invoke profile-hotspots`: run the full benchmark suite
