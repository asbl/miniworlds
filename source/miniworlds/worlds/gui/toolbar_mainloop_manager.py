import miniworlds.worlds.manager.mainloop_manager as mainloop_manager


class ToolbarMainloopManager(mainloop_manager.MainloopManager):

    async def update(self):
        frame_budget = await super().update()
        if self.world.is_paused:
            return frame_budget
        # Iterate over a copy: a timed widget may add or remove (timed)
        # widgets during update(), e.g. by rebuilding a toolbar menu.
        for widget in list(self.world.timed_widgets.values()):
            widget.update()
        return frame_budget
