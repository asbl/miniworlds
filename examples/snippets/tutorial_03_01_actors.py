import miniworlds

# Erstelle eine Welt mit den Maßen 600x300 Pixel
world = miniworlds.World(600, 300)

# Füge einen Hintergrund hinzu (zum Beispiel ein Grasbild)
world.add_background("images/grass.png")

# Erstelle einen Actor
actor = miniworlds.Actor((100, 40))     # Actor an der Position (0, 0)

# Starte die Welt, damit sie angezeigt wird
world.run()