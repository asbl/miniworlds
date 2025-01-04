from typing import Tuple
import miniworlds.actors.actor as actor_mod
import miniworlds.actors.texts.text as text
import miniworlds.actors.widgets.widget_costume as widget_costume

class WidgetPart():
    pass

class WidgetText(text.Text, WidgetPart):
    def __init__(self, position: Tuple[float, float] = (0, 0), **kwargs):
        super().__init__(position, **kwargs)
        self.origin = kwargs.get("origin") if kwargs.get("origin") else "topleft"

    def font_by_size(self, width=None, height=None):
        pass # Do not change text (when widget is created in tiledworld)

    def resize(self):
        pass
    
class WidgetImage(actor_mod.Actor, WidgetPart):
    def __init__(self, position: Tuple[float, float] = (0, 0), **kwargs):
        super().__init__(position, **kwargs)
        self.origin = kwargs.get("origin") if kwargs.get("origin") else "topleft"

    def resize(self):
        pass