import miniworlds.worlds.manager.mainloop_manager as mainloop_manager

class ToolbarMainloopManager(mainloop_manager.MainloopManager):

    async def update(self):
        await super().update()
        for widget in self.world.timed_widgets:
            widget.update()
    