# Performance follow-up, 2026-11-13

Baseline: `bf230e1` (including the recent large-world and moving-camera optimizations).

## Changes

- Clear cached collision detections after geometry/costume changes, collision-mode changes, and camera cache resets (including actor addition/removal). Subsequent handlers observe mutations made by earlier callbacks; handlers can still share results while the scene is unchanged.
- Clear cached rotations on transformation dirty signals. A surface can change its pixels without changing its identity; callers modifying a source surface must mark the appearance dirty.
- Batch intermediate background presentation during world updates. The final repaint flushes full background changes, including for docked worlds. Initial setup and reset retain immediate presentation. Restore batching state after exceptions.
- Suppress recursive background presentation during repaint after initial setup.
- Mark only current/recently visible dynamic actors dirty after a static-layer rebuild.
- Sort spatial candidates by cached pygame draw rank instead of scanning every world actor for every static-layer rebuild. Invalidate ranks on group membership and layer-order changes, including changes within the same layer.
- Compute occupied chunks directly from the tile footprint rather than visiting every tile.
- Skip index/visibility work for unchanged positions, retaining `last_position` semantics.

## Measurements

Scenario: `test/performance/profile_tiled_many_actors.py`, 800 moving enemies,
100 x 75 tiles, 25 x 20 camera, 120 simulation frames (119 timing samples).
Docker image: `pygame-tests`, Python 3.12.16, pygame-ce 2.5.8, dummy video/audio.
The comparison used isolated source snapshots so concurrent unrelated HexWorld edits were excluded.

Repaint calls: **384 -> 158 (-58.9%)**, including setup overhead.
The full-scene actor iteration in static candidate selection is now performed only when draw ranks need rebuilding, rather than on each camera movement.

Three alternating runs without cProfile, mean milliseconds per frame:

| Run | Baseline wall time | Changed wall time | Baseline process CPU | Changed process CPU |
| --- | ---: | ---: | ---: | ---: |
| 1 | 27.9532 | 26.0149 | 64.7140 | 46.8581 |
| 2 | 34.2543 | 51.8744 | 63.6181 | 60.0736 |
| 3 | 60.3716 | 66.8052 | 66.6114 | 66.0529 |

Wall-time runs and process-CPU runs are separate experiments. Process-CPU runs
exclude sleep/descheduling via `time.process_time`; other validation work was
running during the CPU experiment. Wall-time runs had no concurrent tests from
this task, but host load was uncontrolled. Their spread is substantial and
wall-time results do **not** demonstrate a reliable speedup. Median CPU means
were 64.7140 -> 60.0736 ms (-7.2%), also with substantial variation. Treat the
reduced rendering calls as the reproducible result, not a guaranteed FPS gain.

## Regression coverage

Collision callback movement, partner removal, collision-mode changes, unchanged-scene
cache reuse, in-place image mutation with a dirty signal, candidate ordering after
membership/layer mutations, chunk footprints crossing boundaries, batched rendering,
and reset/exception handling. Existing screenshot references are preserved.

Final validation: `venv/bin/invoke tests.cached` completed with **1233 passed**,
**67 subtests passed**, 10 warnings, no failures (104.98 s). This includes unit,
visual and physics integration tests. No screenshot baselines were changed.
`git diff --check` also passed.
