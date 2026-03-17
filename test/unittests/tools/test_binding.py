import unittest

from miniworlds.tools.binding import bind_method


class Receiver:
    def __init__(self, value):
        self.value = value

    def describe(self, prefix=""):
        return f"{prefix}{self.value}"


class TestBinding(unittest.TestCase):
    def test_bind_method_attaches_bound_method_to_instance(self):
        receiver = Receiver("ready")

        bound = bind_method(receiver, Receiver.describe)

        self.assertIs(receiver.describe, bound)
        self.assertEqual(bound.__self__, receiver)

    def test_bound_method_uses_instance_state(self):
        receiver = Receiver("rocket")

        bind_method(receiver, Receiver.describe)

        self.assertEqual(receiver.describe("launch-"), "launch-rocket")