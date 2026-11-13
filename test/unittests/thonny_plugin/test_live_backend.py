"""Real Thonny CPython wire protocol, SDL loop and authenticated side channel.

Requires Thonny 4.1.7 on the test interpreter's path. These tests do not replace
Thonny with a mock; only the graphical frontend is replaced by its wire client.
"""

import importlib
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import ModuleType

import pytest

from test.unittests.thonny_plugin.test_learning_tools import ROOT

pytestmark = pytest.mark.unit


@pytest.fixture
def connected_backend(tmp_path):
    thonny = pytest.importorskip(
        "thonny", reason="Install Thonny 4.1.7 for real-backend integration tests"
    )
    from thonny.common import ToplevelCommand, serialize_message

    package = ModuleType("_live_backend_test")
    package.__path__ = [
        str(ROOT / "libraries/thonny-miniworlds/thonnycontrib/miniworlds")
    ]
    sys.modules[package.__name__] = package
    Connection = importlib.import_module(
        package.__name__ + ".live_connection"
    ).Connection
    connection = Connection()
    filename = tmp_path / "main.py"
    source = """from miniworlds import World, Actor
class Player(Actor):
    def advance(self, steps):
        self.x += steps
        return self.position
    def references(self):
        return {"items": [self, self.world]}
    def forever(self):
        while True:
            pass
    def broken(self):
        self.x = 99
        raise ValueError("pupil error")
world = World(200, 200)
player = Player((10, 10))
alias = player
secondary = World(80, 100)
world.camera.add_right(secondary)
world.run()
"""
    filename.write_text(source.replace("Player((10, 10))", "Player((80, 80))"))
    paths = [str(ROOT / "libraries/thonny-miniworlds"), *sys.path]
    env = dict(
        os.environ,
        THONNY_USER_DIR=str(tmp_path / "profile"),
        THONNY_FRONTEND_SYS_PATH=repr(paths),
        PYTHONPATH=os.pathsep.join(p for p in paths if p),
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
    )
    launcher = Path(thonny.__file__).parent / "plugins/cpython_backend/cp_launcher.py"
    process = subprocess.Popen(
        [sys.executable, "-u", str(launcher), str(tmp_path), "{}"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    output = []

    def drain(stream):
        for line in stream:
            output.append(line)  # noqa: PERF402 -- stream output concurrently for failure diagnostics

    threads = [
        threading.Thread(target=drain, args=(s,), daemon=True)
        for s in (process.stdout, process.stderr)
    ]
    for thread in threads:
        thread.start()
    command = ToplevelCommand(
        "Run",
        args=[str(filename)],
        miniworlds_experiment={
            "port": connection.port,
            "token": connection.token,
            "source": source,
            "version": "v1",
        },
    )
    process.stdin.write(serialize_message(command) + "\n")
    process.stdin.flush()

    def receive():
        try:
            message = connection.events.get(timeout=15)
        except queue.Empty:
            pytest.fail("No backend response: " + "".join(output))
        assert not message.get("ended"), "".join(output)
        return message

    try:
        initial = receive()
        assert initial["ok"], initial
        yield connection, receive, initial["data"], process
    finally:
        connection.close()
        process.kill()
        process.communicate(timeout=5)
        for thread in threads:
            thread.join(timeout=2)


def test_real_thonny_run_pause_invoke_resume_and_versions(connected_backend):
    connection, receive, initial, process = connected_backend
    assert initial["paused"]
    player = next(r for r in initial["objects"] if "player" in r["aliases"])
    assert "alias" in player["aliases"]
    world = next(r for r in initial["objects"] if "world" in r["aliases"])
    frame = world["fields"]["frame"]
    request = connection.send(
        {
            "action": "invoke",
            "handle": player["handle"],
            "method": "advance",
            "arguments": "20",
        }
    )
    response = receive()
    assert response["ok"] and response["id"] == request
    updated = next(r for r in response["data"]["objects"] if "player" in r["aliases"])
    assert updated["fields"]["position"] != player["fields"]["position"]
    assert (
        next(r for r in response["data"]["objects"] if "world" in r["aliases"])[
            "fields"
        ]["frame"]
        == frame
    )
    connection.send({"action": "resume"})
    assert receive()["ok"]
    time.sleep(0.1)
    connection.send({"action": "pause"})
    response = receive()
    assert response["data"]["paused"]
    assert (
        next(r for r in response["data"]["objects"] if "world" in r["aliases"])[
            "fields"
        ]["frame"]
        != frame
    )
    connection.send(
        {"action": "invoke", "handle": player["handle"], "method": "broken"}
    )
    response = receive()
    assert not response["ok"] and "ValueError: pupil error" in response["error"]
    assert "main.py" in response["traceback"] and response["data"]["paused"]
    connection.send({"action": "revision", "version": "v2"})
    assert receive()["data"]["stale"]
    connection.send({"action": "resume"})
    assert not receive()["ok"]
    connection.send({"action": "revision", "version": "v1"})
    assert not receive()["data"]["stale"]
    connection.send(
        {"action": "invoke", "handle": "old-generation:0", "method": "advance"}
    )
    assert not receive()["ok"]
    assert process.poll() is None


def test_real_thonny_stop_interrupts_long_method_and_invalidates_connection(
    connected_backend,
):
    connection, _receive, initial, process = connected_backend
    player = next(r for r in initial["objects"] if "player" in r["aliases"])
    connection.send(
        {"action": "invoke", "handle": player["handle"], "method": "forever"}
    )
    time.sleep(0.2)
    # Thonny's cmd_stop_restart -> restart_backend -> _close_backend kills
    # the old process. SIGINT alone has different asyncio cancellation semantics.
    process.kill()
    assert connection.events.get(timeout=10).get("ended")


def test_real_thonny_selective_world_control_and_constructor(connected_backend):
    connection, receive, initial, _process = connected_backend
    world = next(r for r in initial["objects"] if "world" in r["aliases"])
    second = next(r for r in initial["objects"] if "secondary" in r["aliases"])
    connection.send({"action": "resume", "world": world["handle"]})
    assert receive()["ok"]
    time.sleep(0.1)
    connection.send({"action": "pause", "world": world["handle"]})
    response = receive()
    secondary = next(
        r for r in response["data"]["objects"] if "secondary" in r["aliases"]
    )
    assert secondary["fields"]["frame"] == second["fields"]["frame"]
    connection.send(
        {
            "action": "create",
            "class": "Player",
            "name": "another",
            "arguments": "(20, 20)",
            "world": second["handle"],
        }
    )
    response = receive()
    assert response["ok"], response
    actor = next(r for r in response["data"]["objects"] if "another" in r["aliases"])
    assert "secondary" in actor["fields"]["world"]


def test_real_thonny_nested_result_references(connected_backend):
    connection, receive, initial, _process = connected_backend
    player = next(r for r in initial["objects"] if "player" in r["aliases"])
    connection.send(
        {"action": "invoke", "handle": player["handle"], "method": "references"}
    )
    response = receive()
    assert response["ok"], response
    result = response["result"]
    assert result["kind"] == "dict"
    nested = result["items"][0][1]
    assert nested["kind"] == "list"
    assert nested["items"][0] == {
        "kind": "reference",
        "handle": player["handle"],
        "type": "Player",
    }
