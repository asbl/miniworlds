"""Invoke tasks grouped by workflow category.

Primary entry points:

- ``invoke tests.run`` for the full Docker-based test suite
- ``invoke benchmarks.run`` for benchmark groups or individual benchmarks
- ``invoke build.docs`` for a local Sphinx build
- ``invoke build.image`` for the Docker image used by tests and benchmarks
- ``invoke deploy.push`` for the normal branch push workflow with tests first
- ``invoke deploy.release --revision`` for the next release workflow

Release workflow summary:

1. Update the version in both packages.
2. Run the Docker test suite unless ``--skip-tests`` is used.
3. Commit and tag the physics repository.
4. Commit and tag the main repository.
5. Push branches and tags unless ``--no-push`` is used.

GitHub Actions handle publication after that push step:

- pushing the main repository branch ``main`` triggers docs deployment
- pushing ``v*`` tags triggers the PyPI publish workflows

``deploy.push`` uses the same Docker test gate before pushing branches or tags.

Legacy flat task names stay available as compatibility aliases while the
grouped interface becomes the documented surface.
"""

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from invoke import Collection, task
from invoke.exceptions import Exit

IMAGE = "pygame-tests"
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
VENV_PYTHON = os.path.join(REPO_ROOT, "venv", "bin", "python")
PHYSICS_REPO = os.path.join(REPO_ROOT, "physics")
MAIN_SETUP_PATH = os.path.join(REPO_ROOT, "source", "setup.py")
PHYSICS_SETUP_PATH = os.path.join(PHYSICS_REPO, "source", "setup.py")
VERSION_PATTERN = re.compile(r'version="([^"]+)"')
PERFORMANCE_RESULTS = Path(REPO_ROOT) / "test" / "performance" / "results"
DOC_EXAMPLE_TESTS = Path(REPO_ROOT) / "test" / "generated" / "docs_examples"

BENCHMARK_SCRIPTS = {
    "method_caller": "test/performance/profile_method_caller.py",
    "event_dispatch": "test/performance/profile_event_dispatch.py",
    "resource_lookup": "test/performance/profile_resource_lookup.py",
    "actor_logic_collisions": "test/performance/profile_actor_logic_collisions.py",
    "actor_logic_filters": "test/performance/profile_actor_logic_filters.py",
    "actor_logic_filters_cprofile": "test/performance/profile_actor_logic_filters_cprofile.py",
    "actor_logic_mask_collisions": "test/performance/profile_actor_logic_mask_collisions.py",
    "blockable_movement": "test/performance/profile_blockable_movement.py",
    "blockable_movement_cprofile": "test/performance/profile_blockable_movement_cprofile.py",
    "blocking_index": "test/performance/profile_blocking_index.py",
    "image_costume_sizes": "test/performance/profile_image_costume_sizes.py",
    "camera_culling": "test/performance/profile_camera_culling.py",
    "static_scene": "test/performance/profile_static_scene.py",
    "world_queries": "test/performance/profile_world_queries.py",
    "actor_lifecycle": "test/performance/profile_actor_lifecycle.py",
    "collision_communication": "test/performance/profile_collision_communication.py",
    "tiled_spatial_index": "test/performance/profile_tiled_world_spatial_index.py",
}

BENCHMARK_GROUPS = {
    "quick": [
        "method_caller",
        "event_dispatch",
        "resource_lookup",
    ],
    "world": [
        "actor_logic_collisions",
        "actor_logic_filters",
        "actor_logic_mask_collisions",
        "blockable_movement",
        "blocking_index",
        "image_costume_sizes",
        "camera_culling",
        "static_scene",
        "world_queries",
        "actor_lifecycle",
        "collision_communication",
        "tiled_spatial_index",
    ],
    "cprofile": [
        "actor_logic_filters_cprofile",
        "blockable_movement_cprofile",
    ],
}

BENCHMARK_GROUPS["all"] = [
    name
    for group_name in ("quick", "world", "cprofile")
    for name in BENCHMARK_GROUPS[group_name]
]


