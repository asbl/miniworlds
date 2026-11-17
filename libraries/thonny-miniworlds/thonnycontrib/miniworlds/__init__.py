"""Thonny entry point. miniworlds itself belongs in the execution backend."""


def load_plugin():
    from thonny import get_workbench

    from .lab_dock import MiniworldsLabView
    from .view import MiniworldsView, contextual_help

    wb = get_workbench()
    wb.set_default("miniworlds.mode", "E2")
    wb.add_view(MiniworldsView, "miniworlds", "se")
    wb.add_view(MiniworldsLabView, "miniworlds · Objektlabor", "s")
    wb.add_command(
        "miniworlds_panel",
        "tools",
        "miniworlds – Lernhilfen",
        lambda: wb.show_view("MiniworldsView"),
    )
    wb.add_command(
        "miniworlds_help",
        "help",
        "miniworlds – Hilfe zum Wort am Cursor",
        contextual_help,
        default_sequence="<Control-F1>",
    )
