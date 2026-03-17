import unittest
from unittest.mock import patch

from miniworlds.tools.actor_class_inspection import ActorClassInspection
from miniworlds.worlds.manager.event_definition import EventDefinition


class TestEventDefinition(unittest.TestCase):
    def test_update_skips_rebuild_when_actor_classes_are_unchanged(self):
        definition = EventDefinition()

        with patch.object(EventDefinition, "setup_event_list", wraps=definition.setup_event_list) as setup_mock:
            changed = definition.update()

        self.assertFalse(changed)
        setup_mock.assert_not_called()

    def test_update_rebuilds_when_new_actor_subclass_exists(self):
        definition = EventDefinition()
        existing_classes = ActorClassInspection.get_all_actor_classes()
        fake_actor_class = type("TemporaryActor", (), {})

        with patch.object(
            ActorClassInspection,
            "get_subclasses_for_cls",
            return_value=set(existing_classes).union({fake_actor_class}),
        ):
            with patch.object(EventDefinition, "setup_event_list", wraps=definition.setup_event_list) as setup_mock:
                changed = definition.update()

        self.assertTrue(changed)
        setup_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()