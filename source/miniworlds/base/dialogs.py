import easygui


class Ask:
    
    def __init__(self, world):
        self.world = world

    def choices(self, message, choices):
        reply = easygui.buttonbox(message, self.world.app.window.title, choices)
        # needed for repl.it
        self.world.app.add_display_to_repaint_areas()
        return reply

    def yn(self, message):
        reply = easygui.ynbox(message, self.world.app.window.title)
        # needed for repl.it
        self.world.app.add_display_to_repaint_areas()
        return reply

    def int(self, message):
        reply = easygui.integerbox(message, self.world.app.window.title)
        # needed for repl.it
        self.world.app.add_display_to_repaint_areas()
        return reply

    def text(self, message):
        reply = easygui.enterbox(message, self.world.app.window.title)
        # needed for repl.it
        self.world.app.add_display_to_repaint_areas()
        return reply

    def ok(self, message):
        reply = easygui.buttonbox(message, self.world.app.window.title)
        # needed for repl.it
        self.world.app.add_display_to_repaint_areas()
        return reply

    def file(self):
        reply = easygui.fileopenbox()
        # needed for repl.it
        self.world.app.add_display_to_repaint_areas()
        return reply

    def file_save(self):
        reply = easygui.filesavebox()
        return reply