def _docker_mounts(results_dir: Path | None = None) -> str:
    mounts = (
        f"-v {REPO_ROOT}/pytest.ini:/app/pytest.ini "
        f"-v {REPO_ROOT}/conftest.py:/app/conftest.py "
        f"-v {REPO_ROOT}/tasks.py:/app/tasks.py "
        f"-v {REPO_ROOT}/source:/app/source "
        f"-v {REPO_ROOT}/test:/app/test "
        f"-v {REPO_ROOT}/examples:/app/examples "
        f"-v {REPO_ROOT}/physics/source:/app/physics/source "
        f"-v {REPO_ROOT}/physics/test:/app/physics/test "
    )
    if results_dir is not None:
        mounts += f"-v {results_dir}:/app/test/performance/results "
    return mounts


def _docker_pythonpath() -> str:
    return "PYTHONPATH=/app/source:/app/physics/source"


def _local_pythonpath() -> str:
    return f"{REPO_ROOT}/source:{REPO_ROOT}/physics/source"


def _local_env_prefix() -> str:
    return (
        f"PYTHONPATH={_local_pythonpath()} "
        "SDL_AUDIODRIVER=dummy "
        "MINIWORLDS_TEST_FAST=1"
    )


def _resolve_benchmark_scripts(selection: str) -> list[str]:
    if selection in BENCHMARK_GROUPS:
        return [BENCHMARK_SCRIPTS[name] for name in BENCHMARK_GROUPS[selection]]
    if selection in BENCHMARK_SCRIPTS:
        return [BENCHMARK_SCRIPTS[selection]]
    available = ", ".join(sorted({*BENCHMARK_GROUPS.keys(), *BENCHMARK_SCRIPTS.keys()}))
    raise ValueError(f"Unknown benchmark selection '{selection}'. Available: {available}")


def _validate_release_version(version: str) -> None:
    if not re.fullmatch(r"\d+(?:\.\d+)+", version):
        raise Exit(f"Invalid version '{version}'. Expected dotted numeric format like 3.5.0.1")


def _parse_release_version(version: str) -> list[int]:
    _validate_release_version(version)
    parts = [int(part) for part in version.split(".")]
    if len(parts) > 4:
        raise Exit(
            f"Invalid version '{version}'. Expected up to four numeric parts: major.minor.patch.revision"
        )
    while len(parts) < 4:
        parts.append(0)
    return parts


def _bump_release_version(current_version: str, level: str) -> str:
    indices = {
        "major": 0,
        "minor": 1,
        "patch": 2,
        "revision": 3,
    }
    if level not in indices:
        raise Exit(f"Unknown release level '{level}'")

    parts = _parse_release_version(current_version)
    index = indices[level]
    parts[index] += 1
    for reset_index in range(index + 1, len(parts)):
        parts[reset_index] = 0
    return ".".join(str(part) for part in parts)


def _resolve_release_version(
    current_version: str,
    version: str | None,
    major: bool,
    minor: bool,
    patch: bool,
    revision: bool,
) -> tuple[str, str]:
    selected_levels = [
        level
        for level, enabled in (
            ("major", major),
            ("minor", minor),
            ("patch", patch),
            ("revision", revision),
        )
        if enabled
    ]

    if version and selected_levels:
        raise Exit("Use either --version or exactly one of --major/--minor/--patch/--revision")
    if len(selected_levels) > 1:
        raise Exit("Choose only one of --major, --minor, --patch, or --revision")
    if version:
        _validate_release_version(version)
        return version, "explicit"
    if len(selected_levels) == 1:
        level = selected_levels[0]
        return _bump_release_version(current_version, level), level
    raise Exit("Provide --version or one of --major, --minor, --patch, or --revision")


def _read_version(file_path: str) -> str:
    with open(file_path, encoding="utf-8") as handle:
        content = handle.read()
    match = VERSION_PATTERN.search(content)
    if not match:
        raise Exit(f"Could not find a version string in {file_path}")
    return match.group(1)


def _write_version(file_path: str, version: str) -> None:
    with open(file_path, encoding="utf-8") as handle:
        content = handle.read()
    updated_content, replacements = VERSION_PATTERN.subn(f'version="{version}"', content, count=1)
    if replacements != 1:
        raise Exit(f"Could not update version in {file_path}")
    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write(updated_content)


def _git(c, repo_path: str, command: str, hide: bool = False):
    return c.run(f"git -C {repo_path} {command}", hide=hide)


def _git_stdout(c, repo_path: str, command: str) -> str:
    return _git(c, repo_path, command, hide=True).stdout.strip()


