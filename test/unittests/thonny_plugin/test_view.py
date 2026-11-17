"""Real Tk widgets with a minimal Thonny host, under Docker/Xvfb."""

import importlib
import os
import subprocess
import sys
import time
import wave
from pathlib import Path
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
    docks = {}
    wb.bind = lambda *args: None
    wb.unbind = lambda *args: None

    def get_view(name):
        if name == "MiniworldsView":
            return panel
        if name not in docks:
            dock_module = importlib.import_module(package.__name__ + ".lab_dock")
            monkeypatch.setattr(dock_module, "get_workbench", lambda: wb)
            live = importlib.import_module(package.__name__ + ".live_view")
            monkeypatch.setattr(live, "get_workbench", lambda: wb)
            docks[name] = dock_module.MiniworldsLabView(root)
        return docks[name]

    def show_view(name, set_focus=True):
        view = get_view(name)
        if name != "MiniworldsView":
            view.pack(fill="both", expand=True)
        return view

    wb.get_view = get_view
    wb.show_view = show_view
    wb.hide_view = lambda name: docks[name].pack_forget() if name in docks else None

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
    for dock in docks.values():
        dock.destroy()
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
    assert len(panel.tabs.tabs()) == 3
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
    ui.panel.media_kind.set("Sounds")
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
    assert ui.panel.settings_dialog.state() != "withdrawn"


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


def form_lab(ui, monkeypatch):
    import copy

    module = importlib.import_module(ui.module.__package__ + ".lab_view")
    model = importlib.import_module(ui.module.__package__ + ".lab_model")

    def compare(other):
        pass

    def move(distance: int = 1):
        pass

    methods = [
        {
            "name": name,
            "signature": "(...)",
            "owner": "Player",
            "inherited": False,
            "parameters": model.parameter_schema(fn),
        }
        for name, fn in [("compare", compare), ("move", move)]
    ]
    data = {
        "objects": [
            {
                "handle": "p",
                "aliases": ["player"],
                "type": "Player",
                "fields": {"x": "20"},
                "methods": methods,
            },
            {
                "handle": "q",
                "aliases": ["other"],
                "type": "Player",
                "fields": {"x": "50"},
                "methods": methods,
            },
        ],
        "classes": [],
        "history": [],
        "prelude": [],
        "paused": True,
    }
    dialog = module.LabDialog(ui.panel)
    commands = []

    def send(command):
        dialog.begin_action(command)
        commands.append(command)

    monkeypatch.setattr(dialog, "send", send)
    dialog.show_data(copy.deepcopy(data))
    dialog.bank.selection_set("p")
    pump(ui.root, lambda: bool(dialog.method_form.rows))
    dialog.choose_method(
        next(label for label, name in dialog.methods.items() if name == "compare")
    )
    return dialog, commands, data


def test_parameter_reference_picker_keeps_receiver_and_shows_call(ui, monkeypatch):
    dialog, commands, _ = form_lab(ui, monkeypatch)
    try:
        value, mode, _ = dialog.method_form.rows["other"]
        mode.set("Objekt")
        value.set("other")
        assert dialog.bank.selection() == ("p",)
        assert dialog.preview.get() == "player.compare(other=other)"
        dialog.invoke()
        assert (
            commands[-1]["handle"] == "p" and commands[-1]["arguments"] == "other=other"
        )
        assert dialog.create_frame.winfo_manager() == ""
        dialog.create_visible.set(True)
        dialog.toggle_create()
        assert dialog.create_frame.winfo_manager() == "pack"
    finally:
        dialog.close()


