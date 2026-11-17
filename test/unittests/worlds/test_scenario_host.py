"""JSON command layer for Greenfoot-style IDEs, against a real world."""
from __future__ import annotations

import json
import unittest

from miniworlds import Actor, App, World
from miniworlds.base import runtime_host
from miniworlds.tools.scenario_host import ScenarioHost


class Crab(Actor):
    def __init__(self, position=(0, 0)):
        self.food = 2
        self.note = object()
        super().__init__(position)

    def act(self):
        self.food += 1

    def eat(self, amount, label="x"):
        self.food += amount
        return f"{label}:{self.food}"

    def _hidden(self):
        pass


class Lobster(Crab):
    pass


class Ball(Actor):
    def __init__(self, position=(0, 0), radius=5, *, tag="red"):
        super().__init__(position)
        self.radius = radius
        self.tag = tag


class Keyed(Actor):
    def go(self, speed, *, turbo=False, label="x"):
        return f"{speed}:{turbo}:{label}"

    def gap(self, a=1, b=2):
        return f"{a}:{b}"


class TestScenarioHost(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(200, 200)
        self.host = ScenarioHost()
        self.host.bind_program({"Crab": Crab, "Lobster": Lobster, "x": 1})
        self.host.start(self.world.app)

    def tearDown(self):
        self.host.close()
        App.reset(unittest=True, file=__file__)

    def send(self, command, *args):
        reply = json.loads(self.host.dispatch(command, json.dumps(list(args))))
        return reply

    def test_start_pauses_before_first_frame(self):
        self.assertTrue(self.world.is_paused)
        self.assertEqual(self.send("snapshot")["value"]["world"]["frame"], 0)

    def test_status_is_a_cheap_summary(self):
        self.send("place", "Crab", 10, 10)
        status = self.send("status")["value"]
        self.assertEqual(
            (status["frame"], status["paused"], status["actors"], status["speed"]),
            (0, True, 1, 1.0),
        )

    def test_status_counts_actors_per_class(self):
        for cls in ("Crab", "Crab", "Lobster"):
            self.send("place", cls, 10, 10)
        self.assertEqual(self.send("status")["value"]["by_class"], {"Crab": 2, "Lobster": 1})

    def test_classes_list_user_classes_with_bases(self):
        classes = {c["name"]: c for c in self.send("classes")["value"]}
        self.assertEqual(set(classes), {"Crab", "Lobster"})
        self.assertEqual(classes["Lobster"]["base"], "Crab")
        self.assertEqual(classes["Crab"]["base"], "Actor")

    def test_place_pick_move_delete_roundtrip(self):
        handle = self.send("place", "Lobster", 60, 40)["value"]
        self.assertEqual(self.send("pick", 60, 40)["value"], handle)
        self.send("move", handle, 120, 90)
        self.assertIsNone(self.send("pick", 60, 40)["value"])
        self.assertEqual(self.send("pick", 120, 90)["value"], handle)
        self.send("delete", handle)
        self.assertEqual(self.send("snapshot")["value"]["actors"], [])

    def test_unknown_class_and_command_report_errors(self):
        self.assertFalse(self.send("place", "Nope", 1, 1)["ok"])
        self.assertIn("Unbekanntes", self.send("explode")["error"])

    def test_inspect_lists_public_fields_only(self):
        handle = self.send("place", "Crab", 10, 10)["value"]
        info = self.send("inspect", handle)["value"]
        self.assertEqual(info["cls"], "Crab")
        self.assertEqual(info["fields"]["food"], "2")
        self.assertEqual(info["fields"]["note"], "<object>")
        self.assertNotIn("actor_id", info["fields"])
        self.assertIn("actor_id", info["engine"])
        self.assertIn("center", info["engine"])

    def test_methods_describe_signatures_and_hide_private(self):
        handle = self.send("place", "Crab", 10, 10)["value"]
        methods = {m["name"]: m for m in self.send("methods", handle)["value"]}
        self.assertNotIn("_hidden", methods)
        self.assertEqual(
            methods["eat"]["params"],
            [
                {"name": "amount", "keyword_only": False, "required": True, "default": None},
                {"name": "label", "keyword_only": False, "required": False, "default": "'x'"},
            ],
        )
        self.assertIn("move", methods)

    def test_call_parses_literals_and_returns_result(self):
        handle = self.send("place", "Crab", 10, 10)["value"]
        reply = self.send("call", handle, "eat", ["3", "'kiwi'"])
        self.assertEqual(reply["value"], {"result": "'kiwi:5'"})
        reply = self.send("call", handle, "eat", ["1", ""])
        self.assertEqual(reply["value"], {"result": "'x:6'"})

    def test_call_validates_input(self):
        handle = self.send("place", "Crab", 10, 10)["value"]
        self.assertIn("fehlt", self.send("call", handle, "eat", [""])["error"])
        self.assertIn("nicht verfügbar", self.send("call", handle, "__init__", [])["error"])
        # arbitrary expressions are never evaluated: text stays a string
        reply = self.send("call", handle, "eat", ["1", "__import__('os')"])
        self.assertEqual(reply["value"], {"result": "\"__import__('os'):3\""})

    def test_dispatch_requires_running_program(self):
        self.host.close()
        self.assertFalse(self.send("snapshot")["ok"])

    def test_host_is_a_valid_runtime_host(self):
        runtime_host.install(self.host)
        try:
            runtime_host.poll(self.world.app)
        finally:
            runtime_host.install(None)

    def test_constructor_lists_parameters_after_the_position(self):
        self.host.bind_program({"Ball": Ball, "Crab": Crab})
        params = self.send("constructor", "Ball")["value"]
        self.assertEqual(
            [(p["name"], p["required"], p["default"], p["keyword_only"]) for p in params],
            [("radius", False, "5", False), ("tag", False, "'red'", True)],
        )
        self.assertEqual(self.send("constructor", "Crab")["value"], [])
        self.assertFalse(self.send("constructor", "Nope")["ok"])

    def test_place_passes_constructor_values(self):
        self.host.bind_program({"Ball": Ball})
        handle = self.send("place", "Ball", 30, 40, ["9", "'blue'"])["value"]
        actor = self.host.scenario.resolve(handle)
        self.assertEqual((actor.radius, actor.tag), (9, "blue"))
        handle = self.send("place", "Ball", 30, 40, ["", "'green'"])["value"]
        actor = self.host.scenario.resolve(handle)
        self.assertEqual((actor.radius, actor.tag), (5, "green"))
        self.assertFalse(self.send("place", "Ball", 1, 1, ["1", "'x'", "3"])["ok"])

    def test_call_rejects_surplus_values(self):
        handle = self.send("place", "Crab", 10, 10)["value"]
        reply = self.send("call", handle, "eat", ["1", "x", "3"])
        self.assertFalse(reply["ok"])
        self.assertIn("höchstens 2", reply["error"])

    def test_call_passes_keyword_only_and_skipped_parameters_by_name(self):
        self.host.bind_program({"Keyed": Keyed})
        handle = self.send("place", "Keyed", 10, 10)["value"]
        reply = self.send("call", handle, "go", ["3", "True", "'hi'"])
        self.assertEqual(reply["value"]["result"], "'3:True:hi'")
        # an empty optional field keeps its default, a later one is still used
        reply = self.send("call", handle, "gap", ["", "7"])
        self.assertEqual(reply["value"]["result"], "'1:7'")

    def test_modules_match_whole_path_components(self):
        import sys
        import types

        inside = types.ModuleType("gf_inside")
        inside.__file__ = "/gf_project/inside.py"
        near = types.ModuleType("gf_near")
        near.__file__ = "/gf_project2/near.py"
        sys.modules.update({"gf_inside": inside, "gf_near": near})
        try:
            self.host.bind_program({}, "/gf_project")
            spaces = list(self.host._modules())
        finally:
            del sys.modules["gf_inside"], sys.modules["gf_near"]
        self.assertIn(vars(inside), spaces)
        self.assertNotIn(vars(near), spaces)


if __name__ == "__main__":
    unittest.main()
