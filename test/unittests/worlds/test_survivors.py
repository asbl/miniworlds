import asyncio
import math
from unittest.mock import patch

import pygame
import pytest

from miniworlds import Actor, ActorPool, App, World, ActionTimer
from miniworlds.appearances.managers.surface_cache import SurfaceCache


class Enemy(Actor):
    def act(self):
        self.moves = getattr(self, 'moves', 0) + 1

    def on_think(self):
        self.thoughts = getattr(self, 'thoughts', 0) + 1


class Shot(Actor):
    def on_detecting_enemy(self, enemy):
        self.hits = getattr(self, 'hits', 0) + 1


@pytest.fixture
def world():
    App.reset(unittest=True, file=__file__)
    result = World(200, 200)
    yield result
    App.reset(unittest=True, file=__file__)


def make(cls, world, position):
    actor = cls(position, world=world)
    actor.size = (12, 12)
    actor.collision_type = 'rect'
    return actor


def test_spatial_queries_match_brute_force_after_moves_groups_and_removal(world):
    enemies = [make(Enemy, world, (i * 13 - 100, i * 7 - 40)) for i in range(40)]
    for actor in enemies:
        actor.collision_group = 'enemy'
    origin = (5.5, -3.25)
    for _ in range(3):
        expected = min(enemies, key=lambda a: ((a.center[0]-origin[0])**2 +
                                              (a.center[1]-origin[1])**2, a.actor_id))
        assert world.find_nearest(origin, Enemy, collision_group='enemy') is expected
        expected_radius = {a for a in enemies if math.dist(origin, a.center) <= 70}
        assert set(world.query_radius(origin, 70, Enemy, collision_group='enemy')) == expected_radius
        expected.position = (1000, -1000)
    removed = enemies.pop()
    removed.remove()
    assert removed not in world.query_rect((-2000, -2000, 4000, 4000), Enemy)
    enemies[0].collision_group = 'loot'
    assert enemies[0] not in world.query_rect((-2000, -2000, 4000, 4000), Enemy, collision_group='enemy')
    assert world.find_nearest(enemies[0].center, collision_group='loot') is enemies[0]


def test_nearest_empty_exclude_zero_radius_and_validation(world):
    assert world.find_nearest((0, 0), Enemy) is None
    actor = make(Enemy, world, (3, 4))
    assert world.find_nearest((3, 4), Enemy, radius=0) is actor
    assert world.find_nearest((3, 4), Enemy, exclude=actor) is None
    assert world.find_nearest((0, 0), Enemy, radius=4) is None
    for radius in (-1, float('nan'), float('inf')):
        with pytest.raises(ValueError):
            world.query_radius((0, 0), radius)


def test_nearest_sparse_distant_and_zero_size_targets(world):
    enemy = make(Enemy, world, (1_000_000, -1_000_000))
    enemy.size = (0, 0)
    assert world.find_nearest((0, 0), Enemy) is enemy
    assert world.query_radius(enemy.center, 0, Enemy) == [enemy]
    assert world.find_nearest(enemy.center, Enemy, exclude=enemy) is None


def test_collision_groups_filter_before_narrow_phase_and_invalidate(world):
    enemy = make(Enemy, world, (40, 40))
    enemy.collision_group = 'enemy'
    loot = make(Actor, world, (40, 40))
    loot.collision_group = 'loot'
    shot = make(Shot, world, (40, 40))
    shot.collision_targets = {'enemy'}
    assert shot.detect_all() == [enemy]
    assert shot.detect_collisions() == [enemy]
    world._collision_manager._handle_all_collisions()
    assert shot.hits == 1
    enemy.collision_group = 'loot'
    assert shot.detect_all() == []
    world._collision_manager._handle_all_collisions()
    assert shot.hits == 1


def test_worldwide_collisions_are_explicit_and_follow_moving_targets(world):
    enemy = make(Enemy, world, (900, 900))
    shot = make(Shot, world, (900, 900))
    assert shot.detect_all() == []
    assert shot.detect_collisions(Enemy) == [enemy]
    shot.collision_worldwide = True
    world._collision_manager._handle_all_collisions()
    assert shot.hits == 1
    enemy.position = (1000, 1000)
    assert shot.detect_collisions(Enemy) == []
    world._collision_manager._handle_all_collisions()
    assert shot.hits == 1


