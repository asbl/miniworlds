import miniworlds.appearances.costume as costume
import miniworlds.actors.texts.text_costume as text_costume

class WidgetCostume(costume.Costume):
    pass


class WidgetPartCostume(costume.Costume):
    pass

class WidgetPartTextCostume(text_costume.TextCostume):
    def scale_to_size(self, width=None, height=None):
        pass
    """
    def _update_draw_shape(self):
        super()._update_draw_shape()
        if not self.actor.world.actors_fixed_size or (
            hasattr(self.actor, "fixed_size") and self.actor.fixed_size
        ):  # fixed size e.g. on Tiledworlds
            if self.actor.max_width != 0:
                width = min(self.get_text_width(), self.actor.max_width)
            else:
                width = self.get_text_width()
            height = self.get_text_height()
            self.actor.set_size((width, height))
        if self.actor.world.actors_fixed_size:
            self.scale_to_size()
    """