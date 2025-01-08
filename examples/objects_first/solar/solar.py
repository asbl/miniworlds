from miniworlds import Circle, Vector, World
import random

def add_planet(position, color, radius):
    global planets
    planet = Circle(position)
    planet.radius = radius
    planet.color = color
    planet.border = 0
    planets.append(planet)
    @planet.register
    def act(self):
        v = Vector.from_actors(sun, planet)
        n = v.get_normal()
        n.normalize()
        self.move_vector(n)
        
world = World(400,400)
world.add_background("galaxy")
sun = Circle((200,200),10)
sun.color = (255,255,0)

planets = []
for i in range(40):
    c = random.randint(0,255)
    pos = (random.randint(0,400), random.randint(0,400))
    color = (c, c, c)
    radius = c / 40
    add_planet(pos, color, radius)
    

    
world.run()