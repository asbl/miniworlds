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

    def draw(self, surface, bgd=None, special_flags=None):
        """Choose full redraws by scene changes, never by machine speed.

        LayeredDirty's timing heuristic penalizes slow targets even when only
        one sprite changes. Dense moving scenes, however, benefit from avoiding
        its quadratic dirty-area merging. Count only visible, clipped sprites.
        """
        # Sparse scenes should not pay for calculating every sprite's rect.
        dirty_candidates = 0
        for sprite in self._spritelist:
            if sprite.dirty:
                dirty_candidates += 1
                if dirty_candidates >= 32:
                    break
        full_redraw = dirty_candidates >= 32 and self._should_redraw_all(surface)
        self._use_update = not full_redraw
        # Older pygame-ce builds shipped with Pyodide have no special_flags
        # parameter on LayeredDirty.draw.
        if special_flags is None:
            rects = super().draw(surface, bgd)
        else:
            rects = super().draw(surface, bgd, special_flags=special_flags)
        if full_redraw:
            # LayeredDirty only consumes one-shot dirty flags in its dirty
            # path. Consume them here too so a stopped scene returns to it.
            for sprite in self._spritelist:
                if sprite.dirty == 1:
                    sprite.dirty = 0
        # Retain the existing sparse-scene regression guard. Every following
        # draw recomputes its mode from scene changes above.
        self._use_update = True
        return rects

    def _should_redraw_all(self, surface):
        clip = surface.get_clip()
        if self._clip is not None:
            clip = clip.clip(self._clip)
        visible = dirty = area = 0
        for sprite in self._spritelist:
            if sprite.visible and clip.colliderect(sprite.rect):
                visible += 1
                if sprite.dirty:
                    dirty += 1
                    rect = clip.clip(sprite.rect)
                    area += rect.width * rect.height
        return dirty >= 32 and (
            dirty >= visible * 0.6 or area >= clip.width * clip.height * 0.6
        )

    def ordered_candidates(self, candidates):
        if self._draw_order is None:
            self._draw_order = {actor: rank for rank, actor in enumerate(self.sprites())}
        ranks = self._draw_order
        return sorted((actor for actor in candidates if actor in ranks), key=ranks.__getitem__)