def test_pool_preserves_managers_and_excludes_inactive_actors(world):
    pool = ActorPool(lambda: make(Enemy, world, (30, 30)), initial_size=2, max_size=2,
                     reset=lambda actor, hp=5: setattr(actor, 'hp', hp))
    assert not world.actors
    actor = pool.acquire((40, 40), hp=7)
    managers = actor.position_manager, actor.costume_manager, actor.sensor_manager
    assert actor.hp == 7
    world.event_manager.act_all()
    assert actor.moves == actor.thoughts == 1
    other = pool.acquire()
    assert pool.acquire() is None
    pool.release(actor)
    assert actor not in world.actors and actor not in world._dynamic_actors
    assert actor not in world._spatial_index
    assert actor.detect_collisions() == []
    world.event_manager.act_all()
    assert actor.moves == 1
    assert pool.acquire((60, 60)) is actor
    assert managers == (actor.position_manager, actor.costume_manager, actor.sensor_manager)
    assert actor.hp == 5
    world.event_manager.act_all()
    assert actor.moves == 2
    pool.release(other)
    with pytest.raises(ValueError):
        pool.release(other)
    pool.clear()
    assert not world.actors and not len(world._spatial_index)


def test_activation_pauses_bound_timers_and_preserves_dynamic_handlers(world):
    actor = make(Enemy, world, (30, 30))
    timer = ActionTimer(1, actor.act)
    actor.active = False
    world._mainloop._tick_timed_objects()
    assert timer.actual_time == 0
    @actor.register
    def on_message(self, message):
        self.message = message
    actor.active = True
    world._mainloop._tick_timed_objects()
    assert actor.moves == 1
    world.event_manager.handler.handle_event('message', 'hello')
    assert actor.message == 'hello'


def test_independent_think_act_and_collision_intervals(world):
    enemy = make(Enemy, world, (40, 40))
    enemy.think_interval = 3
    enemy.act_interval = 2
    shot = make(Shot, world, (40, 40))
    shot.collision_interval = 3
    for frame in range(12):
        world.frame = frame
        world.event_manager.act_all()
        world._collision_manager._handle_all_collisions()
    assert enemy.thoughts == 4
    assert enemy.moves == 6
    assert shot.hits == 4


def test_removed_target_is_not_active_and_world_transfer_restores_events(world):
    actor = make(Enemy, world, (30, 30))
    other = World(200, 200)
    actor.world = other
    assert actor.active and actor in other.actors and actor not in world.actors
    other.event_manager.act_all()
    assert actor.moves == 1
    actor.remove()
    assert not actor.active
    with pytest.raises(RuntimeError):
        actor.active = True


def test_offscreen_interval_does_not_slow_nearby_actors(world):
    enemy = make(Enemy, world, (900, 900))
    enemy.offscreen_act_interval = 4
    for frame in range(8):
        world.frame = frame
        world.event_manager.act_all()
    assert enemy.moves == 2
    enemy.position = (40, 40)
    for frame in range(8, 16):
        world.frame = frame
        world.event_manager.act_all()
    assert enemy.moves == 10


def test_actor_intervals_combine_with_world_tick_rate_without_starvation(world):
    enemy = make(Enemy, world, (40, 40))
    enemy.act_interval = 2
    enemy.think_interval = 3
    world.tick_rate = 2
    for frame in range(0, 24, 2):
        world.frame = frame
        world.event_manager.act_all()
    assert enemy.moves == 6
    assert enemy.thoughts == 4


def test_pool_release_cancels_bound_lifetime_timers(world):
    pool = ActorPool(lambda: make(Enemy, world, (30, 30)), max_size=1)
    enemy = pool.acquire()
    ActionTimer(1, enemy.act)
    pool.release(enemy)
    pool.acquire()
    world._mainloop._tick_timed_objects()
    assert not hasattr(enemy, 'moves')


def test_parent_activation_restores_only_previously_active_children(world):
    from miniworlds.actors.parent_actor import ParentActor
    parent = ParentActor((20, 20), world=world)
    first = make(Enemy, world, (20, 20))
    second = make(Enemy, world, (20, 20))
    parent.add_child(first)
    parent.add_child(second)
    second.active = False
    parent.active = False
    assert not first.active and not second.active
    parent.active = True
    assert first.active and not second.active


def test_pool_reset_failure_keeps_actor_inactive_and_available(world):
    def fail(actor):
        actor.active = True
        raise RuntimeError('reset failed')
    pool = ActorPool(lambda: make(Enemy, world, (20, 20)), reset=fail, max_size=1)
    with pytest.raises(RuntimeError, match='reset failed'):
        pool.acquire()
    assert pool.available == 1 and not pool.in_use and not world.actors


