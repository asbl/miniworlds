from __future__ import annotations

import unittest
import pymunk

import miniworlds_physics

from miniworlds import App, Circle
from miniworlds_physics import PhysicsWorld


class TestPhysicsIntegration(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_physics_package_exports_only_physics_world(self):
        self.assertIs(miniworlds_physics.PhysicsWorld, PhysicsWorld)
        self.assertEqual(miniworlds_physics.__all__, ["PhysicsWorld"])

    def test_physics_world_damping_round_trip(self):
        world = PhysicsWorld(160, 120)

        self.assertAlmostEqual(world.damping, 0.9)

        world.damping = 0.5

        self.assertAlmostEqual(world.damping, 0.5)
        self.assertAlmostEqual(world.space.damping, 0.5)

    def test_simulated_actor_moves_under_gravity(self):
        world = PhysicsWorld(160, 120)
        world.gravity = (0, 240)
        ball = Circle((80, 20), 10)
        start_y = ball.y

        for _ in range(12):
            world.simulate_all_physics_actors()

        self.assertGreater(ball.y, start_y)
        self.assertIn(ball, world.physics_actors)

    def test_removed_actor_is_removed_from_physics_actor_list(self):
        world = PhysicsWorld(160, 120)
        ball = Circle((80, 20), 10)

        self.assertIn(ball, world.physics_actors)

        ball.remove()

        self.assertNotIn(ball, world.physics_actors)

    def test_impulse_changes_velocity_and_position(self):
        world = PhysicsWorld(180, 120)
        world.gravity = (0, 0)
        ball = Circle((90, 60), 10)
        start_center = tuple(ball.center)

        ball.impulse(0, 50)

        self.assertGreater(ball.physics.body.velocity.length, 0)

        for _ in range(10):
            world.simulate_all_physics_actors()

        self.assertNotEqual(tuple(round(value, 3) for value in ball.center), start_center)

    def test_force_changes_velocity(self):
        world = PhysicsWorld(180, 120)
        world.gravity = (0, 0)
        ball = Circle((90, 60), 10)

        ball.force(0, 50)

        for _ in range(10):
            world.simulate_all_physics_actors()

        self.assertGreater(ball.physics.body.velocity.length, 0)

    def test_simulation_transition_rebuilds_body_without_moving_actor(self):
        world = PhysicsWorld(180, 120)
        world.gravity = (0, 0)
        ball = Circle((90, 60), 10)
        original_body = ball.physics.body
        original_center = tuple(ball.center)
        ball.physics.velocity_x = 120

        ball.physics.simulation = "manual"

        self.assertIsNot(ball.physics.body, original_body)
        self.assertEqual(ball.physics.body.body_type, pymunk.Body.KINEMATIC)
        self.assertEqual(tuple(ball.center), original_center)

        for _ in range(5):
            world.simulate_all_physics_actors()

        self.assertNotEqual(tuple(round(value, 3) for value in ball.center), original_center)

    def test_join_and_remove_join_update_space_constraints(self):
        world = PhysicsWorld(200, 120)
        world.gravity = (0, 0)
        anchor = Circle((70, 60), 10)
        anchor.physics.simulation = "manual"
        ball = Circle((120, 60), 10)

        anchor.physics.join(ball)

        self.assertEqual(len(world.space.constraints), 1)

        anchor.physics.remove_join(ball)

        self.assertEqual(len(world.space.constraints), 0)

    def test_removing_joined_actor_removes_space_constraints(self):
        world = PhysicsWorld(200, 120)
        world.gravity = (0, 0)
        anchor = Circle((70, 60), 10)
        ball = Circle((120, 60), 10)

        anchor.physics.join(ball)

        self.assertEqual(len(world.space.constraints), 1)

        anchor.remove()

        self.assertEqual(len(world.space.constraints), 0)
        self.assertEqual(anchor.physics.joints, [])

    def test_invalid_simulation_value_raises(self):
        world = PhysicsWorld(160, 120)
        ball = Circle((80, 60), 10)

        with self.assertRaises(ValueError):
            ball.physics.simulation = "bogus"

    def test_accuracy_must_be_positive(self):
        world = PhysicsWorld(160, 120)

        with self.assertRaises(ValueError):
            world.accuracy = 0

    def test_touching_callback_receives_other_actor_and_contact_points(self):
        world = PhysicsWorld(200, 120)
        world.gravity = (0, 0)
        left = Circle((60, 60), 10)
        right = Circle((140, 60), 10)
        collisions = []

        @left.register
        def on_touching_circle(self, other, info):
            collisions.append((other, info))

        left.physics.velocity_x = 150
        right.physics.velocity_x = -150

        for _ in range(40):
            world.simulate_all_physics_actors()
            if collisions:
                break

        self.assertTrue(collisions)
        other, info = collisions[0]
        self.assertIs(other, right)
        self.assertTrue(info)
        self.assertEqual(len(info[0]), 2)
        self.assertGreater(info[0][0], left.x)
        self.assertLess(info[0][0], right.x)
        self.assertGreater(info[0][1], 40)
        self.assertLess(info[0][1], 80)

    def test_touching_callbacks_are_dispatched_to_involved_actor_only(self):
        world = PhysicsWorld(260, 120)
        world.gravity = (0, 0)
        left = Circle((50, 60), 10)
        middle = Circle((120, 60), 10)
        uninvolved = Circle((220, 60), 10)
        left_calls = []
        uninvolved_calls = []

        @left.register
        def on_touching_circle(self, other, info):
            left_calls.append((other, info))

        @uninvolved.register
        def on_touching_circle(self, other, info):
            uninvolved_calls.append((other, info))

        left.physics.velocity_x = 180

        for _ in range(60):
            world.simulate_all_physics_actors()
            if left_calls:
                break

        self.assertTrue(left_calls)
        self.assertIs(left_calls[0][0], middle)
        self.assertEqual(uninvolved_calls, [])

    def test_removed_actor_collision_callbacks_are_unregistered(self):
        world = PhysicsWorld(200, 120)
        world.gravity = (0, 0)
        ball = Circle((60, 60), 10)

        @ball.register
        def on_touching_circle(self, other, info):
            pass

        @ball.register
        def on_separation_from_circle(self, other, info):
            pass

        self.assertEqual(len(world.touching_methods), 1)
        self.assertEqual(len(world.separate_methods), 1)

        ball.remove()

        self.assertEqual(len(world.touching_methods), 0)
        self.assertEqual(len(world.separate_methods), 0)

    def test_separation_callback_receives_other_actor(self):
        world = PhysicsWorld(200, 120)
        world.gravity = (0, 0)
        left = Circle((60, 60), 10)
        right = Circle((140, 60), 10)
        touching_calls = []
        separations = []

        @left.register
        def on_touching_circle(self, other, info):
            if not touching_calls:
                self.physics.velocity_x = -180
                other.physics.velocity_x = 180
            touching_calls.append((other, info))

        @left.register
        def on_separation_from_circle(self, other, info):
            separations.append((other, info))

        left.physics.velocity_x = 180
        right.physics.velocity_x = -180

        for _ in range(80):
            world.simulate_all_physics_actors()
            if separations:
                break

        self.assertTrue(touching_calls)
        self.assertTrue(separations)
        other, info = separations[0]
        self.assertIs(other, right)
        self.assertIsInstance(info, list)