def _ensure_clean_repo(c, repo_path: str, name: str) -> None:
    status = _git_stdout(c, repo_path, "status --short")
    if status:
        raise Exit(f"{name} repository has uncommitted changes:\n{status}")


def _ensure_tag_missing(c, repo_path: str, tag_name: str, name: str) -> None:
    existing_tag = _git_stdout(c, repo_path, f"tag -l {tag_name}")
    if existing_tag:
        raise Exit(f"{name} repository already contains tag {tag_name}")


def _current_branch(c, repo_path: str, name: str) -> str:
    branch = _git_stdout(c, repo_path, "branch --show-current")
    if not branch:
        raise Exit(f"{name} repository is not on a named branch")
    return branch


def _repo_status(c, repo_path: str) -> str:
    return _git_stdout(c, repo_path, "status --short")


def _describe_workflow_automation(main_branch: str, push: bool, tags: bool = True) -> list[str]:
    if not push:
        return ["No GitHub workflow runs until branches and tags are pushed manually."]
    notes = []
    if main_branch == "main":
        notes.insert(
            0,
            "Pushing the main repository branch 'main' triggers .github/workflows/deploy-docs.yml, so docs are rebuilt and deployed automatically.",
        )
    else:
        notes.insert(
            0,
            "Docs deployment only runs from pushes to the main repository branch 'main'. "
            f"The current branch is '{main_branch}', so this release push will not deploy docs automatically.",
        )
    if tags:
        notes.append("Pushed v* tags trigger the PyPI publish workflows in both repositories.")
    else:
        notes.append("Without pushing tags, the PyPI publish workflows are not triggered.")
    return notes


def _push_repositories(c, main_branch: str, physics_branch: str, tags: bool) -> None:
    _git(c, PHYSICS_REPO, f"push origin {physics_branch}")
    _git(c, REPO_ROOT, f"push origin {main_branch}")
    if tags:
        _git(c, PHYSICS_REPO, "push --tags")
        _git(c, REPO_ROOT, "push --tags")


def _print_release_plan(
    version: str,
    release_mode: str,
    tag_name: str,
    main_branch: str,
    physics_branch: str,
    current_main_version: str,
    current_physics_version: str,
    main_status: str,
    physics_status: str,
    main_tag_exists: bool,
    physics_tag_exists: bool,
    skip_tests: bool,
    push: bool,
) -> None:
    print("Release dry-run summary")
    print(f"- Target version: {version}")
    print(f"- Version source: {release_mode}")
    print(f"- Target tag: {tag_name}")
    print(f"- Main branch: {main_branch}")
    print(f"- Physics branch: {physics_branch}")
    print(f"- Current main version: {current_main_version}")
    print(f"- Current physics version: {current_physics_version}")
    print(f"- Run tests: {'no' if skip_tests else 'yes'}")
    print(f"- Push branches and tags: {'yes' if push else 'no'}")
    print("Planned steps:")
    print("1. Update source/setup.py and physics/source/setup.py")
    if skip_tests:
        print("2. Skip Docker tests")
    else:
        print("2. Run invoke tests.run")
    print("3. Commit and tag the physics repository")
    print("4. Commit and tag the main repository")
    if push:
        print("5. Push both branches and tags")
    else:
        print("5. Skip pushes")
    print("Workflow automation after push:")
    for note in _describe_workflow_automation(main_branch, push, tags=True):
        print(f"- {note}")
    print("Checks:")
    print(f"- Main repo clean: {'yes' if not main_status else 'no'}")
    if main_status:
        print(main_status)
    print(f"- Physics repo clean: {'yes' if not physics_status else 'no'}")
    if physics_status:
        print(physics_status)
    print(f"- Main tag exists already: {'yes' if main_tag_exists else 'no'}")
    print(f"- Physics tag exists already: {'yes' if physics_tag_exists else 'no'}")
    print(
        "- Package versions already aligned: "
        f"{'yes' if current_main_version == current_physics_version else 'no'}"
    )


def _run_deploy_tests(c, skip_tests: bool) -> None:
    if not skip_tests:
        tests_run(c)


def ensure_test_environment(c):
    """Build the docker image if it does not exist yet."""
    c.run(f"docker image inspect {IMAGE} >/dev/null 2>&1 || docker build -t {IMAGE} .")

def build_test_environment(c):
    """Rebuild the Docker image used by tests and benchmarks."""
    c.run(f"docker build -t {IMAGE} .")


