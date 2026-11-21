"""Opt-in simulation controls for dense scenes."""
import math


def interval_property(name):
    def get(self):
        return getattr(self, "_" + name, 1)

    def set(self, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        if value < 1:
            raise ValueError(f"{name} must be positive")
        setattr(self, "_" + name, value)
        if name == "collision_interval" and value > 1:
            self.world._collision_interval_enabled = True
    return property(get, set)


class ActorPerformance:
    act_interval = interval_property("act_interval")
    think_interval = interval_property("think_interval")
    offscreen_act_interval = interval_property("offscreen_act_interval")
    animation_interval = interval_property("animation_interval")
    collision_interval = interval_property("collision_interval")

    def on_think(self):
        """Optional AI hook, independent of movement in act()."""

    def _update_due(self, kind):
        interval = getattr(self, kind + "_interval")
        offscreen_interval = self.offscreen_act_interval
        if kind in ("act", "think") and offscreen_interval > 1:
            if not self.world.camera.is_actor_in_view(self):
                interval = max(interval, offscreen_interval)
        tick = self.world.frame
        if kind in ("act", "think"):
            tick //= self.world.tick_rate
        return interval == 1 or (tick + self.actor_id) % interval == 0

    @property
    def collision_group(self):
        """Named simulation group; independent of the sprite draw layer."""
        return getattr(self, "_collision_group", "default")

    @collision_group.setter
    def collision_group(self, value):
        if not isinstance(value, str):
            raise TypeError("collision_group must be a string")
        if value == self.collision_group:
            return
        self._collision_group = value
        index = getattr(self.world, "_spatial_index", None)
        if index is not None and self in index:
            index.reindex(self)
        self.world._collision_manager.invalidate()

    @property
    def collision_targets(self):
        """Groups this actor detects; None keeps the existing all-groups behavior."""
        return getattr(self, "_collision_targets", None)

    @collision_targets.setter
    def collision_targets(self, value):
        if value is not None:
            if isinstance(value, str):
                value = (value,)
            value = frozenset(value)
            if not all(isinstance(group, str) for group in value):
                raise TypeError("collision_targets must contain group names")
        self._collision_targets = value
        self.world._collision_manager.invalidate()

    @property
    def collision_worldwide(self):
        """Opt in to automatic collision events outside the camera too."""
        return getattr(self, "_collision_worldwide", False)

    @collision_worldwide.setter
    def collision_worldwide(self, value):
        if not isinstance(value, bool):
            raise TypeError("collision_worldwide must be bool")
        if value and getattr(self.world, "is_tiled", False):
            raise ValueError("worldwide collisions currently require a pixel World")
        self._collision_worldwide = value
        self.world._collision_manager.invalidate()

    @property
    def active(self):
        """Inactive actors retain managers/images but leave simulation and drawing."""
        return (getattr(self, "_active", True)
                and not getattr(self, "_is_deleted", False)
                and getattr(self, "_has_position_manager", True))

    @active.setter
    def active(self, value):
        if not isinstance(value, bool):
            raise TypeError("active must be bool")
        if value == self.active:
            return
        if self._is_deleted or not self._has_position_manager:
            raise RuntimeError("removed actors cannot be activated; use active=False for pooling")
        world = self.world
        if getattr(world, "is_tiled", False):
            raise ValueError("Actor activation currently requires a pixel World")
        from miniworlds.worlds.manager.world_connector import WorldConnector
        if type(world.get_world_connector(self)) is not WorldConnector:
            raise ValueError("Actor activation requires the standard pixel-world connector")
        self._active = value
        if not value:
            self._inactive_children = [(child, child.active)
                                       for child in getattr(self, "children", ())]
            for child, was_active in self._inactive_children:
                if was_active:
                    child.active = False
            self._inactive_subscriptions = []
            self._inactive_acting = self._is_acting
            self._is_acting = False
            self._inactive_subscriptions.extend(world.event_manager.unregister_instance(self))
            world.actors.remove(self)
            world._dynamic_actors.remove(self)
            world._spatial_index.remove(self)
            world._blocking_spatial_index.remove(self)
            world._blocking_actors.discard(self)
            world._mainloop.reload_costumes_queue[:] = [
                actor for actor in world._mainloop.reload_costumes_queue if actor is not self
            ]
        else:
            world.actors.add(self)
            if not self.static:
                world._dynamic_actors.add(self)
            self._is_acting = self._inactive_acting
            world.event_manager.restore_subscriptions(self._inactive_subscriptions)
            self._inactive_subscriptions = []
            world._spatial_index.update(self)
            world.get_world_connector(self).sync_blocking_registration(value=self.is_blocking)
            self._dirty = 1
            for child, was_active in getattr(self, "_inactive_children", ()):
                if was_active:
                    child.active = True
            self._inactive_children = []
        world.camera._clear_camera_cache()
        world._blocking_registry_version += 1
        world._collision_manager.invalidate()

    def detect_collisions(self, actor_type=None, *, collision_group=None):
        """Query overlapping actors anywhere in the world, applying this hitbox mode."""
        if not self.active:
            return []
        candidates = self.world.query_rect(
            self.position_manager.get_global_rect(), actor_type,
            collision_group=collision_group, exclude=self,
        )
        targets = self.collision_targets
        if targets is not None:
            candidates = [actor for actor in candidates if actor.collision_group in targets]
        if self.collision_type not in ("rect", "static-rect"):
            candidates = self.sensor_manager._detect_actor_by_collision_type(candidates, self.collision_type)
        return candidates

    def move_towards_fast(self, target, distance=1):
        """Move directly towards a target without changing facing direction.

        The step is clamped to the remaining distance. Blocking is respected.
        """
        self._ensure_real(distance, "distance")
        if not math.isfinite(distance) or distance < 0:
            raise ValueError("distance must be finite and non-negative")
        target = target.center if hasattr(target, "center") else target
        self._ensure_position_tuple(target, "target")
        if not all(math.isfinite(value) for value in target):
            raise ValueError("target must be finite")
        x, y = self.position
        dx, dy = target[0] - x, target[1] - y
        length = math.hypot(dx, dy)
        if length:
            scale = min(distance / length, 1)
            destination = (x + dx * scale, y + dy * scale)
            if not self.is_blockable or self.sensor_manager.detect_blocking_actor_at_destination(destination) is None:
                self.position_manager.set_position(destination)
        return self
