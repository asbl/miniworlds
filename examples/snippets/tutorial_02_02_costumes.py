from miniworlds import World, Actor
# Erstelle eine Welt mit den Maßen 600x300
world = World(600, 300)

# Füge einen Hintergrund hinzu
world.add_background("images/grass.png")

# Erstelle den ersten Actor an der Position (100, 20) und füge ein Kostüm hinzu
actor2 = Actor((100, 20))
actor2.add_costume("images/knight.png")  # "knight.png" als Kostüm

# Starte die Welt, damit die Actors sichtbar sind
world.run()