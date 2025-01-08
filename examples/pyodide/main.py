import os
os.environ["SDL_WINDOWID"] = "#canvas"  # Verknüpfe SDL mit dem Canvas
import pygame
import miniworlds

# Initialisiere die Miniworlds-Welt
world = miniworlds.World()
actor = miniworlds.Actor((20, 20))
actor.color = (255, 0, 0);
world.color = (100,100,100)
world.run()