def test_before_after_comparison_survives_selection_and_inspection(ui, monkeypatch):
    import copy

    dialog, _, data = form_lab(ui, monkeypatch)
    try:
        dialog.begin_action({"action": "invoke"})
        updated = copy.deepcopy(data)
        updated["objects"][0]["fields"]["x"] = "40"
        dialog.show_data(updated)
        dialog.set_outcome({"ok": True})
        ui.root.update()
        dialog.show_data(copy.deepcopy(updated))
        ui.root.update()
        row = dialog.fields.item(dialog.fields.get_children()[0])
        assert row["text"] == "● x" and row["values"] == [20, 40]
        dialog.set_outcome(
            {
                "ok": False,
                "error": "TypeError: bad argument",
                "traceback": "technical trace",
            }
        )
        assert "Parameter" in dialog.feedback.get()
        assert "technical trace" in dialog.details.get("1.0", "end")
        assert "technical trace" not in dialog.log.get("1.0", "end")
    finally:
        dialog.close()


def test_connected_lab_program_stop_is_distinct_from_close(ui, monkeypatch):
    module = importlib.import_module(ui.module.__package__ + ".live_view")
    wb = sys.modules["thonny"].get_workbench()
    wb.bind = lambda *args: None
    wb.unbind = lambda *args: None
    stops = []
    monkeypatch.setattr(
        module,
        "get_runner",
        lambda: SimpleNamespace(cmd_stop_restart=lambda: stops.append(True)),
    )
    dialog = module.ConnectedLabDialog(ui.panel)
    try:
        dialog.stop_program()
        assert stops == [True]
        assert not dialog.bank.get_children()
        dialog.close()
        assert stops == [True], (
            "Closing the laboratory must not stop unrelated pupil execution."
        )
    finally:
        if dialog.winfo_exists():
            dialog.close()


def test_navigation_has_three_visible_areas_and_routes_context_help(ui):
    panel = ui.panel
    assert [panel.tabs.tab(tab, "text") for tab in panel.tabs.tabs()] == [
        "Start",
        "Code",
        "Medien",
    ]
    assert not hasattr(panel, "section_box")
    assert [panel.code_tabs.tab(tab, "text") for tab in panel.code_tabs.tabs()] == [
        "Hilfe",
        "Aktion",
        "Prüfen",
    ]
    ui.text.mark_set("insert", "1.6")
    panel.context_help()
    assert panel.tabs.select() == str(panel.code_page)
    assert panel.code_tabs.select() == str(panel.help_tab)
    panel.show_page("Ereignisse")
    ui.root.update()
    assert panel.target_box.cget("values")
    panel.show_page("Prüfung")
    ui.root.update()
    assert panel.checked_editor is ui.editor


def test_media_opens_without_refresh_and_import_selects_new_file(ui, monkeypatch):
    from PIL import Image

    images = ui.filename.parent / "images"
    images.mkdir()
    Image.new("RGB", (10, 10), "red").save(images / "existing.png")
    ui.panel.show_page("Bilder & Sounds")
    ui.root.update()
    assert ui.panel.media_project == ui.filename.parent
    assert ui.panel.media.exists("images/existing.png")
    assert ui.panel.gallery_frame.winfo_manager() == "pack"
    assert not ui.panel.media.winfo_manager(), "Do not show the same images twice."
    sound = ui.filename.parent / "click.wav"
    sound.write_bytes(b"dummy sound import")
    monkeypatch.setattr(
        ui.module.filedialog, "askopenfilenames", lambda **kw: (str(sound),)
    )
    ui.panel.import_files()
    ui.root.update()
    assert ui.panel.media_kind.get() == "Sounds"
    assert ui.panel.media.selection() == ("sounds/click.wav",)
    assert str(ui.panel.media_insert_button.cget("state")) == "normal"


def test_object_lab_opens_and_starts_in_one_click(ui, monkeypatch):
    import tkinter as tk

    module = importlib.import_module(ui.module.__package__ + ".live_view")
    starts = []

    class Dialog(tk.Frame):
        def __init__(self, owner, parent=None):
            super().__init__(parent if parent is not None else owner)

        def start(self):
            starts.append(True)

        def close(self):
            self.destroy()

    monkeypatch.setattr(module, "ConnectedLabDialog", Dialog)
    ui.panel.lab_button.invoke()
    assert starts == [True]
    original = ui.panel.lab_dialog
    ui.panel.lab_button.invoke()
    assert ui.panel.lab_dialog is original and starts == [True]


