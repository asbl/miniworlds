from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from miniworlds.appearances.appearance import Appearance
from miniworlds.appearances.appearances_manager import AppearancesManager
from miniworlds.base.exceptions import CostumeOutOfBoundsError, MiniworldsError


class DummyAppearance(Appearance):
    def __init__(self, manager: "DummyAppearancesManager"):
        self._manager = manager
        super().__init__()

    def get_manager(self):
        return self._manager

    @property
    def world(self):
        return SimpleNamespace()


class DummyAppearancesManager(AppearancesManager):
    def create_appearance(self) -> DummyAppearance:
        return DummyAppearance(self)


class HookAwareAppearance(Appearance):
    def __init__(self):
        self.after_hook_calls = 0
        self._world = SimpleNamespace(frame=0)
        super().__init__()
        self.parent = SimpleNamespace(dirty=0, size=(1, 1))

    def get_manager(self):
        return SimpleNamespace(_is_display_initialized=False)

    @property
    def world(self):
        return self._world

    def _after_transformation_pipeline(self) -> None:
        self.after_hook_calls += 1


class TestAppearancesManager(unittest.TestCase):
    def setUp(self):
        self.manager = DummyAppearancesManager(SimpleNamespace())

    def test_add_default_appearance_keeps_has_appearance_false(self):
        appearance = self.manager.add_new_appearance(None)

        self.assertIs(appearance, self.manager.appearance)
        self.assertFalse(self.manager.has_appearance)
        self.assertEqual(len(self.manager.appearances_list), 1)

    def test_add_new_appearance_applies_manager_defaults(self):
        self.manager.is_animated = True
        self.manager.border = 3

        appearance = self.manager.add_new_appearance((255, 0, 0))

        self.assertTrue(self.manager.has_appearance)
        self.assertTrue(appearance._is_animated)
        self.assertEqual(appearance._border, 3)

    def test_next_appearance_wraps_to_first_appearance(self):
        first = self.manager.add_new_appearance((255, 0, 0))
        self.manager.add_new_appearance((0, 255, 0))
        self.manager.switch_appearance(1)

        next_appearance = self.manager.next_appearance()

        self.assertIs(next_appearance, first)

    def test_remove_last_explicit_appearance_replaces_it_with_default(self):
        explicit_appearance = self.manager.add_new_appearance((255, 0, 0))

        removed = self.manager.remove_appearance(0)

        self.assertTrue(removed)
        self.assertFalse(self.manager.has_appearance)
        self.assertEqual(len(self.manager.appearances_list), 1)
        self.assertIsNot(self.manager.appearance, explicit_appearance)

    def test_switch_appearance_raises_for_invalid_index(self):
        self.manager.add_new_appearance((255, 0, 0))

        with self.assertRaises(CostumeOutOfBoundsError):
            self.manager.switch_appearance(2)

    def test_add_new_appearances_requires_list(self):
        with self.assertRaises(MiniworldsError):
            self.manager.add_new_appearances(("not", "a", "list"))

    def test_init_display_marks_current_appearance_only_once(self):
        self.manager.add_new_appearance((255, 0, 0))
        self.manager.appearance.set_dirty = MagicMock()

        self.manager._init_display()
        self.manager._init_display()

        self.manager.appearance.set_dirty.assert_called_once_with(
            "all", self.manager.appearance.LOAD_NEW_IMAGE
        )

    def test_get_image_preserves_subclass_after_transformation_hook(self):
        appearance = HookAwareAppearance()

        appearance.get_image()

        self.assertEqual(appearance.after_hook_calls, 1)


if __name__ == "__main__":
    unittest.main()