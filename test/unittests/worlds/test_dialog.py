import unittest

import pygame

from miniworlds import App, World


class TestDialog(unittest.TestCase):
    def setUp(self):
        App.reset(unittest=True, file=__file__)
        self.world = World(400, 300)
        self.surface = pygame.Surface((400, 300), pygame.SRCALPHA)

    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_ynbox_is_centered_and_returns_bool(self):
        dialog = self.world.dialog.ynbox("Continue?", "Question")

        dialog.draw(self.surface)
        self.assertEqual(dialog._panel_rect.center, self.world.camera.get_screen_rect().center)

        yes_button = dialog._button_rects[0][0]
        self.world.event_manager.handler.handle_event("mouse_left_down", yes_button.center)
        self.world.event_manager.handler.handle_event("mouse_left_up", yes_button.center)

        self.assertFalse(dialog.is_open)
        self.assertIs(dialog.value, True)
        self.assertIsNone(self.world._active_dialog)

    def test_dialog_button_can_be_clicked_with_mouse_down_and_up(self):
        dialog = self.world.dialog.ynbox("Continue?", "Question")
        dialog.draw(self.surface)
        yes_button = dialog._button_rects[0][0]

        self.world.event_manager.handler.handle_event("mouse_left_down", yes_button.center)
        self.assertTrue(dialog.is_open)

        self.world.event_manager.handler.handle_event("mouse_left_up", yes_button.center)

        self.assertFalse(dialog.is_open)
        self.assertIs(dialog.value, True)

    def test_dialog_lays_out_buttons_before_first_click_if_needed(self):
        dialog = self.world.dialog.ynbox("Continue?", "Question")

        dialog._layout(self.world.camera.get_screen_rect())
        yes_center = dialog._button_rects[0][0].center
        dialog._buttons.clear()
        self.world.event_manager.handler.handle_event("mouse_left_down", yes_center)
        self.world.event_manager.handler.handle_event("mouse_left_up", yes_center)

        self.assertFalse(dialog.is_open)
        self.assertIs(dialog.value, True)

    def test_choicebox_stacks_choices_and_returns_selected_choice(self):
        dialog = self.world.dialog.choicebox(
            "Choose a color",
            "Color",
            choices=["Red", "Green", "Blue"],
        )

        dialog.draw(self.surface)
        self.assertEqual(len(dialog._button_rects), 3)
        self.assertLess(dialog._button_rects[0][0].y, dialog._button_rects[1][0].y)

        blue_button = dialog._button_rects[2][0]
        self.world.event_manager.handler.handle_event("mouse_left_down", blue_button.center)
        self.world.event_manager.handler.handle_event("mouse_left_up", blue_button.center)

        self.assertEqual(dialog.value, "Blue")

    def test_choicebox_supports_many_choices_with_keyboard_focus_and_scrolling(self):
        choices = [f"Choice {index}" for index in range(20)]
        dialog = self.world.dialog.choicebox("Choose one", choices=choices, size=(300, 220))

        dialog.draw(self.surface)
        self.assertLess(len(dialog._button_rects), len(choices))

        for _ in range(12):
            self.world.event_manager.handler.handle_event("key_down", ["DOWN"])
        dialog.draw(self.surface)

        self.assertEqual(dialog.focus_index, 12)
        self.assertGreater(dialog.scroll_offset, 0)

        self.world.event_manager.handler.handle_event("key_down", ["RETURN"])

        self.assertEqual(dialog.value, "Choice 12")

    def test_enterbox_accepts_text_and_return_key(self):
        dialog = self.world.dialog.enterbox("Name?", "Input", default="A")

        dialog.handle_event("key_down", ["b"])
        dialog.handle_event("key_down", ["SPACE"])
        dialog.handle_event("key_down", ["c"])
        dialog.handle_event("key_down", ["BACKSPACE"])
        dialog.handle_event("key_down", ["RETURN"])

        self.assertEqual(dialog.value, "Ab ")
        self.assertFalse(dialog.is_open)

    def test_input_dialog_focus_can_cancel_with_keyboard(self):
        dialog = self.world.dialog.enterbox("Name?", default="Ada")

        self.world.event_manager.handler.handle_event("key_down", ["TAB"])
        self.world.event_manager.handler.handle_event("key_down", ["RETURN"])

        self.assertIsNone(dialog.value)
        self.assertFalse(dialog.is_open)

    def test_dialog_swallows_world_mouse_events_while_open(self):
        calls = []

        @self.world.register
        def on_mouse_left(self, position):
            calls.append(position)

        self.world.dialog.ynbox("Stop clicks?", "Modal")

        self.world.event_manager.handler.handle_event("mouse_left", (10, 10))

        self.assertEqual(calls, [])
        self.assertIsNotNone(self.world._active_dialog)

    def test_dialog_swallows_specific_key_and_wheel_events_while_open(self):
        calls = []

        @self.world.register
        def on_key_down_a(self):
            calls.append("a")

        @self.world.register
        def on_wheel_down(self, position):
            calls.append(("wheel", position))

        dialog = self.world.dialog.choicebox("Choose", choices=["A", "B", "C"])

        self.world.event_manager.handler.handle_event("key_down_a", None)
        self.world.event_manager.handler.handle_event("wheel_down", (20, 20))

        self.assertEqual(calls, [])
        self.assertEqual(dialog.focus_index, 1)

    def test_dialog_uses_camera_screen_rect_when_world_is_docked_or_moved(self):
        self.world.camera.width = 240
        self.world.camera.height = 180
        self.world.camera.screen_topleft = (90, 40)
        surface = pygame.Surface((500, 400), pygame.SRCALPHA)
        dialog = self.world.dialog.ynbox("Camera aware")

        dialog.draw(surface)

        self.assertEqual(dialog._panel_rect.center, self.world.camera.get_screen_rect().center)
        self.assertGreaterEqual(dialog._panel_rect.left, 90)
        self.assertGreaterEqual(dialog._panel_rect.top, 40)

    def test_dialog_wraps_long_words_and_clamps_to_small_viewports(self):
        self.world.camera.width = 180
        self.world.camera.height = 140
        dialog = self.world.dialog.ynbox("Supercalifragilisticexpialidocious" * 2)

        dialog.draw(self.surface)

        self.assertLessEqual(dialog._panel_rect.width, 168)
        self.assertLessEqual(dialog._panel_rect.height, 128)
        self.assertGreater(len(dialog._message_lines), 1)

    def test_opening_new_dialog_closes_existing_dialog(self):
        first_values = []
        first = self.world.dialog.ynbox("First?", callback=first_values.append)

        second = self.world.dialog.enterbox("Second?")

        self.assertFalse(first.is_open)
        self.assertEqual(first_values, [])
        self.assertIs(self.world._active_dialog, second)

    def test_user_cancel_still_notifies_callback(self):
        values = []
        dialog = self.world.dialog.ynbox("Cancel?", callback=values.append)

        dialog.handle_event("key_down", ["ESC"])

        self.assertEqual(values, [None])
        self.assertIsNone(self.world._active_dialog)

    def test_replacing_active_dialog_does_not_fire_cancel_callback(self):
        calls = []

        def open_dialog():
            self.world.dialog.ynbox("Start?", callback=lambda value: calls.append(value))

        open_dialog()
        open_dialog()

        self.assertEqual(calls, [])
        self.assertIsNotNone(self.world._active_dialog)

    def test_dialog_callback_can_open_next_dialog_immediately(self):
        opened = []

        def open_input(value):
            opened.append(("yn", value))
            self.world.dialog.enterbox("Name?", default="Ada", callback=open_choice)

        def open_choice(value):
            opened.append(("input", value))
            self.world.dialog.choicebox("Color?", choices=["Red", "Blue"], callback=open_confirm)

        def open_confirm(value):
            opened.append(("choice", value))
            self.world.dialog.ynbox("Confirm?", callback=lambda result: opened.append(("confirm", result)))

        dialog = self.world.dialog.ynbox("Start?", callback=open_input)
        dialog.draw(self.surface)
        self.world.event_manager.handler.handle_event("mouse_left_down", dialog._button_rects[0][0].center)
        self.world.event_manager.handler.handle_event("mouse_left_up", dialog._button_rects[0][0].center)

        self.assertEqual(opened, [("yn", True)])
        self.assertEqual(self.world._active_dialog.kind, "input")

        self.world.event_manager.handler.handle_event("key_down", ["RETURN"])
        self.assertEqual(opened, [("yn", True), ("input", "Ada")])
        self.assertEqual(self.world._active_dialog.kind, "choice")

        self.world.event_manager.handler.handle_event("key_down", ["DOWN"])
        self.world.event_manager.handler.handle_event("key_down", ["RETURN"])
        self.assertEqual(opened, [("yn", True), ("input", "Ada"), ("choice", "Blue")])
        self.assertEqual(self.world._active_dialog.kind, "yn")

        self.world.event_manager.handler.handle_event("key_down", ["RETURN"])
        self.assertEqual(
            opened,
            [("yn", True), ("input", "Ada"), ("choice", "Blue"), ("confirm", True)],
        )
        self.assertIsNone(self.world._active_dialog)


if __name__ == "__main__":
    unittest.main()