def ensure_local_environment(c):
    """Create/update the local venv through prepare.sh."""
    c.run("MINIWORLDS_PREPARE_SKIP_LIST=1 zsh -lc 'source prepare.sh'", pty=True)


def run_pytest_in_container(
    c,
    pytest_args: str,
    rebuild: bool = True,
    extra_env: dict[str, str] | None = None,
):
    """Run pytest inside the docker image against the live source tree."""
    if rebuild:
        build_test_environment(c)
    else:
        ensure_test_environment(c)
    uid = os.getuid()
    gid = os.getgid()
    extra_env_args = ""
    if extra_env:
        extra_env_args = " ".join(f"{key}={value}" for key, value in extra_env.items()) + " "
    c.run(
        f"docker run --rm "
        f"--user {uid}:{gid} "
        f"{_docker_mounts()}"
        f"{IMAGE} env "
        "SDL_AUDIODRIVER=dummy "
        "MINIWORLDS_TEST_FAST=1 "
        "MINIWORLDS_TESTS_IN_DOCKER=1 "
        f"{extra_env_args}"
        f"{_docker_pythonpath()} pytest {pytest_args}"
    )


def run_python_in_container(c, script_path: str, rebuild: bool = False):
    """Run a Python script inside the docker image against the live source tree."""
    if rebuild:
        build_test_environment(c)
    else:
        ensure_test_environment(c)
    uid = os.getuid()
    gid = os.getgid()
    c.run(
        f"docker run --rm "
        f"--user {uid}:{gid} "
        f"{_docker_mounts()}"
        f"{IMAGE} env "
        "SDL_AUDIODRIVER=dummy "
        "MINIWORLDS_TEST_FAST=1 "
        "MINIWORLDS_TESTS_IN_DOCKER=1 "
        f"{_docker_pythonpath()} python {script_path}"
    )


def run_python_scripts_in_container(
    c,
    script_paths: list[str],
    rebuild: bool = False,
    results_dir: Path | None = None,
):
    """Run multiple Python scripts sequentially in a single docker container."""
    if rebuild:
        build_test_environment(c)
    else:
        ensure_test_environment(c)
    uid = os.getuid()
    gid = os.getgid()
    commands = " && ".join(f"python {script_path}" for script_path in script_paths)
    c.run(
        f"docker run --rm "
        f"--user {uid}:{gid} "
        f"{_docker_mounts(results_dir)}"
        f"{IMAGE} sh -lc \"export SDL_AUDIODRIVER=dummy MINIWORLDS_TEST_FAST=1 {_docker_pythonpath()} && {commands}\""
    )


def _read_latest_benchmark_results(results_dir: Path) -> dict[str, dict]:
    latest_results = {}
    for latest_path in sorted((results_dir / "benchmarks").glob("*/latest.json")):
        entry = json.loads(latest_path.read_text(encoding="utf-8"))
        latest_results[entry["slug"]] = entry
    return latest_results


def _performance_metric_direction(key: str) -> int:
    if key.endswith("_per_s"):
        return 1
    if key.endswith("_ms"):
        return -1
    return 0


def _format_performance_comparison(
    historical: dict[str, dict],
    current: dict[str, dict],
    benchmark_names: list[str],
) -> str:
    lines = [
        "",
        "Performance comparison against historical latest results",
        "=" * 56,
        f"{'Benchmark / metric':42} {'Historical':>12} {'Current':>12} {'Change':>10}",
        "-" * 80,
    ]
    for benchmark_name in benchmark_names:
        slug = re.sub(r"[^a-z0-9]+", "-", benchmark_name.lower()).strip("-")
        old_entry = historical.get(slug)
        new_entry = current.get(slug)
        if old_entry is None or new_entry is None:
            lines.append(f"{benchmark_name:42} {'missing result':>36}")
            continue

        for key, new_value in new_entry["values"].items():
            direction = _performance_metric_direction(key)
            old_value = old_entry["values"].get(key)
            if (
                direction == 0
                or not isinstance(old_value, (int, float))
                or not isinstance(new_value, (int, float))
                or not old_value
            ):
                continue
            percent = (float(new_value) - float(old_value)) / float(old_value) * 100
            performance_change = percent * direction
            marker = (
                "faster"
                if performance_change > 0
                else "slower"
                if performance_change < 0
                else "same"
            )
            lines.append(
                f"{benchmark_name + ' / ' + key:42} "
                f"{old_value:12.2f} {new_value:12.2f} "
                f"{abs(performance_change):8.1f}% {marker}"
            )
    return "\n".join(lines)