def test_project_creation_is_one_dialog_with_inline_errors(ui, monkeypatch):
    import tkinter as tk

    opened = []
    wb = sys.modules["thonny"].get_workbench()
    wb.get_editor_notebook().show_file = opened.append
    ui.panel.last_project_parent = ui.filename.parent
    ui.panel.new_project()
    dialog = next(
        child
        for child in ui.panel.winfo_children()
        if isinstance(child, tk.Toplevel) and child.title() == "Projekt anlegen"
    )

    def descendants(widget):
        result = []
        for child in widget.winfo_children():
            result.append(child)
            result.extend(descendants(child))
        return result

    widgets = descendants(dialog)
    submit = next(
        w
        for w in widgets
        if w.winfo_class() == "TButton" and w.cget("text") == "Projekt anlegen"
    )
    submit.invoke()
    assert len(opened) == 1 and Path(opened[0]).is_file()
    assert Path(opened[0]).parent.name == "mein_spiel"


def test_navigation_remains_reachable_in_184_pixel_sidebar(ui):
    import tkinter as tk

    ui.panel.pack(fill="both", expand=True)
    ui.root.geometry("184x700")
    ui.root.deiconify()
    pump(ui.root, lambda: ui.root.winfo_width() == 184)
    # Scan the actual header hit targets, not just its stored tab names.
    visible = set()
    for y in range(0, 36, 3):
        for x in range(ui.panel.tabs.winfo_width()):
            try:
                visible.add(ui.panel.tabs.index(f"@{x},{y}"))
            except tk.TclError:
                pass
    assert visible == {0, 1, 2}, (
        "All three top-level tabs must be reachable without widening the dock."
    )
    assert ui.panel.lab_button.winfo_reqwidth() <= ui.panel.lab_button.winfo_width()
    ui.panel.show_page("Hilfe")
    ui.root.update()
    inner = set()
    for y in range(0, 36, 3):
        for x in range(ui.panel.code_tabs.winfo_width()):
            try:
                inner.add(ui.panel.code_tabs.index(f"@{x},{y}"))
            except tk.TclError:
                pass
    assert inner == {0, 1, 2}, "All code tools must also fit the narrow dock."
    ui.root.withdraw()


def test_embedded_lab_creates_no_window_and_keeps_session_when_returning(
    ui, monkeypatch
):
    import tkinter as tk

    module = importlib.import_module(ui.module.__package__ + ".live_view")
    wb = sys.modules["thonny"].get_workbench()
    bindings = {}
    wb.bind = lambda name, callback, add: bindings.setdefault(name, callback)
    wb.unbind = lambda name, callback: bindings.pop(name, None)
    starts = []
    monkeypatch.setattr(
        module.ConnectedLabDialog, "start", lambda lab: starts.append(lab)
    )
    before = {w for w in ui.root.winfo_children() if isinstance(w, tk.Toplevel)}
    ui.panel.open_lab()
    lab = ui.panel.lab_dialog
    assert not isinstance(lab, tk.Toplevel)
    assert lab.winfo_toplevel() is ui.root
    assert {w for w in ui.root.winfo_children() if isinstance(w, tk.Toplevel)} == before
    dock = wb.get_view("MiniworldsLabView")
    assert lab.master is dock
    assert dock.winfo_manager() == "pack"
    assert ui.panel.tabs.winfo_manager() == "grid"
    lab.data = {"objects": [], "history": [{"code": "player.move(1)"}]}
    lab.back()
    assert ui.panel.tabs.winfo_manager() == "grid"
    assert not dock.winfo_manager()
    ui.panel.open_lab()
    assert ui.panel.lab_dialog is lab and len(starts) == 1
    assert lab.data["history"][0]["code"] == "player.move(1)"
    ui.panel.show_page("Hilfe")
    assert ui.panel.tabs.winfo_manager() == "grid"
    lab.close()
    assert not bindings


