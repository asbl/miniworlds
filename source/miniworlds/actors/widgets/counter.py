import miniworlds.actors.widgets.label as mod_label


class CounterLabel(mod_label.Label):
    """A counter label contains a `description` and a `counter`. The counter starts with value 0 and can be modified with
    `add` and `sub`
    """

    def __init__(self, description, value = 0, image=None):
        self.value = value
        self.description = description
        super().__init__(str(self), image)

    def __str__(self):
        return f"{self.description} : {str(self.value)}"
    
    def add(self, value):
        self.value += value
        self.update_text()

    def sub(self, value):
        self.value -= value
        self.update_text()

    def get_value(self):
        return self.value

    def set(self, value):
        self.value = value
        self.update_text()

    def update_text(self):
        self.set_text(f"{self.description} : {str(self.value)}")