def test_pool_reset_failure_cancels_timers_before_next_lifetime(world):
    def fail(actor):
        ActionTimer(1, actor.act)
        raise RuntimeError('reset failed')
    pool = ActorPool(lambda: make(Enemy, world, (20, 20)), reset=fail, max_size=1)
    with pytest.raises(RuntimeError, match='reset failed'):
        pool.acquire()
    assert not world._timed_objects
    pool.reset = None
    actor = pool.acquire()
    world._mainloop._tick_timed_objects()
    assert not hasattr(actor, 'moves')


def test_pool_factory_cannot_reuse_an_already_owned_actor(world):
    actor = make(Enemy, world, (20, 20))
    pool = ActorPool(lambda: actor, initial_size=1)
    assert pool.acquire() is actor
    with pytest.raises(ValueError, match='new Actor'):
        pool.acquire()
    assert actor.active and pool.in_use == {actor}
    assert pool.available == 0


def test_custom_draw_group_removal_marks_overlapping_actors_dirty(world):
    actor = make(Actor, world, (40, 40))
    other = make(Actor, world, (40, 40))
    # Custom groups without LayeredDirty must retain the old erasure fallback.
    world.actors = pygame.sprite.Group(actor, other)
    other.dirty = 0
    actor.remove()
    assert other.dirty == 1
    assert actor not in world.actors


def test_registering_on_inactive_auto_static_actor_does_not_reactivate_it(world):
    actor = make(Actor, world, (40, 40))
    actor.active = False
    @actor.register
    def act(self):
        self.moved = True
    assert actor not in world.actors and actor not in world._dynamic_actors
    actor.active = True
    world.event_manager.act_all()
    assert actor.moved


def test_shared_scaling_is_reused_across_costumes(world):
    from miniworlds import Appearance
    Appearance.clear_shared_cache()
    actors = [make(Actor, world, (40, 40)), make(Actor, world, (70, 40))]
    source = pygame.Surface((8, 8), pygame.SRCALPHA)
    source.fill('red')
    for actor in actors:
        actor.costume.shared_transform_cache = True
    with patch('pygame.transform.scale', wraps=pygame.transform.scale) as scale:
        results = [actor.costume.transformations_manager.transformation_scale(source, actor.costume)
                   for actor in actors]
        assert scale.call_count == 1
        results[0].fill('blue')
        assert results[1].get_at((0, 0))[:3] == (255, 0, 0)
    Appearance.clear_shared_cache()


def test_animation_interval_is_independent_and_staggered(world):
    enemy = make(Enemy, world, (40, 40))
    enemy.costume.add_images([(255, 0, 0), (0, 255, 0)])
    enemy.costume.animate(loop=True)
    enemy.animation_interval = 3
    with patch.object(enemy.costume.image_manager, 'next_image', wraps=enemy.costume.image_manager.next_image) as step:
        for frame in range(1, 13):
            world.frame = frame
            enemy.costume.update()
        assert step.call_count == 4


def test_fast_move_clamps_preserves_heading_and_respects_blocking(world):
    actor = make(Actor, world, (20, 20))
    actor.direction = 75
    actor.move_towards_fast((23, 24), 100)
    assert actor.position == (23, 24)
    assert actor.direction == 75
    wall = make(Actor, world, (40, 40))
    wall.is_blocking = True
    actor.is_blockable = True
    actor.move_towards_fast((40, 40), 100)
    assert actor.position == (23, 24)
    assert actor.get_distance_to(wall) == math.dist(actor.center, wall.center)
    for invalid in (-1, float('nan'), float('inf')):
        with pytest.raises(ValueError):
            actor.move_towards_fast((30, 30), invalid)


def test_surface_cache_limits_bytes_and_does_not_share_mutable_results():
    cache = SurfaceCache(max_bytes=1024)
    source = pygame.Surface((8, 8), pygame.SRCALPHA)
    source.fill('red')
    render = lambda: pygame.transform.scale(source, (16, 16))
    with patch('pygame.transform.scale', wraps=pygame.transform.scale) as scale:
        first = cache.transform('scale', source, (16, 16), render)
        first.fill('blue')
        second = cache.transform('scale', source, (16, 16), render)
        assert second.get_at((0, 0))[:3] == (255, 0, 0)
        assert scale.call_count == 1
        source.fill('green')
        third = cache.transform('scale', source, (16, 16), render)
        assert third.get_at((0, 0))[:3] == (0, 255, 0)
        assert scale.call_count == 2
    assert cache.bytes_used <= 1024