def test_docked_lab_keeps_objects_and_action_visible(ui, monkeypatch):
    module = importlib.import_module(ui.module.__package__ + ".live_view")
    wb = sys.modules["thonny"].get_workbench()
    wb.bind = lambda *args: None
    wb.unbind = lambda *args: None
    monkeypatch.setattr(module.ConnectedLabDialog, "start", lambda lab: None)
    ui.root.geometry("1000x600")
    ui.root.deiconify()
    ui.panel.open_lab()
    lab = ui.panel.lab_dialog
    pump(ui.root, lambda: ui.root.winfo_width() == 1000)
    assert lab.load_button.winfo_reqwidth() <= lab.load_button.winfo_width()
    assert lab.stop_button.winfo_reqwidth() <= lab.stop_button.winfo_width()
    assert lab.bank.winfo_ismapped() and lab.method_box.winfo_ismapped()
    assert lab.bank.winfo_rootx() < lab.method_box.winfo_rootx()
    assert not lab.properties_frame.winfo_manager()
    assert not lab.history_frame.winfo_manager()
    assert lab.invoke_button.winfo_rooty() < lab.winfo_rooty() + lab.winfo_height()
    assert not lab.world_box.winfo_manager(), (
        "A world selector is unnecessary for one world."
    )
    ui.root.withdraw()


def test_lab_open_keeps_a_session_started_from_the_view_menu(ui, monkeypatch):
    module = importlib.import_module(ui.module.__package__ + ".live_view")
    starts = []
    monkeypatch.setattr(
        module.ConnectedLabDialog, "start", lambda lab: starts.append(lab)
    )
    dock = sys.modules["thonny"].get_workbench().get_view("MiniworldsLabView")
    dock.lab.loaded_revision = "manually-loaded"
    ui.panel.open_lab()
    assert not starts
    assert ui.panel.lab_dialog is dock.lab


def test_lab_search_preserves_filter_and_parameter_values(ui, monkeypatch):
    import copy

    dialog, commands, data = form_lab(ui, monkeypatch)
    try:
        dialog.method_search.set("bewegen")
        assert list(dialog.method_box.cget("values")) == [dialog.method.get()]
        assert dialog.methods[dialog.method.get()] == "move"
        dialog.method_form.rows["distance"][0].set("23")
        dialog.show_data(copy.deepcopy(data))
        assert dialog.method_search.get() == "bewegen"
        assert dialog.method_form.rows["distance"][0].get() == "23"
        dialog.choose_method(
            next(label for label, name in dialog.methods.items() if name == "compare")
        )
        dialog.choose_method(
            next(label for label, name in dialog.methods.items() if name == "move")
        )
        assert dialog.method_form.rows["distance"][0].get() == "23"
        assert dialog.method_form.rows["distance"][2].bind("<Return>")
        dialog.method_form.enter()
        assert (
            commands[-1]["method"] == "move"
            and commands[-1]["arguments"] == "distance=23"
        )
        dialog.method_search.set("unbekannte methode")
        assert dialog.method.get() == ""
        assert not dialog.method_form.winfo_manager()
        dialog.show_data(copy.deepcopy(data))
        assert dialog.method.get() == "", (
            "Snapshots must not replace an empty search result."
        )
        count = len(commands)
        dialog.invoke()
        assert len(commands) == count
    finally:
        dialog.close()


