import pygame

from miniworlds.worlds.manager.ordered_actor_group import OrderedActorGroup


def test_dense_redraw_matches_dirty_rendering_and_returns_to_sparse_mode():
    adaptive = OrderedActorGroup()
    reference = pygame.sprite.LayeredDirty()
    background = pygame.Surface((160, 160))
    background.fill((13, 24, 35))
    surfaces = [background.copy(), background.copy()]
    sprites = []
    for index in range(50):
        pair = []
        for group in (adaptive, reference):
            sprite = pygame.sprite.DirtySprite(group)
            sprite.image = pygame.Surface((12, 12), pygame.SRCALPHA)
            sprite.image.fill((index * 5, 100, 200, 160))
            sprite.rect = sprite.image.get_rect(topleft=(index % 8 * 8, index // 8 * 8))
            pair.append(sprite)
        sprites.append(pair)
    reference.set_timing_threshold(1_000_000)
    for frame in range(5):
        if frame == 1:
            for pair in sprites:
                for sprite in pair:
                    sprite.rect.move_ip(4, 3)
                    sprite.dirty = 1
        if frame == 2:
            # A hidden and a removed sprite must be erased after a full draw.
            for sprite in sprites[0]:
                sprite.visible = False
            for sprite in sprites[1]:
                sprite.kill()
        if frame == 3:
            for sprite in sprites[2]:
                sprite.rect.move_ip(5, 0)
                sprite.dirty = 1
        for group, surface in zip((adaptive, reference), surfaces):
            group.clear(surface, background)
            rects = group.draw(surface)
            if group is adaptive and frame == 1:
                assert rects == [surface.get_rect()]
            if group is adaptive and frame == 4:
                assert rects == []
        assert pygame.image.tobytes(surfaces[0], 'RGBA') == pygame.image.tobytes(surfaces[1], 'RGBA')


def test_offscreen_dirty_sprites_do_not_force_full_redraw():
    group = OrderedActorGroup()
    surface = pygame.Surface((100, 100))
    background = surface.copy()
    for index in range(50):
        sprite = pygame.sprite.DirtySprite(group)
        sprite.image = pygame.Surface((5, 5))
        sprite.rect = sprite.image.get_rect(topleft=(200 + index, 200))
    group.clear(surface, background)
    assert all(rect.width * rect.height == 0 for rect in group.draw(surface))
