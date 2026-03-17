# Miniworlds Workspace Instructions

## Project goals

- miniworlds is an educational library for students who should be able to write 2D programs with as little friction as possible.
- The public API is intentionally more intuitive than strictly "best practice" in some places. Preserve that tradeoff unless a change is explicitly requested.
- The project should stay compatible with pygame-ce today and should remain workable for a later Pyodide or browser-based runtime.

## Change priorities

- Do not introduce fundamental public API changes unless explicitly asked.
- Prefer internal refactorings over user-facing redesigns.
- When a tradeoff exists, prioritize student-facing clarity and low ceremony over architectural purity.
- Keep behavior stable for examples, tutorials, and visual tests.

## Implementation guidance

- Prefer small, focused changes that improve determinism, testability, and maintainability without changing user code.
- Favor internal improvements in lifecycle handling, event dispatching, state management, and platform abstraction.
- Avoid adding new hard desktop-only assumptions in core logic.
- Isolate file system, audio, display, and runtime-specific behavior where practical so web support remains possible.
- Preserve existing naming and default behavior when refactoring internals.
- Use type hints in new or changed Python code whenever practical.
- Add brief comments for non-obvious logic where they improve readability, but avoid redundant commentary.
- When public API docstrings or comments are surfaced through the Sphinx documentation, update the corresponding German translations under `docs/source/locales/de/` as part of the same change when practical.

## Validation

- Always validate changes with the Docker-based test path defined in tasks.py.
- Preferred command: `invoke run_tests`.
- If `invoke` is unavailable, run the equivalent Docker build and container test commands from tasks.py.
- Focused unit tests are grouped under `test/unittests/<domain>/`; prefer keeping new unit coverage in the matching domain folder instead of the old flat layout.
- Rendering and behavior changes are expected to keep the visual test suite green unless the change is explicitly intended to alter output.

## Review guidance

- Prefer recommendations that improve internal architecture without making the library harder for students to use.
- Treat educational ergonomics as a core requirement, not as secondary polish.
- Do not treat large line counts in `Actor` and `World` as an issue by itself. Their public method surface is intentionally broad for student-facing ergonomics.
- When reviewing `Actor` and `World`, prioritize internal cohesion, coupling to managers/connectors, hot-path performance, determinism, and test coverage over raw file length.