def test_lab_result_is_inline_and_repeat_uses_original_receiver(ui, monkeypatch):
    import copy

    dialog, commands, data = form_lab(ui, monkeypatch)
    try:
        dialog.begin_action({"action": "invoke"})
        updated = copy.deepcopy(data)
        updated["objects"][0]["fields"]["x"] = "40"
        updated["history"] = [
            {"code": "player.move(distance=20)", "result": "None", "prediction": ""}
        ]
        dialog.show_data(updated)
        dialog.set_outcome({"ok": True})
        assert "player.move" in dialog.last_call.get()
        assert "x: 20 → 40" in dialog.result_summary.get()
        assert not dialog.properties_frame.winfo_manager()
        dialog.bank.selection_set("q")
        dialog.select_object()
        dialog.repeat_last()
        assert commands[-1]["action"] == "invoke"
        assert commands[-1]["handle"] == "p"
        assert commands[-1]["arguments"] == "distance=20"
        assert dialog.bank.selection() == ("p",)
        dialog.method_search.set("compare")
        dialog.repeat_last()
        assert dialog.method_search.get() == ""
        assert commands[-1]["method"] == "move"
        updated["paused"] = False
        dialog.show_data(updated)
        count = len(commands)
        dialog.method_form.enter()
        dialog.repeat_last()
        assert len(commands) == count, (
            "Keyboard and repeat must respect a running simulation."
        )
    finally:
        dialog.close()


def test_connected_lab_pause_toggle_and_world_selector(ui, monkeypatch):
    module = importlib.import_module(ui.module.__package__ + ".live_view")
    monkeypatch.setattr(module, "get_workbench", sys.modules["thonny"].get_workbench)
    lab = module.ConnectedLabDialog(ui.panel)
    commands = []
    monkeypatch.setattr(lab, "send", commands.append)
    data = {
        "objects": [],
        "classes": [],
        "history": [],
        "prelude": [],
        "worlds": [{"handle": "w1", "type": "World"}],
        "paused": True,
    }
    try:
        lab.show_data(data)
        lab.toggle_pause()
        assert commands[-1] == {"action": "resume"}
        assert not lab.world_box.winfo_manager()
        data["paused"] = False
        data["worlds"].append({"handle": "w2", "type": "World"})
        lab.show_data(data)
        assert lab.world_box.winfo_manager() == "pack"
        lab.toggle_pause()
        assert commands[-1] == {"action": "pause"}
        lab.world_choice.set("2: World")
        lab.toggle_pause()
        assert commands[-1] == {"action": "pause", "world": "w2"}
    finally:
        lab.close()


def test_parameter_form_hides_extra_defaults_without_losing_them(ui, monkeypatch):
    dialog, _, _ = form_lab(ui, monkeypatch)
    model = importlib.import_module(ui.module.__package__ + ".lab_model")

    def move(distance=10, direction=None):
        pass

    try:
        form = dialog.method_form
        form.configure_parameters("example", model.parameter_schema(move), {})
        assert len(form.optional_rows) == 1
        assert not form.optional_rows[0].winfo_manager()
        assert form.code() == "distance=10, direction=None"
        form.optional.set(True)
        form.show_optional()
        assert form.optional_rows[0].winfo_manager() == "pack"
        form.rows["direction"][0].set("left")
        form.optional.set(False)
        form.show_optional()
        assert "direction='left'" in form.code()
    finally:
        dialog.close()


def test_lab_mode_switch_updates_class_diagram_and_signatures(ui, monkeypatch):
    dialog, _, _ = form_lab(ui, monkeypatch)
    ui.panel.lab_dialog = dialog
    try:
        assert not dialog.diagram.winfo_manager()
        ui.panel.mode.set(core.MODES["Q1"])
        ui.panel.change_mode()
        assert dialog.diagram.winfo_manager() == "pack"
        assert dialog.bank_heading.cget("text") == "Instanzen"
        assert dialog.create_frame.cget("text") == "Konstruktor"
        assert "(...)" in dialog.method.get()
        ui.panel.mode.set(core.MODES["E2"])
        ui.panel.change_mode()
        assert not dialog.diagram.winfo_manager()
        assert dialog.bank_heading.cget("text") == "Figuren"
        assert "(...)" not in dialog.method.get()
    finally:
        dialog.close()


