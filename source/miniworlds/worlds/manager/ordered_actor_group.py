import pygame


class OrderedActorGroup(pygame.sprite.LayeredDirty):
    """LayeredDirty with a lazily cached rank for spatial-query candidates."""

    def __init__(self):
        self._draw_order = None
        super().__init__()

    def add_internal(self, sprite, layer=None):
        self._draw_order = None
        super().add_internal(sprite, layer)

    def remove_internal(self, sprite):
        self._draw_order = None
        super().remove_internal(sprite)

    def change_layer(self, sprite, new_layer):
        self._draw_order = None
        super().change_layer(sprite, new_layer)

    def ordered_candidates(self, candidates):
        if self._draw_order is None:
            self._draw_order = {actor: rank for rank, actor in enumerate(self.sprites())}
        ranks = self._draw_order
        return sorted((actor for actor in candidates if actor in ranks), key=ranks.__getitem__)
