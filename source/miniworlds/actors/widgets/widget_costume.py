import miniworlds.appearances.costume as costume
import miniworlds.actors.texts.text_costume as text_costume

class WidgetCostume(costume.Costume):
    pass


class WidgetPartCostume(costume.Costume):
    pass

class WidgetPartTextCostume(text_costume.TextCostume):
    def scale_to_size(self, width=None, height=None):
        pass
