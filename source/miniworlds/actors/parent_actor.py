from typing import List
import pygame
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.world as world_mod

class ParentActor(actor_mod.Actor):
    """A parent Actor is an actor which can contain one ore multiple children.
    """
    def __init__(self, position, children=[], *args, **kwargs):
        super().__init__(position, *args, **kwargs)
        self._visible: bool = True
        self._layer: int = 0
        self.children: "pygame.sprite.LayeredDirty()" =  pygame.sprite.LayeredDirty(children)

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value: bool):
        self._visible = value
        for child in self.children:
            child.visible = value
        self.dirty = 1

    def add_child(self, actor: "actor_mod.Actor"):
        self.children.add(actor)
        actor._parent = self
        actor.layer = self.layer + 1
        
    @property
    def layer(self):
        return self._layer

    @layer.setter
    def layer(self, value: int):
        self.set_layer(value)

    def set_layer(self, value):
        actual_layer = self.world.actors.get_layer_of_sprite(self)
        self._layer = value
        if self in self.world.actors.get_sprites_from_layer(actual_layer):
            self.world.actors.change_layer(self, value)
        for child in self.children:
            child.layer = self.layer + 1
        self.dirty = 1

    def set_world(self, new_world : "world_mod.World") -> "actor_mod.Actor":
        super().set_world(new_world)
        for child in self.children:
            child.set_world(new_world)

    def reset_costumes(self):
        super().reset_costumes()
        for child in self.children:
            child.reset_costumes()
            
    def before_remove(self):
        for child in self.children:
            child.remove(kill = False)
        