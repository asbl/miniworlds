from invoke import task
from invoke.exceptions import Exit
import os
import re
import shutil

IMAGE = "pygame-tests"
CONTAINER = "pygame-test-container"
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
PHYSICS_REPO = os.path.join(REPO_ROOT, "physics")
MAIN_SETUP_PATH = os.path.join(REPO_ROOT, "source", "setup.py")
PHYSICS_SETUP_PATH = os.path.join(PHYSICS_REPO, "source", "setup.py")
VERSION_PATTERN = re.compile(r'version="([^"]+)"')

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
    "image_costume_sizes": "test/performance/profile_image_costume_sizes.py",
    "camera_culling": "test/performance/profile_camera_culling.py",
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
        "image_costume_sizes",
        "camera_culling",
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


def _docker_mounts() -> str:
    return (
        f"-v {os.getcwd()}/pytest.ini:/app/pytest.ini "
        f"-v {os.getcwd()}/conftest.py:/app/conftest.py "
        f"-v {os.getcwd()}/source:/app/source "
        f"-v {os.getcwd()}/test:/app/test "
        f"-v {os.getcwd()}/examples:/app/examples "
        f"-v {os.getcwd()}/physics/source:/app/physics/source "
        f"-v {os.getcwd()}/physics/test:/app/physics/test "
    )


def _docker_pythonpath() -> str:
    return "PYTHONPATH=/app/source:/app/physics/source"


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


def _print_release_plan(
    version: str,
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
        print("2. Run invoke run-tests")
    print("3. Commit and tag physics repository")
    print("4. Commit and tag main repository")
    if push:
        print("5. Push both branches and tags")
    else:
        print("5. Skip pushes")
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


def ensure_test_environment(c):
    """Build the docker image if it does not exist yet."""
    c.run(f"docker image inspect {IMAGE} >/dev/null 2>&1 || docker build -t {IMAGE} .")

def build_test_environment(c):
    """Build the rest environment. Must run bevor `run_tests`"""
    c.run(f"docker build -t {IMAGE} .")


def run_pytest_in_container(c, pytest_args: str, rebuild: bool = True):
    """Run pytest inside the docker image against the live source tree."""
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
        f"{IMAGE} env {_docker_pythonpath()} pytest {pytest_args}"
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
        f"{IMAGE} env SDL_AUDIODRIVER=dummy MINIWORLDS_TEST_FAST=1 {_docker_pythonpath()} python {script_path}"
    )


def run_python_scripts_in_container(c, script_paths: list[str], rebuild: bool = False):
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
        f"{_docker_mounts()}"
        f"{IMAGE} sh -lc \"export SDL_AUDIODRIVER=dummy MINIWORLDS_TEST_FAST=1 {_docker_pythonpath()} && {commands}\""
    )


