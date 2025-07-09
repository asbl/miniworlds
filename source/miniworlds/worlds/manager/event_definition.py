import collections
import inspect
import logging
from collections import defaultdict
from typing import Any, Optional

import miniworlds.tools.keys as keys
import miniworlds.tools.actor_class_inspection as actor_class_inspection
import miniworlds.actors.actor as actor_mod


class EventDefinition:
    """Defines all allowed events for all Objects
    """

    def __init__(self):
        self.actor_class_events = dict()
        self.actor_class_events_set = set()
        self.world_class_events = dict()
        "EventManager.world_class_events Predefined set of all world events"
        self.world_class_events_set = set()
        # Combination of actor_class_events and world_class_events
        self.class_events = dict()
        self.class_events_set = set()
        self.setup_event_list()  # setup static event set/dict

    def update(self):
        self.setup_event_list()

    def setup_event_list(self):
        specific_key_events = []
        for key, value in keys.KEYS.items():
            specific_key_events.append("on_key_down_" + value.lower())
            specific_key_events.append("on_key_pressed_" + value.lower())
            specific_key_events.append("on_key_up_" + value.lower())
        detecting_actor_methods = []
        not_detecting_actor_methods = []
        for actor_cls in actor_class_inspection.ActorClassInspection(
                actor_mod.Actor
        ).get_subclasses_for_cls():
            detecting_actor_methods.append("on_detecting_" + actor_cls.__name__.lower())
        for actor_cls in actor_class_inspection.ActorClassInspection(
                actor_mod.Actor
        ).get_subclasses_for_cls():
            not_detecting_actor_methods.append(
                "on_not_detecting_" + actor_cls.__name__.lower()
            )

        self.actor_class_events = {
            "mouse": [
                "on_mouse_left",
                "on_mouse_right",
                "on_mouse_middle",
                "on_mouse_motion",
                "on_mouse_left_down",
                "on_mouse_right_down",
                "on_mouse_left_up",
                "on_mouse_right_up",
            ],
            "clicked_on_actor": [
                "on_clicked",
                "on_clicked_left",
                "on_clicked_right",
            ],
            "mouse_over": ["on_mouse_over", "on_mouse_leave", "on_mouse_enter"],
            "key": [
                "on_key_down",
                "on_key_pressed",
                "on_key_up",
            ],
            "specific_key": specific_key_events,
            "message": ["on_message"],
            "act": ["act"],
            "setup": ["on_setup"],
            "border": [
                "on_detecting_borders",
                "on_detecting_left_border",
                "on_detecting_right_border",
                "on_detecting_top_border",
                "on_detecting_bottom_border",
            ],
            "on_the_world": [
                "on_detecting_world",
                "on_not_detecting_world",
            ],
            "on_detecting": ["on_detecting", "on_detecting_"] + detecting_actor_methods,
            "on_not_detecting": [
                                    "on_not_detecting",
                                    "on_not_detecting_",
                                ]
                                + not_detecting_actor_methods,
            "focus": ["on_focus", "on_focus_lost"],
        }

        self.world_class_events = {
            "mouse": [
                "on_mouse_left",
                "on_mouse_right",
                "on_mouse_motion",
                "on_mouse_middle",
                "on_mouse_left_down",
                "on_mouse_right_down",
                "on_mouse_left_up",
                "on_mouse_right_up",
            ],
            "key": [
                "on_key_down",
                "on_key_pressed",
                "on_key_up",
            ],
            "specific_key": specific_key_events,
            "message": ["on_message"],
            "act": ["act"],
        }
        # Generate
        self.fill_event_sets()

    def fill_event_sets(self):
        self.class_events = {**self.actor_class_events, **self.world_class_events}
        self.actor_class_events_set = set()
        # Iterate over all events in dictionary actor_class_event (see above)
        for key in self.actor_class_events.keys():
            for event in self.actor_class_events[key]:
                self.actor_class_events_set.add(event)
        self.world_class_events_set = set()
        for key in self.world_class_events.keys():
            for event in self.world_class_events[key]:
                self.world_class_events_set.add(event)
        self.class_events_set = set()
        for key in self.class_events.keys():
            for event in self.class_events[key]:
                self.class_events_set.add(event)