@task(
    name="release",
    help={
        "version": "Release version, for example 3.5.0.1",
        "major": "Bump the major version and reset minor, patch, and revision to 0",
        "minor": "Bump the minor version and reset patch and revision to 0",
        "patch": "Bump the patch version and reset revision to 0",
        "revision": "Bump the revision version",
        "skip_tests": "Skip the Docker test run before committing and tagging",
        "push": "Push both repositories and tags after creating the release",
        "dry_run": "Show the planned release steps and blockers without changing anything",
    },
)
def deploy_release(
    c,
    version=None,
    major=False,
    minor=False,
    patch=False,
    revision=False,
    skip_tests=False,
    push=True,
    dry_run=False,
):
    """Create a synchronized miniworlds/miniworlds-physics release.

    Choose either an explicit ``--version`` or one bump flag from ``--major``,
    ``--minor``, ``--patch``, or ``--revision``. The task updates both package
    versions, runs Docker tests unless skipped, commits and tags the physics
    repository first, then the main repository. When pushes are enabled,
    GitHub Actions take over publication: pushed ``v*`` tags publish the
    packages and pushes to main deploy the docs.
    """
    main_branch = _current_branch(c, REPO_ROOT, "Main")
    physics_branch = _current_branch(c, PHYSICS_REPO, "Physics")

    current_main_version = _read_version(MAIN_SETUP_PATH)
    current_physics_version = _read_version(PHYSICS_SETUP_PATH)
    if current_main_version != current_physics_version:
        raise Exit(
            "Main and physics package versions differ before release: "
            f"{current_main_version} != {current_physics_version}"
        )

    version, release_mode = _resolve_release_version(
        current_main_version,
        version,
        major,
        minor,
        patch,
        revision,
    )
    tag_name = f"v{version}"

    main_status = _repo_status(c, REPO_ROOT)
    physics_status = _repo_status(c, PHYSICS_REPO)
    main_tag_exists = bool(_git_stdout(c, REPO_ROOT, f"tag -l {tag_name}"))
    physics_tag_exists = bool(_git_stdout(c, PHYSICS_REPO, f"tag -l {tag_name}"))

    if dry_run:
        _print_release_plan(
            version,
            release_mode,
            tag_name,
            main_branch,
            physics_branch,
            current_main_version,
            current_physics_version,
            main_status,
            physics_status,
            main_tag_exists,
            physics_tag_exists,
            skip_tests,
            push,
        )
        return

    _ensure_clean_repo(c, REPO_ROOT, "Main")
    _ensure_clean_repo(c, PHYSICS_REPO, "Physics")
    _ensure_tag_missing(c, REPO_ROOT, tag_name, "Main")
    _ensure_tag_missing(c, PHYSICS_REPO, tag_name, "Physics")

    _write_version(MAIN_SETUP_PATH, version)
    _write_version(PHYSICS_SETUP_PATH, version)

    try:
        _run_deploy_tests(c, skip_tests)
    except BaseException:
        _write_version(MAIN_SETUP_PATH, current_main_version)
        _write_version(PHYSICS_SETUP_PATH, current_physics_version)
        raise

    _git(c, PHYSICS_REPO, "add source/setup.py")
    _git(c, PHYSICS_REPO, f'commit -m "Bump version to {version}"')
    _git(c, PHYSICS_REPO, f'tag -a {tag_name} -m "Release {tag_name}"')

    _git(c, REPO_ROOT, "add source/setup.py physics")
    _git(c, REPO_ROOT, f'commit -m "Bump version to {version}"')
    _git(c, REPO_ROOT, f'tag -a {tag_name} -m "Release {tag_name}"')

    if push:
        for note in _describe_workflow_automation(main_branch, push=True, tags=True):
            print(f"Workflow note: {note}")
        _git(c, PHYSICS_REPO, f"push origin {tag_name}")
        _git(c, REPO_ROOT, f"push origin {tag_name}")
        _push_repositories(c, main_branch, physics_branch, tags=False)


