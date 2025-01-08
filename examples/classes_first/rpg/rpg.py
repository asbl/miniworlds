import miniworlds

class MyWorld(miniworlds.TiledWorld):

    def on_setup(self):
        self.columns = 24
        self.rows = 14
        self.tile_size = 20
        self.add_background((255,255,255,255))
        for i in range(self.rows):
            for j in range(self.columns):
                g = Grass((j, i))
                g.static = True
        Wall((0, 4))
        Wall((1, 4))
        Wall((2, 4))
        Wall((3, 4))
        Wall((4, 4))
        Wall((5, 4))
        Wall((6, 4))
        Wall((6, 0))
        Wall((6, 1))
        Wall((6, 3))
        self.torch = Torch((10, 4))
        self.fireplace = Fireplace((10, 12))
        self.door = Door((6, 2))
        self.player = Player((8, 2))
        self.play_music("sounds/bensound-betterdays.mp3")
        self.toolbar = miniworlds.Toolbar()
        self.console = miniworlds.Console()
        self.toolbar = self.add_right(self.toolbar, size = 200)
        self.console = self.add_bottom(self.console, size = 100)

    def on_message(self, data):
        if data == "Fackel":
            fireplace = self.player.detect(Fireplace)
            if fireplace:
                self.console.newline("Du zündest die Feuerstelle an.")
                self.fireplace.burn()
                self.toolbar.remove_widget("Fackel")


class Player(miniworlds.Actor):

    def on_setup(self):
        self.add_costume("images/knight.png")
        self.costume.is_rotatable = False
        self.inventory = []

    def on_key_down_w(self):
        self.move_up()

    def on_key_down_s(self):
        self.move_down()

    def on_key_down_a(self):
        self.move_left()

    def on_key_down_d(self):
        self.move_right()

    def on_detecting_torch(self, torch):
        reply = self.ask.choices("Du findest eine Fackel. Möchtest du sie aufheben?",["Ja", "Nein"])
        if reply == "Ja":
            self.inventory.append("Torch")
            self.world.torch.remove()
            self.world.console.newline("Du hebst die Fackel auf.")
        button = miniworlds.Button("Fackel", "images/torch.png")
        button.world = self.world.toolbar

    def on_detecting_wall(self, wall):
        self.move_back()

    def on_detecting_door(self, door):
        if door.closed:
            self.move_back()           
            message = "Die Tür ist geschlossen... möchtest du sie öffnen"
            reply = self.ask.choices(message, ["Ja", "Nein"])
            if reply == "Ja":
                self.world.door.open()
                self.world.console.newline("Du hast das Tor geöffnet.")
        else:
            self.world.console.newline("Du gehst durch das Tor...")

class Wall(miniworlds.Actor):

    def on_setup(self):
        self.add_costume("images/wall.png")
        self.static = True


class Grass(miniworlds.Actor):

    def on_setup(self):
        self.add_costume("images/grass.png")
        self.static = True

class Torch(miniworlds.Actor):

    def on_setup(self):
        self.add_costume("images/torch.png")


class Fireplace(miniworlds.Actor):

    def on_setup(self):
        self.add_costume("images/fireplace_0.png")
        self.costume_burned = self.add_costume(["images/fireplace_1.png", "images/fireplace_2.png"])
        self.burning = False

    def burn(self):
        if not self.burning:
            self.world.play_sound("sounds/fireplace.wav")
            self.switch_costume(self.costume_burned)
            self.costume.is_animated = True


class Door(miniworlds.Actor):

    def on_setup(self):
        self.add_costume("images/door_closed.png")
        self.costume_open = self.add_costume("images/door_open.png")
        self.closed = True

    def open(self):
        if not self.closed:
            self.switch_costume(self.costume_open)
            #self.world.play_sound("sounds/olddoor.wav")
            self.closed = False


myworld = MyWorld()
myworld.run()
