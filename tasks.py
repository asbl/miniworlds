from invoke import task
import os

IMAGE = "pygame-tests"
CONTAINER = "pygame-test-container"

def build_test_environment(c):
    """Build the rest environment. Must run bevor `run_tests`"""
    c.run(f"docker build -t {IMAGE} .")

@task
def run_tests(c):
    """Run all tests. build_test_environment must be called before `run_tests`"""
    build_test_environment(c)
    uid = os.getuid()
    gid = os.getgid()
    c.run(
        f"docker run --rm "
        f"--user {uid}:{gid} "
        f"-v {os.getcwd()}/test/outputfiles:/app/test/outputfiles "
        f"-v {os.getcwd()}/test/testfiles:/app/test/testfiles "
        f"{IMAGE} pytest test/ -v"
    )

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
    """Sphinx-Dokumentation erstellen"""
    c.run("cd docs && make gettext && sphinx-intl update -p build/gettext -l de -l en && make docs")

@task
def checkout_examples(c):
    """submodule update (with --init --recursive) on examples folder"""
    c.run ("cd examples && git submodule update --init --recursive")