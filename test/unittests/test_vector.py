import unittest
from math import isclose
from miniworlds.positions.vector import Vector  # ggf. Pfad anpassen
from typing import Tuple, Union

class TestVector(unittest.TestCase):

    def test_addition(self):
        v1 = Vector(1, 2)
        v2 = Vector(3, 4)
        result = v1 + v2
        self.assertEqual(result, Vector(4, 6))

        result2 = v1 + (3, 4)
        self.assertEqual(result2, Vector(4, 6))

        result3 = (3, 4) + v1
        self.assertEqual(result3, Vector(4, 6))

    def test_subtraction(self):
        v = Vector(5, 5)
        self.assertEqual(v - Vector(2, 3), Vector(3, 2))
        self.assertEqual((7, 8) - v, Vector(2, 3))

    def test_multiplication(self):
        v = Vector(2, 3)
        self.assertEqual(v * 2, Vector(4, 6))
        self.assertEqual(3 * v, Vector(6, 9))
        self.assertAlmostEqual(v * Vector(1, 1), 5.0)

    def test_length_and_normalize(self):
        v = Vector(3, 4)
        self.assertEqual(v.length(), 5.0)
        v_norm = Vector(3, 4).normalize()
        self.assertTrue(isclose(v_norm.length(), 1.0))

    def test_limit(self):
        v = Vector(10, 0)
        v.limit(5)
        self.assertTrue(isclose(v.length(), 5))
        self.assertTrue(v, (5,0))
        

    def test_distance_to(self):
        v1 = Vector(0, 0)
        v2 = Vector(3, 4)
        self.assertEqual(v1.distance_to(v2), 5.0)
        self.assertEqual(v1.distance_to((3, 4)), 5.0)

    def test_angle_to(self):
        v1 = Vector(1, 0)
        v2 = Vector(0, 1)
        angle = v1.angle_to(v2)
        self.assertTrue(isclose(angle, 90.0, abs_tol=0.001))

        self.assertTrue(isclose(Vector(1, 0).angle_to((1, 0)), 0.0))
        self.assertTrue(isclose(Vector(1, 0).angle_to((-1, 0)), 180.0))

    def test_dot_product(self):
        v1 = Vector(2, 3)
        v2 = Vector(4, -5)
        self.assertEqual(v1.dot(v2), 2 * 4 + 3 * -5)

    def test_equality(self):
        self.assertTrue(Vector(1, 2) == Vector(1.0, 2.0))
        self.assertTrue(Vector(1, 2) == (1.0, 2.0))
        self.assertFalse(Vector(1, 2) == (2.0, 1.0))

    def test_repr_and_str(self):
        v = Vector(1.12345, 2.98765)
        self.assertTrue(str(v).startswith("("))
        self.assertIn("Vector", repr(v))

if __name__ == "__main__":
    unittest.main()
