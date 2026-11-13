"""Real Tk widgets with a minimal Thonny host, under Docker/Xvfb."""

import importlib
import os
import subprocess
import sys
import time
import wave
from types import ModuleType, SimpleNamespace

import pytest

from test.unittests.thonny_plugin.test_learning_tools import ROOT, core

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def display():
    if os.environ.get("DISPLAY"):
        yield os.environ["DISPLAY"]
        return
    read_fd, write_fd = os.pipe()
    server = subprocess.Popen(
        [
            "Xvfb",
            "-displayfd",
            str(write_fd),
            "-screen",
            "0",
            "1280x1024x24",
            "-nolisten",
            "tcp",
        ],
        pass_fds=(write_fd,),
        stderr=subprocess.DEVNULL,
    )
    os.close(write_fd)
    try:
        with os.fdopen(read_fd) as stream:
            number = stream.readline().strip()
        assert number, "Xvfb did not start"
        yield ":" + number
    finally:
        server.terminate()
        server.wait(timeout=5)


@pytest.fixture
def ui(monkeypatch, tmp_path, display):
    import tkinter as tk

    monkeypatch.setenv("DISPLAY", display)
    root = tk.Tk()
    root.withdraw()
    text = tk.Text(root, undo=True)
    filename = tmp_path / "main.py"
    filename.write_text(core.project_code("E2"))
    text.insert("1.0", filename.read_text())
    text.edit_reset()
    editor = SimpleNamespace(
        get_content=lambda: text.get("1.0", "end-1c"),
        get_code_view=lambda: SimpleNamespace(text=text),
        get_filename=lambda: str(filename),
    )
    options = {"miniworlds.mode": "E2"}
    notebook = SimpleNamespace(
        get_current_editor=lambda: editor,
        get_all_editors=lambda: [editor],
        select=lambda e: None,
    )
    wb = SimpleNamespace(
        get_option=options.get,
        set_option=options.__setitem__,
        get_editor_notebook=lambda: notebook,
    )
    thonny = ModuleType("thonny")
    thonny.get_workbench = lambda: wb
    thonny.get_runner = lambda: None
    thonny.ui_utils = SimpleNamespace()
    monkeypatch.setitem(sys.modules, "thonny", thonny)
    package = ModuleType("_miniworlds_gui_test")
    package.__path__ = [
        str(ROOT / "libraries/thonny-miniworlds/thonnycontrib/miniworlds")
    ]
    monkeypatch.setitem(sys.modules, package.__name__, package)
    monkeypatch.setitem(sys.modules, package.__name__ + ".core", core)
    # Reload for every fixture so functions never retain a previous fake host.
    monkeypatch.delitem(sys.modules, package.__name__ + ".view", raising=False)
    module = importlib.import_module(package.__name__ + ".view")
    panel = module.MiniworldsView(root)

    def unexpected(message):
        raise AssertionError(message)

    panel.info = unexpected
    yield SimpleNamespace(
        root=root,
        panel=panel,
        editor=editor,
        text=text,
        filename=filename,
        module=module,
    )
    panel.destroy()
    root.destroy()
    sys.modules.pop(package.__name__ + ".view", None)