@task(
    help={
        "version": "Release version, for example 3.5.0.1",
        "skip_tests": "Skip the Docker test run before committing and tagging",
        "push": "Push both repositories and tags after creating the release",
        "dry_run": "Show the planned release steps and blockers without changing anything",
    }
)
def release(c, version, skip_tests=False, push=True, dry_run=False):
    """Create a synchronized miniworlds/miniworlds_physics release and push tags for PyPI."""
    _validate_release_version(version)

    tag_name = f"v{version}"
    main_branch = _current_branch(c, REPO_ROOT, "Main")
    physics_branch = _current_branch(c, PHYSICS_REPO, "Physics")

    current_main_version = _read_version(MAIN_SETUP_PATH)
    current_physics_version = _read_version(PHYSICS_SETUP_PATH)
    main_status = _repo_status(c, REPO_ROOT)
    physics_status = _repo_status(c, PHYSICS_REPO)
    main_tag_exists = bool(_git_stdout(c, REPO_ROOT, f"tag -l {tag_name}"))
    physics_tag_exists = bool(_git_stdout(c, PHYSICS_REPO, f"tag -l {tag_name}"))

    if dry_run:
        _print_release_plan(
            version,
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
    if current_main_version != current_physics_version:
        raise Exit(
            "Main and physics package versions differ before release: "
            f"{current_main_version} != {current_physics_version}"
        )

    _write_version(MAIN_SETUP_PATH, version)
    _write_version(PHYSICS_SETUP_PATH, version)

    if not skip_tests:
        run_tests(c)

    _git(c, PHYSICS_REPO, "add source/setup.py")
    _git(c, PHYSICS_REPO, f'commit -m "Bump version to {version}"')
    _git(c, PHYSICS_REPO, f'tag -a {tag_name} -m "Release {tag_name}"')

    _git(c, REPO_ROOT, "add source/setup.py physics")
    _git(c, REPO_ROOT, f'commit -m "Bump version to {version}"')
    _git(c, REPO_ROOT, f'tag -a {tag_name} -m "Release {tag_name}"')

    if push:
        _git(c, PHYSICS_REPO, f"push origin {physics_branch}")
        _git(c, PHYSICS_REPO, f"push origin {tag_name}")
        _git(c, REPO_ROOT, f"push origin {main_branch}")
        _git(c, REPO_ROOT, f"push origin {tag_name}")

@task
def run_tests(c):
    """Run all tests. build_test_environment must be called before `run_tests`"""
    run_pytest_in_container(c, "-v")


@task
def run_tests_cached(c):
    """Run all tests with the existing image and the current working tree mounted into the container."""
    run_pytest_in_container(c, "-v", rebuild=False)


@task
def run_unit_tests(c):
    """Run only the fast unit tests inside docker."""
    run_pytest_in_container(c, "-m unit -v", rebuild=False)


@task
def run_visual_tests(c):
    """Run only the screenshot-based visual tests inside docker."""
    run_pytest_in_container(c, "-m visual -v", rebuild=False)


@task
def profile_tests(c):
    """Show the slowest tests inside docker without rebuilding the image."""
    run_pytest_in_container(c, "-q --durations=25", rebuild=False)


@task
def profile_hotspots(c):
    """Run focused hotspot profiling scripts inside docker."""
    run_python_scripts_in_container(
        c,
        _resolve_benchmark_scripts("all"),
        rebuild=False,
    )


@task
def list_benchmarks(c):
    """List available benchmark groups and individual benchmark names."""
    del c
    print("Benchmark groups:")
    for group_name in sorted(BENCHMARK_GROUPS.keys()):
        print(f"- {group_name}: {', '.join(BENCHMARK_GROUPS[group_name])}")
    print("\nIndividual benchmarks:")
    for benchmark_name in sorted(BENCHMARK_SCRIPTS.keys()):
        print(f"- {benchmark_name}: {BENCHMARK_SCRIPTS[benchmark_name]}")


@task
def run_benchmark(c, name, rebuild=False):
    """Run one benchmark by name inside docker."""
    scripts = _resolve_benchmark_scripts(name)
    run_python_scripts_in_container(c, scripts, rebuild=rebuild)


@task
def run_benchmarks(c, selection="quick", rebuild=False):
    """Run a benchmark group or a single named benchmark inside docker.

    Examples:
        invoke run-benchmarks
        invoke run-benchmarks --selection=world
        invoke run-benchmarks --selection=blockable_movement_cprofile
    """
    scripts = _resolve_benchmark_scripts(selection)
    run_python_scripts_in_container(c, scripts, rebuild=rebuild)

@task
def debug(c):
    """Interaktives Debugging des Containers"""
    c.run(f"docker run --rm -it {IMAGE} bash")

@task
def cleanup(c):
    """Cleanup - Nicht verwendete Images und Container entfernen"""
    c.run("docker system prune -f")

@task
def debug_x11(c):
    """Container starten und eine grafische Debugging-Umgebung bereitstellen"""
    c.run("xhost +local:root")
    c.run(
        f"docker run --rm -it "
        f"-e DISPLAY=$DISPLAY "
        f"-v /tmp/.X11-unix:/tmp/.X11-unix "
        f"{IMAGE} bash"
    )
    c.run("xhost -local:root")

@task
def build_local(c):
    """Lokalen Build der source/ ausführen"""
    c.run("cd source && pip install -e .")

@task
def build_physics(c):
    """Lokalen Build der source/ ausführen"""
    c.run("cd physics/source && pip install -e .")


@task
def make_docs(c):
    """Mehrsprachige Sphinx-Dokumentation erstellen (EN + DE)"""
    with c.cd("docs"):
        build_dir = "build"

        # Build-Verzeichnis leeren
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        os.makedirs(build_dir, exist_ok=True)

        # Schritt 1: gettext extrahieren
        c.run("make gettext", pty=True)

        # Schritt 2: PO-Dateien aktualisieren
        c.run("sphinx-intl update -p build/gettext -l en -l de", pty=True)

        # Schritt 3: Kompilieren der .mo-Dateien
        c.run("sphinx-intl build", pty=True)

        # Schritt 4: HTML für Englisch bauen
        c.run("sphinx-build -b html -D language=en source build/html/en", pty=True)

        # Schritt 5: HTML für Deutsch bauen
        c.run("sphinx-build -b html -D language=de source build/html/de", pty=True)


def upload_docs(c):
    pass

@task
def checkout_examples(c):
    """submodule update (with --init --recursive) on examples folder"""
    c.run ("cd examples && git submodule update --init --recursive")