from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import pygame


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DialogButton:
    rect: pygame.Rect
    label: str
    value: Any
    index: int


class Overlay:
    """Modal overlay drawn over a world's camera viewport."""

    blocks_input = True

    def __init__(
        self,
        world,
        *,
        darken: bool = True,
        overlay_color: tuple[int, int, int, int] = (0, 0, 0, 130),
    ) -> None:
        self.world = world
        self.darken = darken
        self.overlay_color = overlay_color
        self.is_open = True
        self._overlay_surface: pygame.Surface | None = None

    @property
    def viewport_rect(self) -> pygame.Rect:
        return self.world.camera.get_screen_rect()

    def close(self, value=None, notify: bool = True) -> None:
        del notify
        self.is_open = False
        if getattr(self.world, "_active_dialog", None) is self:
            self.world._active_dialog = None

    def draw(self, target_surface: pygame.Surface) -> None:
        if not self.is_open:
            return
        if self.darken:
            world_rect = self.viewport_rect
            if self._overlay_surface is None or self._overlay_surface.get_size() != world_rect.size:
                self._overlay_surface = pygame.Surface(world_rect.size, pygame.SRCALPHA)
                self._overlay_surface.fill(self.overlay_color)
            target_surface.blit(self._overlay_surface, world_rect.topleft)

    def handle_event(self, event: str, data) -> bool:
        if not self.is_open or not self.blocks_input:
            return False
        return (
            event.startswith("mouse_")
            or event.startswith("key_")
            or event.startswith("wheel_")
            or event.startswith("text_")
        )


