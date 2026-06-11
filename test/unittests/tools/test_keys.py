import unittest

import pygame

from miniworlds.tools import keys


class TestGetKey(unittest.TestCase):
    def test_printable_unicode_is_returned_directly(self):
        self.assertEqual(keys.get_key("a", pygame.K_a), "a")
        self.assertEqual(keys.get_key("A", pygame.K_a), "A")
        self.assertEqual(keys.get_key(" ", pygame.K_SPACE), " ")

    def test_control_characters_resolve_to_named_keys(self):
        self.assertEqual(keys.get_key("\r", pygame.K_RETURN), "RETURN")
        self.assertEqual(keys.get_key("\x1b", pygame.K_ESCAPE), "ESC")
        self.assertEqual(keys.get_key("\t", pygame.K_TAB), "TAB")
        self.assertEqual(keys.get_key("\x08", pygame.K_BACKSPACE), "BACKSPACE")

    def test_empty_unicode_falls_back_to_key_table(self):
        self.assertEqual(keys.get_key("", pygame.K_UP), "UP")
        self.assertEqual(keys.get_key("", pygame.K_RETURN), "RETURN")

    def test_modifier_combinations_keep_their_unicode(self):
        # Ctrl+Q arrives as "\x11" and is used as the quit shortcut.
        self.assertEqual(keys.get_key("\x11", pygame.K_q), "\x11")


if __name__ == "__main__":
    unittest.main()