def test_lab_stop_cancels_pending_reload(ui, monkeypatch):
    module = importlib.import_module(ui.module.__package__ + ".live_view")
    monkeypatch.setattr(module, "get_workbench", sys.modules["thonny"].get_workbench)
    lab = module.ConnectedLabDialog(ui.panel)
    called = []
    try:
        lab.reload_job = lab.after(50, lambda: called.append("reloaded"))
        lab.stop_program()
        assert lab.reload_job is None
        finished = []
        ui.root.after(100, lambda: finished.append(True))
        pump(ui.root, lambda: bool(finished))
        assert not called
    finally:
        lab.close()


def test_workshop_cards_select_by_click_and_keyboard_and_keep_selection(
    ui, monkeypatch
):
    import copy

    dialog, commands, data = form_lab(ui, monkeypatch)
    try:
        ui.panel.pack(fill="both", expand=True)
        ui.panel.tabs.grid_remove()
        dialog.grid(row=2, column=0, sticky="nsew")
        ui.root.geometry("800x550")
        ui.root.deiconify()
        bank = dialog.bank
        pump(ui.root, lambda: bank.winfo_ismapped())
        bank.canvas.event_generate("<Button-1>", x=25, y=bank.CARD_HEIGHT + 25)
        assert bank.selection() == ("q",)
        assert commands[-1] == {"action": "select", "handle": "q"}
        bank.navigate(SimpleNamespace(keysym="Up"))
        assert bank.selection() == ("p",)
        bank.navigate(SimpleNamespace(keysym="End"))
        assert bank.selection() == ("q",)
        dialog.show_data(copy.deepcopy(data))
        assert bank.selection() == ("q",)
        labels = [
            bank.canvas.itemcget(item, "text")
            for item in bank.canvas.find_all()
            if bank.canvas.type(item) == "text"
        ]
        assert any("✓ other" in label for label in labels)
        assert "other" in dialog.receiver.get()
    finally:
        ui.root.withdraw()
        dialog.close()


def test_workshop_hides_extras_and_shows_reference_choice_only_where_useful(
    ui, monkeypatch
):
    dialog, _, _ = form_lab(ui, monkeypatch)
    try:
        assert not dialog.method_filters.winfo_manager()
        assert not dialog.more_frame.winfo_manager()
        assert not dialog.method_form.advanced_toggle.winfo_manager()
        assert dialog.method_form.selectors["other"].winfo_manager() == "pack"
        dialog.methods_toggle.invoke()
        assert dialog.method_filters.winfo_manager() == "pack"
        dialog.method_search.set("bewegen")
        assert not dialog.method_form.selectors["distance"].winfo_manager()
        dialog.methods_toggle.invoke()
        assert dialog.method_search.get() == ""
        dialog.more_toggle.invoke()
        assert dialog.more_frame.winfo_manager() == "pack"
        dialog.more_toggle.invoke()
        assert not dialog.more_frame.winfo_manager()
    finally:
        dialog.close()


def test_workshop_footer_stays_visible_when_details_scroll(ui, monkeypatch):
    module = importlib.import_module(ui.module.__package__ + ".live_view")
    monkeypatch.setattr(module.ConnectedLabDialog, "start", lambda lab: None)
    ui.root.geometry("900x420")
    ui.root.deiconify()
    ui.panel.open_lab()
    lab = ui.panel.lab_dialog
    ui.root.update()
    toolbar_y = lab.toolbar.winfo_rooty()
    lab.more_toggle.invoke()
    lab.history_visible.set(True)
    lab.toggle_history()
    lab.properties_visible.set(True)
    lab.toggle_properties()
    ui.root.update()
    lab.action_canvas.yview_moveto(1)
    ui.root.update()
    assert lab.toolbar.winfo_rooty() == toolbar_y
    for button in (lab.load_button, lab.stop_button, lab.pause_button):
        assert button.winfo_ismapped()
        assert button.winfo_rooty() >= lab.winfo_rooty()
        assert (
            button.winfo_rooty() + button.winfo_height()
            <= lab.winfo_rooty() + lab.winfo_height()
        )
    ui.root.withdraw()


