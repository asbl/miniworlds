# Performance Results

Open the per-benchmark `latest.md` or `history.md` files for detailed changes.

| Benchmark | Last Run | Summary | Delta | Directory |
| --- | --- | --- | --- | --- |
| actor logic collisions | 2026-03-16T22:15:30 | avg_ms=68.99, p95_ms=88.44, max_ms=136.19 | avg_ms=+37.66, p95_ms=+50.43, max_ms=+82.53 | benchmarks/actor-logic-collisions |
| actor logic filters | 2026-03-16T22:15:38 | avg_ms=53.01, p95_ms=75.68, max_ms=84.19 | avg_ms=+30.79, p95_ms=+49.53, max_ms=+54.15 | benchmarks/actor-logic-filters |
| actor logic mask collisions | 2026-03-16T22:04:32 | avg_ms=9.20, p95_ms=11.88, max_ms=12.31 | - | benchmarks/actor-logic-mask-collisions |
| blockable movement | 2026-03-16T22:15:06 | avg_ms=10.04, p95_ms=11.80, max_ms=12.73 | avg_ms=-1.91, p95_ms=-6.99, max_ms=-9.54 | benchmarks/blockable-movement |
| blockable movement cprofile | 2026-03-16T22:15:20 | avg_ms=113.44, p95_ms=207.46, max_ms=271.52 | avg_ms=+60.80, p95_ms=+140.42, max_ms=+180.45 | benchmarks/blockable-movement-cprofile |
| camera culling | 2026-03-16T22:15:44 | avg_ms=16.73, p95_ms=23.27, max_ms=35.78 | avg_ms=+7.68, p95_ms=+13.20, max_ms=+24.39 | benchmarks/camera-culling |
| event dispatch | 2026-03-16T19:30:07 | hover_events_ms=626.22, hover_events_per_s=79844.53, iterations=50000, key_events_ms=202.00 | - | benchmarks/event-dispatch |
| image costume sizes | 2026-03-16T22:04:35 | avg_ms=1.98, p95_ms=4.65, max_ms=5.15 | - | benchmarks/image-costume-sizes |
| method caller | 2026-03-16T19:30:51 | cache_hits=99999, cache_misses=1, first_pass_ms=88.76, iterations=50000 | cache_hits=0.00, cache_misses=0.00, first_pass_ms=-3.41 | benchmarks/method-caller |
| resource lookup | 2026-03-16T19:29:45 | iterations=50000, lookup_ms=78.77, lookups_per_s=634752.95 | - | benchmarks/resource-lookup |
