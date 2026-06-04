import subprocess

from miniworlds import World


world = World()
world.add_background("/home/student/Bilder/hintergrund.png")

with open("highscore.txt", "w", encoding="utf-8") as highscore:
    highscore.write("10")
