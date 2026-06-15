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

        dialog.handle_event("text_input", "b")
        dialog.handle_event("text_input", " ")
        dialog.handle_event("text_input", "c")
        dialog.handle_event("key_down", ["BACKSPACE"])
        dialog.handle_event("key_down", ["RETURN"])

        self.assertEqual(dialog.value, "Ab ")
        self.assertFalse(dialog.is_open)

    def test_enterbox_edits_at_cursor_position(self):
        dialog = self.world.dialog.enterbox("Name?", default="Ada")

        dialog.handle_event("key_down", ["LEFT"])
        dialog.handle_event("key_down", ["LEFT"])
        dialog.handle_event("text_input", "n")
        dialog.handle_event("key_down", ["HOME"])
        dialog.handle_event("text_input", ">")
        dialog.handle_event("key_down", ["DELETE"])
        dialog.handle_event("key_down", ["END"])
        dialog.handle_event("text_input", "!")
        dialog.handle_event("key_down", ["RETURN"])

        # "Ada" -> LEFT LEFT, insert "n" at 1 -> "Anda"; HOME, insert ">" -> ">Anda";
        # DELETE removes the "A" -> ">nda"; END, insert "!" -> ">nda!".
        self.assertEqual(dialog.value, ">nda!")

    def test_enterbox_accepts_composed_unicode_text(self):
        dialog = self.world.dialog.enterbox("Name?", default="")

        dialog.handle_event("text_input", "ä")
        dialog.handle_event("text_input", "ß")
        dialog.handle_event("key_down", ["RETURN"])

        self.assertEqual(dialog.value, "äß")

    def test_msgbox_confirms_with_true_and_cancels_with_none(self):
        values = []
        dialog = self.world.dialog.msgbox("Done!", "Info", callback=values.append)

        dialog.draw(self.surface)
        self.assertEqual(len(dialog._button_rects), 1)
        self.assertEqual(dialog._button_rects[0][1], "OK")

        ok_button = dialog._button_rects[0][0]
        self.world.event_manager.handler.handle_event("mouse_left_down", ok_button.center)
        self.world.event_manager.handler.handle_event("mouse_left_up", ok_button.center)

        self.assertIs(dialog.value, True)
        self.assertEqual(values, [True])

        cancelled = self.world.dialog.alert("Again", button="Weiter")
        self.assertEqual(cancelled.choices, ["Weiter"])
        cancelled.handle_event("key_down", ["ESC"])
        self.assertIsNone(cancelled.value)

    def test_invalid_dialog_kind_raises_value_error(self):
        from miniworlds.worlds.dialog import Dialog

        with self.assertRaises(ValueError):
            Dialog(self.world, "msg", kind="bogus")
        with self.assertRaises(ValueError):
            Dialog(self.world, "msg", choices=("only one",), kind="yn")
        with self.assertRaises(ValueError):
            Dialog(self.world, "msg", choices=(), kind="choice")

    def test_callback_exception_does_not_propagate_and_dialog_closes(self):
        def explode(value):
            raise RuntimeError("boom")

        dialog = self.world.dialog.ynbox("Continue?", callback=explode)

        with self.assertLogs("miniworlds.worlds.dialog", level="ERROR"):
            dialog.handle_event("key_down", ["RETURN"])

        self.assertFalse(dialog.is_open)
        self.assertIsNone(self.world._active_dialog)

    def test_pause_stops_world_while_dialog_is_open_and_restores_state(self):
        self.assertTrue(self.world.is_running)
        dialog = self.world.dialog.ynbox("Pause?", pause=True)

        self.assertFalse(self.world.is_running)
        dialog.handle_event("key_down", ["RETURN"])
        self.assertTrue(self.world.is_running)

        self.world.is_running = False
        dialog = self.world.dialog.ynbox("Still stopped?", pause=True)
        dialog.handle_event("key_down", ["ESC"])
        self.assertFalse(self.world.is_running)

    def test_replacing_paused_dialog_keeps_world_paused(self):
        self.world.dialog.ynbox("First?", pause=True)
        second = self.world.dialog.enterbox("Second?", pause=True)

        self.assertFalse(self.world.is_running)
        second.handle_event("key_down", ["ESC"])
        self.assertTrue(self.world.is_running)

    def test_replacing_dialog_hands_over_press_suppression(self):
        first = self.world.dialog.ynbox("First?")
        first._suppress_active_press = True

        second = self.world.dialog.choicebox("Second?", choices=["A", "B"])

        self.assertTrue(second._suppress_active_press)
        second.draw(self.surface)
        target = second._button_rects[0][0].center
        self.world.event_manager.handler.handle_event("mouse_left_down", target)
        self.world.event_manager.handler.handle_event("mouse_left_up", target)
        self.assertTrue(second.is_open)

        self.world.event_manager.handler.handle_event("mouse_left_down", target)
        self.world.event_manager.handler.handle_event("mouse_left_up", target)
        self.assertEqual(second.value, "A")

    def test_long_input_text_is_clipped_to_input_field(self):
        dialog = self.world.dialog.enterbox("Name?", default="x" * 200)

        dialog.draw(self.surface)

        text_width = dialog._font.size(dialog.input_text)[0]
        self.assertGreater(text_width, dialog._input_rect.width)
        # The clip region must be restored after drawing the input field.
        self.assertEqual(self.surface.get_clip(), self.surface.get_rect())

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
