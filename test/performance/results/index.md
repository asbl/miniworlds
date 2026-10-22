# Performance Results

Open the per-benchmark `latest.md` or `history.md` files for detailed changes.

| Benchmark | Last Run | Summary | Delta | Directory |
| --- | --- | --- | --- | --- |
| actor lifecycle | 2026-10-22T04:34:00 | actors=1000, creation_ms=235.51, creations_per_s=4246.12, removal_ms=66.69 | - | benchmarks/actor-lifecycle |
| actor logic collisions | 2026-03-16T22:15:30 | avg_ms=68.99, p95_ms=88.44, max_ms=136.19 | avg_ms=+37.66, p95_ms=+50.43, max_ms=+82.53 | benchmarks/actor-logic-collisions |
| actor logic filters | 2026-03-16T22:15:38 | avg_ms=53.01, p95_ms=75.68, max_ms=84.19 | avg_ms=+30.79, p95_ms=+49.53, max_ms=+54.15 | benchmarks/actor-logic-filters |
| actor logic filters cprofile | 2026-10-22T04:34:13 | avg_ms=68.22, p95_ms=88.16, max_ms=111.41 | - | benchmarks/actor-logic-filters-cprofile |
| actor logic mask collisions | 2026-03-16T22:04:32 | avg_ms=9.20, p95_ms=11.88, max_ms=12.31 | - | benchmarks/actor-logic-mask-collisions |
| blockable movement | 2026-03-16T22:15:06 | avg_ms=10.04, p95_ms=11.80, max_ms=12.73 | avg_ms=-1.91, p95_ms=-6.99, max_ms=-9.54 | benchmarks/blockable-movement |
| blockable movement cprofile | 2026-10-22T04:34:20 | avg_ms=41.94, p95_ms=47.81, max_ms=57.74 | avg_ms=-71.50, p95_ms=-159.65, max_ms=-213.78 | benchmarks/blockable-movement-cprofile |
| blocking index | 2026-10-22T04:45:56 | avg_ms=4.98, p95_ms=7.61, max_ms=8.14 | avg_ms=+1.49, p95_ms=+3.75, max_ms=+2.12 | benchmarks/blocking-index |
| camera culling | 2026-03-16T22:15:44 | avg_ms=16.73, p95_ms=23.27, max_ms=35.78 | avg_ms=+7.68, p95_ms=+13.20, max_ms=+24.39 | benchmarks/camera-culling |
| collision communication | 2026-06-04T15:29:14 | avg_ms=37.45, p95_ms=43.60, max_ms=49.20 | avg_ms=+0.19, p95_ms=+0.94, max_ms=+4.58 | benchmarks/collision-communication |
| event dispatch | 2026-10-22T04:50:29 | hover_events_ms=380.53, hover_events_per_s=131395.75, iterations=50000, key_events_ms=196.73 | hover_events_ms=-500.11, hover_events_per_s=+74618.91, iterations=0.00 | benchmarks/event-dispatch |
| image costume sizes | 2026-03-16T22:04:35 | avg_ms=1.98, p95_ms=4.65, max_ms=5.15 | - | benchmarks/image-costume-sizes |
| method caller | 2026-10-22T04:32:50 | cache_hits=99999, cache_misses=1, first_pass_ms=152.62, iterations=50000 | cache_hits=0.00, cache_misses=0.00, first_pass_ms=+84.34 | benchmarks/method-caller |
| resource lookup | 2026-10-22T04:32:54 | iterations=50000, lookup_ms=117.83, lookups_per_s=424351.66 | iterations=0.00, lookup_ms=+56.04, lookups_per_s=-384855.79 | benchmarks/resource-lookup |
| static scene | 2026-10-22T04:33:44 | avg_ms=4.08, p95_ms=7.16, max_ms=9.85 | - | benchmarks/static-scene |
| world queries | 2026-10-22T04:33:57 | actors=384, iterations=20000, pixel_hits=20000, pixel_queries_ms=170.75 | - | benchmarks/world-queries |