@task(
    name="push",
    help={
        "tags": "Also push all local tags in both repositories",
        "skip_tests": "Skip the Docker test run before pushing",
        "dry_run": "Show the planned push steps and workflow effects without changing anything",
    },
)
def deploy_push(c, tags=False, skip_tests=False, dry_run=False):
    """Push the current main and physics branches, optionally including tags.

    This is the normal deploy step when you only want to push existing commits.
    If the main repository branch is ``main``, the docs workflow runs after the
    branch push. PyPI publication only happens when tags are pushed as well.
    A full Docker test run is performed before pushing unless ``--skip-tests``
    is passed.
    """
    main_branch = _current_branch(c, REPO_ROOT, "Main")
    physics_branch = _current_branch(c, PHYSICS_REPO, "Physics")

    print("Deploy push summary")
    print(f"- Main branch: {main_branch}")
    print(f"- Physics branch: {physics_branch}")
    print(f"- Push tags: {'yes' if tags else 'no'}")
    print(f"- Run tests: {'no' if skip_tests else 'yes'}")
    print("Workflow automation after push:")
    for note in _describe_workflow_automation(main_branch, push=True, tags=tags):
        print(f"- {note}")

    if dry_run:
        return

    _run_deploy_tests(c, skip_tests)
    _push_repositories(c, main_branch, physics_branch, tags=tags)

@task(name="run")
def tests_run(c):
    """Run the full test suite in Docker and rebuild the image first."""
    run_pytest_in_container(c, "-v")


@task(name="cached")
def tests_cached(c):
    """Run the full test suite against the current image without rebuilding it."""
    run_pytest_in_container(c, "-v", rebuild=False)


@task(name="unit")
def tests_unit(c):
    """Run only the fast unit tests in Docker."""
    run_pytest_in_container(c, "-m unit -v", rebuild=False)


@task(name="visual")
def tests_visual(c):
    """Run only the screenshot-based visual tests in Docker."""
    run_pytest_in_container(c, "-m visual -v", rebuild=False)


@task(name="pyodide")
def tests_pyodide(c):
    """Run core browser-runtime tests in Pyodide and headless Chromium in Docker."""
    run_python_in_container(c, "test/pyodidetests/run.py", rebuild=False)


@task(name="profile")
def tests_profile(c):
    """Show the slowest tests inside Docker without rebuilding the image."""
    run_pytest_in_container(c, "-q --durations=25", rebuild=False)


@task(name="physics")
def tests_physics(c):
    """Run the focused miniworlds_physics integration tests in Docker."""
    run_pytest_in_container(
        c,
        "test/unittests/physics/test_physics_integration.py -q",
        rebuild=False,
    )


@task(name="docs")
def tests_docs(c):
    """Generate documentation example tests and run them in Docker."""
    docs_generate_example_tests(c)
    run_pytest_in_container(
        c,
        "test/generated/docs_examples -q",
        rebuild=False,
        extra_env={"MINIWORLDS_INCLUDE_DOC_EXAMPLES": "1"},
    )


@task(name="list")
def benchmarks_list(c):
    """List benchmark groups and individual benchmark names."""
    del c
    print("Benchmark groups:")
    for group_name in sorted(BENCHMARK_GROUPS.keys()):
        print(f"- {group_name}: {', '.join(BENCHMARK_GROUPS[group_name])}")
    print("\nIndividual benchmarks:")
    for benchmark_name in sorted(BENCHMARK_SCRIPTS.keys()):
        print(f"- {benchmark_name}: {BENCHMARK_SCRIPTS[benchmark_name]}")


@task(
    name="run",
    help={
        "selection": "Benchmark group or individual benchmark name",
        "rebuild": "Rebuild the Docker image before running the benchmarks",
    },
)
def benchmarks_run(c, selection="quick", rebuild=False):
    """Run a benchmark group or one named benchmark inside Docker.

    Examples:
        invoke benchmarks.run
        invoke benchmarks.run --selection=world
        invoke benchmarks.run --selection=blockable_movement_cprofile
    """
    scripts = _resolve_benchmark_scripts(selection)
    run_python_scripts_in_container(c, scripts, rebuild=rebuild)


@task(name="hotspots")
def benchmarks_hotspots(c):
    """Run the full hotspot profiling suite inside Docker."""
    run_python_scripts_in_container(
        c,
        _resolve_benchmark_scripts("all"),
        rebuild=False,
    )