def test_workshop_class_cards_open_constructor_and_disappear_in_e2(ui, monkeypatch):
    import copy

    dialog, _, data = form_lab(ui, monkeypatch)
    try:
        updated = copy.deepcopy(data)
        updated["classes"] = [{"name": "Player", "parameters": []}]
        dialog.show_data(updated)
        ui.panel.mode.set(core.MODES["Q1"])
        dialog.apply_mode()
        assert str(dialog.classes_host) in [
            str(pane) for pane in dialog.workspace.panes()
        ]
        assert dialog.diagram.find_withtag("class_Player")
        assert dialog.diagram.tag_bind("class_Player", "<Button-1>")
        dialog.choose_class("Player")
        assert dialog.class_name.get() == "Player"
        assert dialog.create_frame.winfo_manager() == "pack"
        ui.panel.mode.set(core.MODES["E2"])
        dialog.apply_mode()
        assert str(dialog.classes_host) not in [
            str(pane) for pane in dialog.workspace.panes()
        ]
    finally:
        dialog.close()


def test_refined_lab_remembers_method_and_fields_per_object(ui, monkeypatch):
    dialog, _, _ = form_lab(ui, monkeypatch)
    try:
        dialog.method_form.rows["other"][0].set("42")
        dialog.bank.selection_set("q")
        dialog.choose_method(next(k for k, v in dialog.methods.items() if v == "move"))
        dialog.method_form.rows["distance"][0].set("17")
        dialog.bank.selection_set("p")
        assert dialog.methods[dialog.method.get()] == "compare"
        assert dialog.method_form.rows["other"][0].get() == "42"
        dialog.bank.selection_set("q")
        assert dialog.methods[dialog.method.get()] == "move"
        assert dialog.method_form.rows["distance"][0].get() == "17"
    finally:
        dialog.close()


def test_refined_card_search_keeps_receiver_and_navigates_only_matches(ui, monkeypatch):
    import copy

    dialog, _, data = form_lab(ui, monkeypatch)
    try:
        updated = copy.deepcopy(data)
        for index in range(8):
            row = copy.deepcopy(updated["objects"][0])
            row.update(handle=f"enemy{index}", aliases=[f"gegner{index}"])
            updated["objects"].append(row)
        dialog.show_data(updated)
        bank = dialog.bank
        assert bank.filter_bar.winfo_manager() == "pack"
        bank.query.set("GEGNER")
        assert len(bank.visible_handles()) == 8
        assert bank.selection() == ("p",)
        assert "Auswahl ausgeblendet" in bank.count.get()
        bank.navigate(SimpleNamespace(keysym="End"))
        assert bank.selection() == ("enemy7",)
        bank.query.set("nichts gefunden")
        assert not bank.visible_handles()
        assert bank.selection() == ("enemy7",)
        bank.clear_filter()
        assert len(bank.visible_handles()) == 10
        assert bank.selection() == ("enemy7",)
    finally:
        dialog.close()


def test_refined_validation_marks_field_and_blocks_invalid_call(ui, monkeypatch):
    dialog, commands, _ = form_lab(ui, monkeypatch)
    try:
        dialog.choose_method(next(k for k, v in dialog.methods.items() if v == "move"))
        form = dialog.method_form
        form.rows["distance"][0].set("kein wert")
        assert "distance" in form.invalid_fields
        assert "Zahl" in form.error_labels["distance"].cget("text")
        assert form.error_labels["distance"].winfo_manager() == "pack"
        assert not dialog.action_ready(True)
        assert "markierten" in dialog.action_hint.get()
        count = len(commands)
        form.enter()
        assert len(commands) == count
        form.rows["distance"][0].set("12")
        assert not form.invalid_fields
        assert not form.error_labels["distance"].winfo_manager()
        assert dialog.action_ready(True)
        form.enter()
        assert commands[-1]["arguments"] == "distance=12"
    finally:
        dialog.close()