class Dialog(Overlay):
    """Modal dialog drawn over a world.

    Dialogs are event-loop friendly: opening a dialog returns immediately. The
    selected value is stored in ``value`` and can also be delivered through
    ``callback``.
    """

    _INPUT_OK = object()
    _BUTTON_HEIGHT = 32
    _BUTTON_GAP = 8
    _PADDING = 20
    _MIN_WIDTH = 260
    _MAX_WIDTH = 500
    _VALID_KINDS = ("yn", "choice", "input", "msg")
    _KEY_REPEAT_DELAY = 400
    _KEY_REPEAT_INTERVAL = 40

    _font_cache: dict[int, pygame.font.Font] = {}

    def __init__(
        self,
        world,
        message: str = "",
        title: str = "",
        choices: Sequence[str] | None = None,
        kind: str = "choice",
        default: str = "",
        callback: Callable[[Any], None] | None = None,
        position: tuple[int, int] | None = None,
        size: tuple[int, int] | None = None,
        darken: bool = True,
        overlay_color: tuple[int, int, int, int] = (0, 0, 0, 130),
        pause: bool = False,
    ) -> None:
        super().__init__(world, darken=darken, overlay_color=overlay_color)
        if kind not in self._VALID_KINDS:
            raise ValueError(
                f"Unknown dialog kind {kind!r}. Valid kinds are: {', '.join(self._VALID_KINDS)}"
            )
        self.message = str(message)
        self.title = str(title)
        self.choices = [str(choice) for choice in (choices or [])]
        if kind == "yn" and len(self.choices) != 2:
            raise ValueError("A yes/no dialog needs exactly two choices")
        if kind == "choice" and not self.choices:
            raise ValueError("A choice dialog needs at least one choice")
        if kind == "msg" and not self.choices:
            self.choices = ["OK"]
        self.kind = kind
        self.input_text = str(default)
        self.cursor_pos = len(self.input_text)
        self.callback = callback
        self.position = position
        self.requested_size = size
        self.pause = pause
        self.value = None
        self.focus_index = 0
        self.scroll_offset = 0
        self._was_running: bool | None = None
        self._previous_key_repeat: tuple[int, int] | None = None
        self._buttons: list[DialogButton] = []
        self._input_rect = pygame.Rect(0, 0, 0, 0)
        self._panel_rect = pygame.Rect(0, 0, 0, 0)
        self._choice_area_rect = pygame.Rect(0, 0, 0, 0)
        self._message_lines: list[str] = []
        self._choice_buttons_visible = 0
        self._pressed_button_index: int | None = None
        # True while the mouse press that was already active when the dialog
        # opened is still held; that press must not select a dialog button.
        self._suppress_active_press = False
        self._layout_cache_key: tuple | None = None
        self._font = self._get_font(22)
        self._title_font = self._get_font(28)
        self._button_font = self._get_font(22)

    @classmethod
    def _get_font(cls, font_size: int) -> pygame.font.Font:
        font = cls._font_cache.get(font_size)
        if font is None:
            font = pygame.font.Font(None, font_size)
            cls._font_cache[font_size] = font
        return font

    @property
    def _button_rects(self) -> list[tuple[pygame.Rect, str, Any]]:
        return [(button.rect, button.label, button.value) for button in self._buttons]

    def on_opened(self) -> None:
        """Called by DialogService once the dialog became the active dialog."""
        if self.pause:
            self._was_running = self.world.is_running
            self.world.is_running = False
        if self.kind == "input":
            self._enable_text_entry()

    def close(self, value=None, notify: bool = True) -> None:
        self.value = value
        if self.pause and self._was_running is not None:
            self.world.is_running = self._was_running
            self._was_running = None
        if self.kind == "input":
            self._disable_text_entry()
        super().close(value, notify=notify)
        if notify and self.callback:
            try:
                self.callback(value)
            except Exception:
                logger.exception(
                    "Error in dialog callback for dialog %r",
                    self.title or self.message,
                )

    def _enable_text_entry(self) -> None:
        try:
            self._previous_key_repeat = pygame.key.get_repeat()
            pygame.key.set_repeat(self._KEY_REPEAT_DELAY, self._KEY_REPEAT_INTERVAL)
            pygame.key.start_text_input()
        except pygame.error:
            self._previous_key_repeat = None

    def _disable_text_entry(self) -> None:
        if self._previous_key_repeat is None:
            return
        try:
            pygame.key.set_repeat(*self._previous_key_repeat)
        except pygame.error:
            pass
        self._previous_key_repeat = None

    def draw(self, target_surface: pygame.Surface) -> None:
        if not self.is_open:
            return
        super().draw(target_surface)
        panel_rect = self._layout(self.viewport_rect)
        pygame.draw.rect(target_surface, (245, 247, 250), panel_rect, border_radius=8)
        pygame.draw.rect(target_surface, (52, 62, 74), panel_rect, 2, border_radius=8)
        self._draw_title_and_message(target_surface)
        if self.kind == "input":
            self._draw_input(target_surface)
        if self.kind == "choice":
            self._draw_choice_area(target_surface)
        for button in self._buttons:
            self._draw_button(target_surface, button)

    def handle_event(self, event: str, data) -> bool:
        if not super().handle_event(event, data):
            return False
        if event == "mouse_left_down":
            self._handle_mouse_left_down(data)
        elif event == "mouse_left_up":
            self._handle_mouse_left_up(data)
        elif event == "key_down":
            self._handle_key_down(data or [])
        elif event == "text_input":
            self._handle_text_input(data)
        elif event == "wheel_up":
            self._move_focus(-1)
        elif event == "wheel_down":
            self._move_focus(1)
        return True

    def _handle_mouse_left_down(self, pos) -> None:
        if self._suppress_active_press:
            return
        button = self._button_at(pos)
        self._pressed_button_index = button.index if button else None
        if button:
            self.focus_index = button.index

    def _handle_mouse_left_up(self, pos) -> None:
        if self._suppress_active_press:
            self._suppress_active_press = False
            self._pressed_button_index = None
            return
        button = self._button_at(pos)
        pressed_index = self._pressed_button_index
        self._pressed_button_index = None
        if button is None or button.index != pressed_index:
            return
        self.focus_index = button.index
        self._choose_focused_button()

    def _button_at(self, pos) -> DialogButton | None:
        if pos is None:
            return None
        self._ensure_layout()
        for button in self._buttons:
            if button.rect.collidepoint(pos):
                return button
        return None

    def _ensure_layout(self) -> None:
        if not self._buttons:
            # Force a rebuild: the cache may match the viewport even though the
            # buttons were cleared (e.g. between layout and the first click).
            self._layout_cache_key = None
            self._layout(self.viewport_rect)

    def _handle_key_down(self, keys: Sequence[str]) -> None:
        if "ESC" in keys:
            self.close(None)
            return
        if "RETURN" in keys or "ENTER" in keys:
            if self.kind == "input" and self.focus_index == 0:
                self.close(self.input_text)
            else:
                self._choose_focused_button()
            return
        if self.kind == "input" and self._handle_input_key(keys):
            return
        if "TAB" in keys or "DOWN" in keys or "RIGHT" in keys:
            self._move_focus(1)
            return
        if "UP" in keys or "LEFT" in keys:
            self._move_focus(-1)
            return

    def _handle_input_key(self, keys: Sequence[str]) -> bool:
        """Handles editing keys for input dialogs. Returns True if handled."""
        if "BACKSPACE" in keys:
            if self.cursor_pos > 0:
                self.input_text = (
                    self.input_text[: self.cursor_pos - 1] + self.input_text[self.cursor_pos:]
                )
                self.cursor_pos -= 1
            return True
        if "DELETE" in keys:
            self.input_text = (
                self.input_text[: self.cursor_pos] + self.input_text[self.cursor_pos + 1:]
            )
            return True
        if "LEFT" in keys:
            self.cursor_pos = max(0, self.cursor_pos - 1)
            return True
        if "RIGHT" in keys:
            self.cursor_pos = min(len(self.input_text), self.cursor_pos + 1)
            return True
        if "HOME" in keys or "home" in keys:
            self.cursor_pos = 0
            return True
        if "END" in keys or "end" in keys:
            self.cursor_pos = len(self.input_text)
            return True
        return False

    def _handle_text_input(self, text) -> None:
        if self.kind != "input" or not text:
            return
        text = str(text)
        self.input_text = (
            self.input_text[: self.cursor_pos] + text + self.input_text[self.cursor_pos:]
        )
        self.cursor_pos += len(text)

    def _move_focus(self, step: int) -> None:
        count = self._button_count()
        if count == 0:
            return
        self.focus_index = (self.focus_index + step) % count
        self._ensure_focus_visible()

    def _choose_focused_button(self) -> None:
        if self.kind == "choice":
            if 0 <= self.focus_index < len(self.choices):
                self.close(self.choices[self.focus_index])
            return
        if self.kind == "yn":
            self.close(self.focus_index == 0)
            return
        if self.kind == "msg":
            self.close(True)
            return
        if self.kind == "input":
            self.close(self.input_text if self.focus_index == 0 else None)

    def _button_count(self) -> int:
        if self.kind == "choice":
            return len(self.choices)
        if self.kind == "msg":
            return 1
        return 2

    def _ensure_focus_visible(self) -> None:
        if self.kind != "choice" or self._choice_buttons_visible <= 0:
            return
        if self.focus_index < self.scroll_offset:
            self.scroll_offset = self.focus_index
        elif self.focus_index >= self.scroll_offset + self._choice_buttons_visible:
            self.scroll_offset = self.focus_index - self._choice_buttons_visible + 1
        max_offset = max(0, len(self.choices) - self._choice_buttons_visible)
        self.scroll_offset = max(0, min(self.scroll_offset, max_offset))

    def _layout(self, world_rect: pygame.Rect) -> pygame.Rect:
        cache_key = (
            world_rect.x,
            world_rect.y,
            world_rect.width,
            world_rect.height,
            self.scroll_offset,
        )
        if cache_key == self._layout_cache_key:
            return self._panel_rect
        width, height = self.requested_size or self._default_size(world_rect)
        width = min(width, max(140, world_rect.width - 24))
        height = min(height, max(120, world_rect.height - 24))
        if self.position is None:
            x = world_rect.x + (world_rect.width - width) // 2
            y = world_rect.y + (world_rect.height - height) // 2
        else:
            x = world_rect.x + self.position[0]
            y = world_rect.y + self.position[1]
            x = max(world_rect.x + 8, min(x, world_rect.right - width - 8))
            y = max(world_rect.y + 8, min(y, world_rect.bottom - height - 8))
        self._panel_rect = pygame.Rect(x, y, width, height)
        self._layout_content()
        # _layout_content may clamp scroll_offset; cache the final value.
        self._layout_cache_key = cache_key[:4] + (self.scroll_offset,)
        return self._panel_rect

    def _default_size(self, world_rect: pygame.Rect) -> tuple[int, int]:
        width = min(max(self._MIN_WIDTH, int(world_rect.width * 0.68)), self._MAX_WIDTH)
        wrap_width = width - 2 * self._PADDING
        message_lines = self._wrap_text(self.message, wrap_width, self._font)
        title_height = self._title_font.get_height() + 12 if self.title else 0
        message_height = len(message_lines) * (self._font.get_height() + 4)
        controls_height = self._controls_height(world_rect)
        control_gap = 10 if self.kind in {"choice", "input"} else 0
        height = self._PADDING * 2 + title_height + message_height + control_gap + controls_height
        return width, max(150, height)

    def _controls_height(self, world_rect: pygame.Rect) -> int:
        if self.kind == "input":
            return 88
        if self.kind == "choice":
            visible_rows = min(max(1, len(self.choices)), self._max_choice_rows(world_rect))
            return visible_rows * self._BUTTON_HEIGHT + max(0, visible_rows - 1) * self._BUTTON_GAP
        return self._BUTTON_HEIGHT

    def _max_choice_rows(self, world_rect: pygame.Rect) -> int:
        return max(1, min(8, (world_rect.height - 150) // (self._BUTTON_HEIGHT + self._BUTTON_GAP)))

    def _layout_content(self) -> None:
        panel = self._panel_rect
        self._buttons.clear()
        y = panel.y + self._PADDING
        if self.title:
            y += self._title_font.get_height() + 12
        self._message_lines = self._wrap_text(self.message, panel.width - 2 * self._PADDING, self._font)
        y += len(self._message_lines) * (self._font.get_height() + 4)
        if self.kind == "input":
            self._layout_input_controls(panel)
        elif self.kind == "choice":
            self._layout_choice_controls(panel, y + 10)
        elif self.kind == "msg":
            self._layout_bottom_buttons([(self.choices[0], True)])
        else:
            self._layout_bottom_buttons([(self.choices[0], True), (self.choices[1], False)])

    def _layout_input_controls(self, panel: pygame.Rect) -> None:
        self._input_rect = pygame.Rect(panel.x + self._PADDING, panel.bottom - 88, panel.width - 2 * self._PADDING, 34)
        self._layout_bottom_buttons([("OK", self._INPUT_OK), ("Cancel", None)])

    def _layout_choice_controls(self, panel: pygame.Rect, top: int) -> None:
        available_height = max(
            self._BUTTON_HEIGHT,
            panel.bottom - self._PADDING - top,
        )
        self._choice_buttons_visible = max(
            1,
            min(
                len(self.choices),
                (available_height + self._BUTTON_GAP) // (self._BUTTON_HEIGHT + self._BUTTON_GAP),
            ),
        )
        self._ensure_focus_visible()
        button_width = panel.width - 2 * self._PADDING
        height = (
            self._choice_buttons_visible * self._BUTTON_HEIGHT
            + max(0, self._choice_buttons_visible - 1) * self._BUTTON_GAP
        )
        self._choice_area_rect = pygame.Rect(panel.x + self._PADDING, top, button_width, height)
        y = top
        for index in range(self.scroll_offset, self.scroll_offset + self._choice_buttons_visible):
            if index >= len(self.choices):
                break
            self._buttons.append(
                DialogButton(
                    pygame.Rect(panel.x + self._PADDING, y, button_width, self._BUTTON_HEIGHT),
                    self.choices[index],
                    self.choices[index],
                    index,
                )
            )
            y += self._BUTTON_HEIGHT + self._BUTTON_GAP

    def _layout_bottom_buttons(self, buttons: Sequence[tuple[str, Any]]) -> None:
        panel = self._panel_rect
        button_width = min(130, max(76, (panel.width - 2 * self._PADDING - self._BUTTON_GAP) // 2))
        total_width = len(buttons) * button_width + max(0, len(buttons) - 1) * self._BUTTON_GAP
        x = panel.x + (panel.width - total_width) // 2
        y = panel.bottom - self._PADDING - self._BUTTON_HEIGHT
        for index, (label, value) in enumerate(buttons):
            self._buttons.append(
                DialogButton(pygame.Rect(x, y, button_width, self._BUTTON_HEIGHT), label, value, index)
            )
            x += button_width + self._BUTTON_GAP

    def _draw_title_and_message(self, target_surface: pygame.Surface) -> None:
        y = self._panel_rect.y + self._PADDING
        if self.title:
            title_surface = self._title_font.render(self.title, True, (25, 30, 36))
            target_surface.blit(title_surface, (self._panel_rect.x + self._PADDING, y))
            y += title_surface.get_height() + 12
        for line in self._message_lines:
            line_surface = self._font.render(line, True, (25, 30, 36))
            target_surface.blit(line_surface, (self._panel_rect.x + self._PADDING, y))
            y += line_surface.get_height() + 4

    def _draw_choice_area(self, target_surface: pygame.Surface) -> None:
        if len(self.choices) <= self._choice_buttons_visible:
            return
        track = pygame.Rect(self._choice_area_rect.right - 4, self._choice_area_rect.y, 4, self._choice_area_rect.height)
        pygame.draw.rect(target_surface, (211, 218, 226), track, border_radius=2)
        thumb_height = max(12, int(track.height * self._choice_buttons_visible / len(self.choices)))
        max_offset = max(1, len(self.choices) - self._choice_buttons_visible)
        thumb_y = track.y + int((track.height - thumb_height) * self.scroll_offset / max_offset)
        pygame.draw.rect(target_surface, (87, 98, 111), (track.x, thumb_y, track.width, thumb_height), border_radius=2)

    def _draw_input(self, target_surface: pygame.Surface) -> None:
        pygame.draw.rect(target_surface, (255, 255, 255), self._input_rect, border_radius=4)
        pygame.draw.rect(target_surface, (63, 93, 132), self._input_rect, 2, border_radius=4)
        inner = self._input_rect.inflate(-12, -8)
        self.cursor_pos = max(0, min(self.cursor_pos, len(self.input_text)))
        cursor_x = self._font.size(self.input_text[: self.cursor_pos])[0]
        text_surface = self._font.render(self.input_text or "", True, (25, 30, 36))
        # Scroll the text horizontally so the cursor stays visible, and clip
        # the text to the input field so long input cannot overflow the panel.
        offset = min(0, inner.width - cursor_x - 2)
        previous_clip = target_surface.get_clip()
        target_surface.set_clip(inner)
        text_y = inner.centery - text_surface.get_height() // 2
        target_surface.blit(text_surface, (inner.x + offset, text_y))
        if self.focus_index == 0 and pygame.time.get_ticks() % 1000 < 600:
            caret_x = inner.x + offset + cursor_x
            pygame.draw.line(
                target_surface,
                (25, 30, 36),
                (caret_x, inner.y + 2),
                (caret_x, inner.bottom - 2),
            )
        target_surface.set_clip(previous_clip)

    def _draw_button(self, target_surface: pygame.Surface, button: DialogButton) -> None:
        focused = button.index == self.focus_index
        fill = (48, 87, 132) if focused else (63, 93, 132)
        border = (21, 35, 54) if focused else (35, 48, 66)
        pygame.draw.rect(target_surface, fill, button.rect, border_radius=5)
        pygame.draw.rect(target_surface, border, button.rect, 2 if focused else 1, border_radius=5)
        label = self._fit_text(button.label, button.rect.width - 16, self._button_font)
        text_surface = self._button_font.render(label, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=button.rect.center)
        target_surface.blit(text_surface, text_rect)

    def _fit_text(self, text: str, max_width: int, font: pygame.font.Font) -> str:
        if font.size(text)[0] <= max_width:
            return text
        clipped = text
        while clipped and font.size(clipped + "...")[0] > max_width:
            clipped = clipped[:-1]
        return clipped + "..." if clipped else "..."

    @staticmethod
    def _wrap_text(text: str, max_width: int, font: pygame.font.Font) -> list[str]:
        lines: list[str] = []
        for paragraph in str(text).splitlines() or [""]:
            current = ""
            for word in paragraph.split() or [""]:
                parts = Dialog._split_word(word, max_width, font)
                for part in parts:
                    candidate = part if not current else f"{current} {part}"
                    if font.size(candidate)[0] <= max_width:
                        current = candidate
                    else:
                        if current:
                            lines.append(current)
                        current = part
            lines.append(current)
        return lines

    @staticmethod
    def _split_word(word: str, max_width: int, font: pygame.font.Font) -> list[str]:
        if font.size(word)[0] <= max_width:
            return [word]
        parts: list[str] = []
        current = ""
        for char in word:
            if current and font.size(current + char)[0] > max_width:
                parts.append(current)
                current = char
            else:
                current += char
        if current:
            parts.append(current)
        return parts


class DialogService:
    """Factory for modal dialogs on a world.

    All factory methods return immediately; the result is delivered to the
    ``callback`` (and stored in ``dialog.value`` after the dialog closed).
    Cancelling a dialog (ESC) always delivers ``None``. Pass ``pause=True``
    to stop the world's logic (acting, timers, collisions) while the dialog
    is open.
    """

    def __init__(self, world) -> None:
        self.world = world

    def msgbox(
        self,
        msg: str = "",
        title: str = "",
        button: str = "OK",
        callback: Callable[[bool | None], None] | None = None,
        **kwargs,
    ) -> Dialog:
        """Shows a message with a single confirmation button.

        The callback receives ``True`` when confirmed and ``None`` when the
        dialog was cancelled with ESC.
        """
        return self._open(
            Dialog(self.world, msg, title, (str(button),), "msg", callback=callback, **kwargs)
        )

    def alert(
        self,
        msg: str = "",
        title: str = "",
        button: str = "OK",
        callback: Callable[[bool | None], None] | None = None,
        **kwargs,
    ) -> Dialog:
        """Alias for :meth:`msgbox`."""
        return self.msgbox(msg, title, button, callback, **kwargs)

    def ynbox(
        self,
        msg: str = "",
        title: str = "",
        choices: Sequence[str] = ("Yes", "No"),
        callback: Callable[[bool | None], None] | None = None,
        **kwargs,
    ) -> Dialog:
        choices = tuple(choices)
        if len(choices) != 2:
            raise ValueError("ynbox choices must contain exactly two labels")
        return self._open(Dialog(self.world, msg, title, choices, "yn", callback=callback, **kwargs))

    def choicebox(
        self,
        msg: str = "",
        title: str = "",
        choices: Sequence[str] = (),
        callback: Callable[[str | None], None] | None = None,
        **kwargs,
    ) -> Dialog:
        if not choices:
            raise ValueError("choicebox choices must not be empty")
        return self._open(Dialog(self.world, msg, title, choices, "choice", callback=callback, **kwargs))

    def enterbox(
        self,
        msg: str = "",
        title: str = "",
        default: str = "",
        callback: Callable[[str | None], None] | None = None,
        **kwargs,
    ) -> Dialog:
        return self._open(
            Dialog(self.world, msg, title, (), "input", default=default, callback=callback, **kwargs)
        )

    def _open(self, dialog: Dialog) -> Dialog:
        active = getattr(self.world, "_active_dialog", None)
        if active and active.is_open:
            active.close(None, notify=False)
            dialog._suppress_active_press = active._suppress_active_press
        self.world._active_dialog = dialog
        if self._is_left_mouse_pressed():
            dialog._suppress_active_press = True
        dialog.on_opened()
        return dialog

    @staticmethod
    def _is_left_mouse_pressed() -> bool:
        import miniworlds.base.app as app_mod

        app = app_mod.App.get_running_app()
        event_manager = getattr(app, "event_manager", None)
        pressed_buttons = getattr(event_manager, "is_mouse_pressed", None)
        return bool(pressed_buttons) and "mouse_left" in pressed_buttons