@task(name="pyodide")
def benchmarks_pyodide(c):
    """Run everyday performance benchmarks in Pyodide and headless Chromium."""
    c.run(f"{sys.executable} test/pyodidetests/run.py --performance")


@task(
    name="analyze",
    help={
        "selection": "Benchmark group or individual benchmark name",
        "rebuild": "Rebuild the Docker image before running the benchmarks",
    },
)
def benchmarks_analyze(c, selection="all", rebuild=False):
    """Run benchmarks in Docker and compare them with historical latest results."""
    scripts = _resolve_benchmark_scripts(selection)
    benchmark_names = [
        name for name, script in BENCHMARK_SCRIPTS.items() if script in scripts
    ]
    historical = _read_latest_benchmark_results(PERFORMANCE_RESULTS)

    with tempfile.TemporaryDirectory(prefix="miniworlds-performance-") as temp_dir:
        analysis_results = Path(temp_dir) / "results"
        shutil.copytree(PERFORMANCE_RESULTS, analysis_results)
        run_python_scripts_in_container(
            c,
            scripts,
            rebuild=rebuild,
            results_dir=analysis_results,
        )
        current = _read_latest_benchmark_results(analysis_results)

    print(_format_performance_comparison(historical, current, benchmark_names))


@task(
    name="single",
    help={
        "name": "Individual benchmark name",
        "rebuild": "Rebuild the Docker image before running the benchmark",
    },
)
def benchmarks_single(c, name, rebuild=False):
    """Run one benchmark by name inside Docker."""
    scripts = _resolve_benchmark_scripts(name)
    run_python_scripts_in_container(c, scripts, rebuild=rebuild)


@task(name="docs")
def docs_build(c):
    """Build the multilingual Sphinx documentation locally.

    Deployment is not handled here. After ``deploy.release`` pushes the main
    branch, ``.github/workflows/deploy-docs.yml`` rebuilds and deploys the docs
    automatically.
    """
    with c.cd("docs"):
        build_dir = "build"

        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        os.makedirs(build_dir, exist_ok=True)

        c.run("make gettext", pty=True)
        c.run("sphinx-intl update -p build/gettext -l en -l de", pty=True)
        c.run("sphinx-intl build", pty=True)
        c.run("sphinx-build -b html -D language=en source build/html/en", pty=True)
        c.run("sphinx-build -b html -D language=de source build/html/de", pty=True)


@task(name="examples")
def docs_generate_example_tests(c):
    """Generate pytest cases from Python code blocks in docs/source."""
    del c
    from test.docs.generate_doc_example_tests import generate_doc_example_tests

    examples, skipped = generate_doc_example_tests(DOC_EXAMPLE_TESTS)
    print(
        f"Generated {len(examples)} documentation example tests in {DOC_EXAMPLE_TESTS}; "
        f"skipped {len(skipped)} non-standalone snippets"
    )


@task(name="test-examples")
def docs_test_examples(c):
    """Generate and run pytest cases for documentation Python examples in Docker."""
    docs_generate_example_tests(c)
    run_pytest_in_container(
        c,
        "test/generated/docs_examples -q",
        rebuild=False,
        extra_env={"MINIWORLDS_INCLUDE_DOC_EXAMPLES": "1"},
    )


@task(name="image")
def build_image(c):
    """Rebuild the Docker image used by test and benchmark tasks."""
    build_test_environment(c)


@task(name="prepare")
def env_prepare(c):
    """Create/update the local venv via prepare.sh."""
    ensure_local_environment(c)


@task(name="check")
def env_check(c):
    """Verify the local venv and physics imports."""
    ensure_local_environment(c)
    c.run(
        f"{_local_env_prefix()} {VENV_PYTHON} - <<'PY'\n"
        "import sys\n"
        "import pygame\n"
        "import pymunk\n"
        "import miniworlds\n"
        "import miniworlds_physics\n"
        "print(sys.executable)\n"
        "print(f'pygame {pygame.__version__}')\n"
        "print('pymunk ok')\n"
        "print('miniworlds ok')\n"
        "print(f'miniworlds_physics exports {miniworlds_physics.__all__}')\n"
        "PY",
        pty=True,
    )


@task(name="shell")
def container_shell(c):
    """Start an interactive shell in the test Docker image."""
    c.run(f"docker run --rm -it {IMAGE} bash")