def test_refined_result_keeps_original_receiver_after_selection_change(ui, monkeypatch):
    import copy

    dialog, _, data = form_lab(ui, monkeypatch)
    try:
        dialog.begin_action({"action": "invoke", "handle": "p"})
        dialog.busy = True
        updated = copy.deepcopy(data)
        updated["objects"][0]["fields"]["x"] = "40"
        updated["history"] = [
            {"code": "player.move(20)", "result": "None", "prediction": ""}
        ]
        dialog.bank.selection_set("q")
        dialog.busy = False
        dialog.show_data(updated)
        dialog.set_outcome({"ok": True})
        assert "player" in dialog.result_panel.cget("text")
        assert "x: 20 → 40" in dialog.result_summary.get()
        assert "other" in dialog.receiver.get()
        dialog.bank.selection_set("p")
        assert "x: 20 → 40" in dialog.result_summary.get()
    finally:
        dialog.close()


def test_refined_layout_fits_small_q1_dock_and_can_hide_classes(ui, monkeypatch):
    module = importlib.import_module(ui.module.__package__ + ".live_view")
    monkeypatch.setattr(module.ConnectedLabDialog, "start", lambda lab: None)
    ui.root.geometry("680x500")
    ui.root.deiconify()
    ui.panel.mode.set(core.MODES["Q1"])
    ui.panel.open_lab()
    lab = ui.panel.lab_dialog
    # Seed actual short-cut methods through the same form helper.
    example, _, data = form_lab(ui, monkeypatch)
    try:
        lab.show_data(data)
        lab.classes_toggle.invoke()
        ui.root.update()
        assert str(lab.classes_host) not in [str(p) for p in lab.workspace.panes()]
        for button in [
            *lab.quick_buttons,
            lab.methods_toggle,
            lab.load_button,
            lab.stop_button,
            lab.pause_button,
            lab.hide_button,
        ]:
            assert button.winfo_ismapped()
            assert button.winfo_rootx() >= lab.winfo_rootx()
            assert (
                button.winfo_rootx() + button.winfo_width()
                <= lab.winfo_rootx() + lab.winfo_width()
            )
        lab.classes_toggle.invoke()
        ui.root.update()
        assert str(lab.classes_host) in [str(p) for p in lab.workspace.panes()]
        assert (
            lab.invoke_button.winfo_rootx() + lab.invoke_button.winfo_width()
            <= lab.action_canvas.winfo_rootx() + lab.action_canvas.winfo_width()
        )
        assert int(lab.invoke_button.grid_info()["row"]) == 1
    finally:
        example.close()
        ui.root.withdraw()


def test_refined_repeat_switches_receiver_without_a_competing_select(ui, monkeypatch):
    import copy

    dialog, _, data = form_lab(ui, monkeypatch)
    sent = []
    try:
        updated = copy.deepcopy(data)
        updated["history"] = [
            {"code": "player.move(distance=20)", "result": "None", "prediction": ""}
        ]
        dialog.show_data(updated)
        dialog.bank.selection_set("q")

        def transport(command):
            dialog.begin_action(command)
            dialog.busy = True
            sent.append(command)

        monkeypatch.setattr(dialog, "send", transport)
        dialog.repeat_last()
        assert len(sent) == 1
        assert sent[0]["action"] == "invoke" and sent[0]["handle"] == "p"
        assert dialog.bank.selection() == ("p",)
    finally:
        dialog.close()
