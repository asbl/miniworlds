from unittest.mock import patch

import pygame

from miniworlds.appearances.managers.font_manager import FontManager


def test_font_reused_for_measurement_and_invalidated_on_changes():
    pygame.font.init()
    manager = FontManager(None)
    manager.font_size = 14
    with patch('pygame.font.SysFont', wraps=pygame.font.SysFont) as factory:
        font = manager.font
        manager.get_text_width('score')
        manager.get_text_height()
        assert manager.font is font
        assert factory.call_count == 1
        manager.font_size = 20
        assert manager.font is not font
        manager.font_style = 'serif'
        manager.font
        assert factory.call_count == 3
    previous = manager.font
    pygame.font.quit()
    pygame.font.init()
    assert manager.font is not previous
    previous = manager.font
    pygame.font.quit()
    assert manager.font is not previous
    assert pygame.font.get_init()
