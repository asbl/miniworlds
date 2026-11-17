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
                {"name": "amount", "required": True, "default": None},
                {"name": "label", "required": False, "default": "'x'"},
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