@task(name="cleanup")
def container_cleanup(c):
    """Remove unused Docker images and containers."""
    c.run("docker system prune -f")


@task(name="x11")
def container_x11(c):
    """Start the Docker image with X11 forwarding for graphical debugging."""
    c.run("xhost +local:root")
    c.run(
        f"docker run --rm -it "
        f"-e DISPLAY=$DISPLAY "
        f"-v /tmp/.X11-unix:/tmp/.X11-unix "
        f"{IMAGE} bash"
    )
    c.run("xhost -local:root")


@task(name="local")
def build_local(c):
    """Install the main package from source/ in editable mode."""
    c.run("cd source && pip install -e .")


@task(name="physics")
def build_physics(c):
    """Install the physics package from physics/source in editable mode."""
    c.run("cd physics/source && pip install -e .")


@task(name="checkout")
def examples_checkout(c):
    """Initialize and update the examples submodule recursively."""
    c.run("cd examples && git submodule update --init --recursive")


deploy = Collection("deploy")
deploy.add_task(deploy_release, default=True)
deploy.add_task(deploy_push)

tests = Collection("tests")
tests.add_task(tests_run, default=True)
tests.add_task(tests_cached)
tests.add_task(tests_unit)
tests.add_task(tests_visual)
tests.add_task(tests_pyodide)
tests.add_task(tests_profile)
tests.add_task(tests_physics)
tests.add_task(tests_docs)

benchmarks = Collection("benchmarks")
benchmarks.add_task(benchmarks_run, default=True)
benchmarks.add_task(benchmarks_list)
benchmarks.add_task(benchmarks_hotspots)
benchmarks.add_task(benchmarks_analyze)
benchmarks.add_task(benchmarks_pyodide)
benchmarks.add_task(benchmarks_single)

build = Collection("build")
build.add_task(build_local, default=True)
build.add_task(build_image)
build.add_task(docs_build)
build.add_task(build_physics)

env = Collection("env")
env.add_task(env_prepare, default=True)
env.add_task(env_check)

container = Collection("container")
container.add_task(container_shell, default=True)
container.add_task(container_cleanup)
container.add_task(container_x11)

examples = Collection("examples")
examples.add_task(examples_checkout, default=True)

docs = Collection("docs")
docs.add_task(docs_generate_example_tests, default=True)
docs.add_task(docs_test_examples)

ns = Collection()
ns.add_collection(deploy)
ns.add_collection(tests)
ns.add_collection(benchmarks)
ns.add_collection(build)
ns.add_collection(env)
ns.add_collection(container)
ns.add_collection(examples)
ns.add_collection(docs)

# Compatibility aliases for the previous flat task surface.
ns.add_task(deploy_release, name="release")
ns.add_task(deploy_push, name="push")
ns.add_task(tests_run, name="run_tests")
ns.add_task(tests_cached, name="run_tests_cached")
ns.add_task(tests_unit, name="run_unit_tests")
ns.add_task(tests_visual, name="run_visual_tests")
ns.add_task(tests_pyodide, name="run_pyodide_tests")
ns.add_task(tests_profile, name="profile_tests")
ns.add_task(tests_physics, name="run_physics_tests")
ns.add_task(tests_docs, name="run_doc_example_tests")
ns.add_task(build_image, name="image")
ns.add_task(env_prepare, name="prepare")
ns.add_task(env_check, name="check_env")
ns.add_task(benchmarks_list, name="list_benchmarks")
ns.add_task(benchmarks_single, name="run_benchmark")
ns.add_task(benchmarks_run, name="run_benchmarks")
ns.add_task(benchmarks_hotspots, name="profile_hotspots")
ns.add_task(benchmarks_analyze, name="analyze_performance")
ns.add_task(benchmarks_pyodide, name="profile_pyodide")
ns.add_task(container_shell, name="debug")
ns.add_task(container_cleanup, name="cleanup")
ns.add_task(container_x11, name="debug_x11")
ns.add_task(build_local, name="build_local")
ns.add_task(build_physics, name="build_physics")
ns.add_task(docs_build, name="make_docs")
ns.add_task(docs_build, name="docs_build")
ns.add_task(docs_generate_example_tests, name="generate_doc_example_tests")
ns.add_task(docs_test_examples, name="test_doc_examples")
ns.add_task(examples_checkout, name="checkout_examples")
