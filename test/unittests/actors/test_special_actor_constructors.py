from __future__ import annotations

import unittest

from miniworlds import (
    Actor,
    App,
    Arc,
    Circle,
    CircleSensor,
    Ellipse,
    Line,
    Number,
    Polygon,
    Rectangle,
    Sensor,
    TextBox,
    Triangle,
    World,
)
from miniworlds.base.exceptions import LineFirstArgumentError, LineSecondArgumentError


class TestSpecialActorConstructors(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(240, 180)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_textbox_uses_position_and_creates_line_children(self):
        box = TextBox((10, 20), 120, 80, text="hello world", world=self.world)

        self.assertEqual(box.position, (10, 20))
        self.assertEqual(box.line_width, 120)
        self.assertEqual(box.lines_height, 80)
        self.assertGreater(len(box.children), 0)
        self.assertIn(box, self.world.actors)

    def test_textbox_rejects_invalid_position_and_dimensions(self):
        with self.assertRaises(TypeError):
            TextBox(10, 120, 80, world=self.world)

        with self.assertRaises(ValueError):
            TextBox((10, 20), 0, 80, world=self.world)

        with self.assertRaises(ValueError):
            TextBox((10, 20), 120, -1, world=self.world)

    def test_number_accepts_and_updates_numeric_values(self):
        number = Number((10, 20), 3, world=self.world)

        number.add(2)
        self.assertEqual(number.number, 5)

        number.sub(1.5)
        self.assertEqual(number.number, 3.5)

        number.value = 8
        self.assertEqual(number.number, 8)

    def test_number_operator_values_keep_float_precision(self):
        number = Number((10, 20), 1.5, world=self.world)
        other = Number((20, 20), 2, world=self.world)

        number + 2.5
        self.assertEqual(number.value, 4.0)

        number * other
        self.assertEqual(number.value, 8.0)

        number - 0.5
        self.assertEqual(number.value, 7.5)

    def test_number_rejects_non_numeric_values(self):
        with self.assertRaises(TypeError):
            Number((10, 20), "3", world=self.world)

        number = Number((10, 20), 3, world=self.world)

        with self.assertRaises(TypeError):
            number.set_number("4")

        with self.assertRaises(TypeError):
            number.add(True)

        with self.assertRaises(TypeError):
            number.sub("1")

        with self.assertRaises(TypeError):
            number + "1"

    def test_sensor_initializes_watch_actor_and_distance(self):
        actor = Actor((40, 50), world=self.world)

        sensor = Sensor(actor, 15, world=self.world)

        self.assertIs(sensor.watch_actor, actor)
        self.assertEqual(sensor.sensor_distance, 15)
        self.assertEqual(sensor.position, actor.position)

    def test_sensor_rejects_invalid_actor_and_distance(self):
        actor = Actor((40, 50), world=self.world)

        with self.assertRaises(TypeError):
            Sensor(object(), 10, world=self.world)

        with self.assertRaises(TypeError):
            Sensor(actor, True, world=self.world)

        with self.assertRaises(TypeError):
            Sensor(actor, "far", world=self.world)

    def test_circle_sensor_uses_distance_as_radius_and_sensor_distance(self):
        actor = Actor((40, 50), world=self.world)

        sensor = CircleSensor(actor, 25, world=self.world)

        self.assertIs(sensor.watch_actor, actor)
        self.assertEqual(sensor.sensor_distance, 25)
        self.assertEqual(sensor.radius, 25)
        self.assertEqual(sensor.position, actor.position)

    def test_circle_rejects_invalid_position_and_radius(self):
        with self.assertRaises(TypeError):
            Circle(10, 20, world=self.world)

        with self.assertRaises(TypeError):
            Circle((10, 20), True, world=self.world)

        with self.assertRaises(ValueError):
            Circle((10, 20), -1, world=self.world)

    def test_ellipse_rejects_invalid_width_and_height(self):
        with self.assertRaises(TypeError):
            Ellipse((10, 20), True, 10, world=self.world)

        with self.assertRaises(ValueError):
            Ellipse((10, 20), 10, -1, world=self.world)

    def test_arc_forwards_kwargs_and_validates_angles(self):
        arc = Arc((10, 20), 30, 40, 0, 180, world=self.world)

        self.assertIs(arc.world, self.world)
        self.assertIn(arc, self.world.actors)
        self.assertEqual(arc.start_angle, 0)
        self.assertEqual(arc.end_angle, 180)

        with self.assertRaises(TypeError):
            Arc((10, 20), 30, 40, True, 180, world=self.world)

        with self.assertRaises(TypeError):
            Arc((10, 20), 30, 40, 0, "180", world=self.world)

    def test_rectangle_rejects_invalid_width_and_height(self):
        with self.assertRaises(TypeError):
            Rectangle((10, 20), True, 10, world=self.world)

        with self.assertRaises(ValueError):
            Rectangle((10, 20), 10, -1, world=self.world)

    def test_line_rejects_invalid_points(self):
        with self.assertRaises(LineFirstArgumentError):
            Line(10, (20, 30), world=self.world)

        with self.assertRaises(LineSecondArgumentError):
            Line((10, 20), "end", world=self.world)

    def test_polygon_and_triangle_reject_invalid_points(self):
        with self.assertRaises(TypeError):
            Polygon([(0, 0), (10, 0)], world=self.world)

        with self.assertRaises(TypeError):
            Polygon([(0, 0), (10, 0), ("x", 10)], world=self.world)

        with self.assertRaises(TypeError):
            Triangle((0, 0), (10, 0), ("x", 10), world=self.world)

    def test_polygon_copies_constructor_pointlist(self):
        points = [(0, 0), (10, 0), (10, 10)]

        polygon = Polygon(points, world=self.world)
        points.append((0, 10))

        self.assertEqual(polygon.pointlist, [(0, 0), (10, 0), (10, 10)])


if __name__ == "__main__":
    unittest.main()