def pump(root, predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        root.update()
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("Timed out waiting for GUI result")


def test_real_widgets_filter_targets_and_atomic_undo(ui):
    panel, editor, text = ui.panel, ui.editor, ui.text
    assert len(panel.tabs.tabs()) == 8
    panel.target.set("world")
    panel.preview_event()
    assert "on_clicked_left" not in panel.event_box.cget("values")
    panel.target.set("player")
    panel.preview_event()
    assert "on_clicked_left" in panel.event_box.cget("values")
    original = editor.get_content()
    edit = core.event_edit(original, "E2", "player", "act")
    assert panel.apply_edit(editor, original, edit)
    assert "@player.register" in editor.get_content()
    text.edit_undo()
    assert editor.get_content() == original
    text.edit_redo()
    assert editor.get_content() == edit.apply(original)
    # A correction involving both deletion and insertion must also be one step.
    text.delete("1.0", "end")
    text.insert(
        "1.0",
        "from miniworlds import Actor\nclass Player(Actor):\n    def act():\n        pass\n",
    )
    text.edit_reset()
    original = editor.get_content()
    finding = next(
        f for f in core.check_code(original) if f.fix and f.severity == "Fehler"
    )
    panel.apply_edit(editor, original, finding.fix)
    text.edit_undo()
    assert editor.get_content() == original


def test_mode_persists_without_changing_code_and_help_is_progressive(ui):
    panel = ui.panel
    original = ui.editor.get_content()
    panel.mode.set(core.MODES["Q1"])
    panel.change_mode()
    assert core.project_mode(ui.filename.parent) == "Q1"
    assert ui.editor.get_content() == original
    panel.topic.set("move")
    panel.reset_help()
    assert "Beispiel:" not in panel.help_output.get("1.0", "end")
    panel.reveal_help()
    assert "Hinweis:" in panel.help_output.get("1.0", "end")
    panel.reveal_help()
    assert "self.move(2)" in panel.help_output.get("1.0", "end")


def test_gallery_and_nested_file_references(ui):
    from PIL import Image

    images = ui.filename.parent / "images"
    images.mkdir()
    path = images / "sprite.png"
    Image.new("RGBA", (40, 20), (200, 0, 0, 80)).save(path)
    ui.panel.refresh_media()
    assert ui.panel.media.item("images/sprite.png", "values") == ("40 × 20", "Ja")
    assert len(ui.panel.gallery_images) == 1
    core.save_project_mode(ui.filename.parent, "E2")
    nested = ui.filename.parent / "actors"
    nested.mkdir()
    ui.filename = nested / "player.py"
    ui.filename.write_text("")
    ui.editor.get_filename = lambda: str(ui.filename)
    assert ui.panel.media_reference(path) == "../images/sprite.png"


def test_sound_preview_worker_volume_and_stop(ui, monkeypatch):
    plugin_root = ROOT / "libraries/thonny-miniworlds"
    monkeypatch.setenv(
        "PYTHONPATH", str(plugin_root) + os.pathsep + os.environ.get("PYTHONPATH", "")
    )
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    sounds = ui.filename.parent / "sounds"
    sounds.mkdir()
    path = sounds / "silence.wav"
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
        stream.writeframes(b"\x00\x00" * 22050 * 3)
    ui.panel.refresh_media()
    ui.panel.media.selection_set("sounds/silence.wav")
    ui.panel.play_audio()
    process = ui.panel.audio_process
    assert process is not None
    ui.panel.set_volume(15)
    ui.panel.stop_audio()
    assert process.poll() is not None and ui.panel.audio_process is None
    # Also wait for natural completion and ensure there was no worker error.
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
        stream.writeframes(b"\x00\x00" * 2205)
    ui.panel.play_audio()
    pump(ui.root, lambda: ui.panel.audio_process is None)
    assert ui.panel.media_info.cget("text") == "Wiedergabe beendet."


def test_stale_editor_blocks_correction_and_examples_filter(ui):
    original = ui.editor.get_content()
    edit = core.event_edit(original, "E2", "player", "act")
    ui.text.insert("end-1c", "\n# changed")
    messages = []
    ui.panel.info = messages.append
    assert not ui.panel.apply_edit(ui.editor, original, edit)
    assert messages and "inzwischen geändert" in messages[0]
    ui.panel.example_topic.set("Eingabe")
    ui.panel.example_level.set("Fortgeschritten")
    ui.panel.filter_examples()
    assert ui.panel.example.get() == "Maus"
    assert "Erwartetes Verhalten:" in ui.panel.example_output.get("1.0", "end")


def test_installation_status_uses_selected_executable(ui, monkeypatch):
    class Proxy:
        def get_target_executable(self):
            return sys.executable

    proxy = Proxy()
    module = ModuleType("thonny.plugins.cpython_frontend.cp_front")
    module.LocalCPythonProxy = Proxy
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(
        ui.module,
        "get_runner",
        lambda: SimpleNamespace(get_backend_proxy=lambda: proxy),
    )
    ui.panel.show_status()
    pump(ui.root, lambda: ui.panel.status_process is None)
    output = ui.panel.status_output.get("1.0", "end")
    assert "Plugin in Thonny:" in output
    assert "Ausführungsinterpreter:" in output
    assert sys.executable in output
    assert "Status konnte nicht gelesen" not in output
    assert ui.panel.section.get() == "Installation"


def test_switching_projects_restores_each_mode(ui):
    project = ui.filename.parent
    core.save_project_mode(project, "E2")
    other = project / "q1_project"
    other.mkdir()
    main = other / "main.py"
    main.write_text(core.project_code("Q1"))
    core.save_project_mode(other, "Q1")
    ui.editor.get_filename = lambda: str(main)
    ui.panel.after_cancel(ui.panel.sync_job)
    ui.panel.sync_project()
    assert ui.panel.mode_key == "Q1"
    ui.editor.get_filename = lambda: str(ui.filename)
    ui.panel.after_cancel(ui.panel.sync_job)
    ui.panel.sync_project()
    assert ui.panel.mode_key == "E2"
    assert core.project_mode(other) == "Q1"


def installer_ui(ui, monkeypatch, state):
    import sys

    thonny = sys.modules["thonny"]
    thonny.get_thonny_user_dir = lambda: str(ui.filename.parent / "profile")
    module = importlib.import_module(ui.module.__package__ + ".installer")
    calls = []
    restarts = []
    runner = SimpleNamespace(
        get_backend_proxy=lambda: SimpleNamespace(
            get_target_executable=lambda: sys.executable
        ),
        is_waiting_toplevel_command=lambda: True,
        restart_backend=lambda **kwargs: restarts.append(kwargs),
    )
    monkeypatch.setattr(module, "get_runner", lambda: runner)
    monkeypatch.setattr(module, "get_thonny_user_dir", thonny.get_thonny_user_dir)

    def work(executable, action, emit, backup_root=None):
        calls.append((executable, action, backup_root))
        emit("test protocol\n")
        return state.copy()

    monkeypatch.setattr(module, "run_worker", work)
    monkeypatch.setattr(
        module, "fetch_versions", lambda python: {"latest": "2.0", "compatible": "2.0"}
    )
    dialog = module.LibraryDialog(ui.root, sys.executable)
    pump(ui.root, lambda: not dialog.busy)
    return module, dialog, calls, restarts


def install_state(**overrides):
    state = {
        "ok": True,
        "version": "1.0",
        "python": "3.12",
        "issues": [],
        "pip": True,
        "user_enabled": True,
        "managed": False,
        "editable": False,
    }
    state.update(overrides)
    return state


def test_installer_checks_versions_on_open_and_restarts_after_install(ui, monkeypatch):
    _, dialog, calls, restarts = installer_ui(ui, monkeypatch, install_state())
    try:
        assert "Update verfügbar: 1.0 → 2.0" in dialog.status.get()
        assert calls[0][1] == "inspect"
        dialog.change("install")
        pump(ui.root, lambda: not dialog.busy)
        assert calls[-1][1] == "install"
        assert restarts == [{"clean": True}]
        assert "test protocol" in dialog.log
    finally:
        dialog.close()


def test_installer_offline_is_not_reported_as_current_and_repair_needs_confirmation(
    ui, monkeypatch
):
    module, dialog, calls, _ = installer_ui(ui, monkeypatch, install_state())
    try:

        def offline(python):
            raise OSError("offline")

        monkeypatch.setattr(module, "fetch_versions", offline)
        dialog.check()
        pump(ui.root, lambda: not dialog.busy)
        assert "nicht festgestellt" in dialog.status.get()
        assert "aktuell" not in dialog.status.get()
        monkeypatch.setattr(
            module.messagebox, "askyesno", lambda *args, **kwargs: False
        )
        dialog.change("repair")
        assert not any(call[1] == "repair" for call in calls)
        monkeypatch.setattr(module.messagebox, "askyesno", lambda *args, **kwargs: True)
        dialog.change("repair")
        pump(ui.root, lambda: not dialog.busy)
        assert calls[-1][1] == "repair" and calls[-1][2].name == "miniworlds-backups"
    finally:
        dialog.close()


def test_installer_blocks_managed_environment_and_interpreter_changes(ui, monkeypatch):
    module, dialog, calls, _ = installer_ui(
        ui, monkeypatch, install_state(managed=True)
    )
    try:
        assert str(dialog.install_button.cget("state")) == "disabled"
        dialog.change("repair")
        assert len(calls) == 1
        monkeypatch.setattr(
            module,
            "get_runner",
            lambda: SimpleNamespace(get_backend_proxy=lambda: None),
        )
        dialog.check()
        assert "Interpreter wurde gewechselt" in dialog.status.get()
    finally:
        dialog.close()


def test_lab_ui_calls_real_experiment_backend(ui, monkeypatch):
    module = importlib.import_module(ui.module.__package__ + ".lab_view")

    class Proxy:
        def get_target_executable(self):
            return sys.executable

    cp = ModuleType("thonny.plugins.cpython_frontend.cp_front")
    cp.LocalCPythonProxy = Proxy
    monkeypatch.setitem(sys.modules, cp.__name__, cp)
    monkeypatch.setattr(
        module, "get_runner", lambda: SimpleNamespace(get_backend_proxy=lambda: Proxy())
    )
    original_popen = subprocess.Popen

    def popen(args, **kwargs):
        # The production command isolates Python; in Docker tests the live
        # engine under /app/source is supplied by Invoke's PYTHONPATH instead.
        assert "-I" in args
        return original_popen([a for a in args if a != "-I"], **kwargs)

    monkeypatch.setattr(module.subprocess, "Popen", popen)
    dialog = module.LabDialog(ui.panel)
    try:
        dialog.start()
        pump(ui.root, lambda: dialog.data is not None and not dialog.busy, timeout=10)
        player = next(
            row for row in dialog.data["objects"] if "player" in row["aliases"]
        )
        dialog.bank.selection_set(player["handle"])
        pump(ui.root, lambda: bool(dialog.methods) and not dialog.busy)
        move = next(label for label, name in dialog.methods.items() if name == "move")
        dialog.method.set(move)
        dialog.args.set("20")
        dialog.prediction.set("position changes")
        dialog.invoke()
        pump(ui.root, lambda: bool(dialog.data["history"]) and not dialog.busy)
        assert dialog.data["history"][-1]["code"] == "player.move(20)"
        assert dialog.data["history"][-1]["prediction"] == "position changes"
        ui.text.insert("end-1c", "\n# changed")
        pump(ui.root, lambda: dialog.stale)
        assert str(dialog.invoke_button.cget("state")) == "disabled"
        dialog.stop()
        assert not dialog.bank.get_children() and dialog.data is None
    finally:
        dialog.close()


def test_connected_lab_lifecycle_and_backend_restarts(ui, monkeypatch):
    module = importlib.import_module(ui.module.__package__ + ".live_view")
    wb = sys.modules["thonny"].get_workbench()
    bindings = {}
    wb.bind = lambda name, callback, add: bindings.setdefault(name, callback)
    wb.unbind = lambda name, callback: bindings.pop(name, None)
    common = ModuleType("thonny.common")
    common.ToplevelCommand = lambda name, **kw: dict(name=name, **kw)
    monkeypatch.setitem(sys.modules, common.__name__, common)

    class Proxy:
        pass

    cp = ModuleType("thonny.plugins.cpython_frontend.cp_front")
    cp.LocalCPythonProxy = Proxy
    monkeypatch.setitem(sys.modules, cp.__name__, cp)
    commands = []
    monkeypatch.setattr(
        module,
        "get_runner",
        lambda: SimpleNamespace(
            get_backend_proxy=lambda: Proxy(),
            is_waiting_toplevel_command=lambda: True,
            send_command=commands.append,
        ),
    )
    dialog = module.ConnectedLabDialog(ui.panel)
    try:
        dialog.start()
        assert commands[-1]["name"] == "Run"
        assert (
            commands[-1]["miniworlds_experiment"]["source"] == ui.editor.get_content()
        )
        connection = dialog.connection
        assert connection is not None
        bindings["BackendRestart"](SimpleNamespace(full=False))
        bindings["ToplevelResponse"](
            SimpleNamespace(command_name="get_environment_info")
        )
        assert dialog.connection is connection
        dialog.show_data(
            {
                "objects": [],
                "classes": [],
                "history": [],
                "prelude": [],
                "worlds": [],
                "paused": True,
            }
        )
        bindings["BackendRestart"](SimpleNamespace(full=True))
        assert dialog.connection is None and dialog.data is None and connection.closed
        assert not dialog.bank.get_children()
    finally:
        dialog.close()
    assert not bindings
