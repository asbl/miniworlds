from collections import deque
import pygame

import miniworlds.base.app as app_mod
from miniworlds.tools import keys


class AppEventManager:
    def __init__(self, app: "app_mod.App"):
        """The event manager consist

        Args:
            app (app.App): _description_
        """
        self.event_queue: deque = deque()
        self.is_key_pressed: dict = {}
        self.is_mouse_pressed: set = set()
        self.app: "app_mod.App" = app

    def handle_event_queue(self):
        """Handle the event queue
        This function is called once per mainloop iteration.
        The event_queue is build with `to_event_queue`.
        """
        while self.event_queue:
            element = self.event_queue.pop()
            [
                world._mainloop.handle_event(element[0], element[1])
                for world in self.app.worlds_manager.worlds
                if world.is_listening
            ]
        self.event_queue.clear()

    def to_event_queue(self, event, data):
        """Puts an event to the event queue.

        It is handled in the handle_event_queue
        """
        self.event_queue.appendleft((event, data))


    def add_special_chars(self, keys):
        if " " in keys:
            keys.append("space")
        return keys
    
    
    def convert_special_chars(self, key: str) -> str:
        if key == " ":
            return "space"
        else:
            return key
    
    def pygame_events_to_event_queue(self):
        """Puts pygame events to event queue. Called in mainloop (App._update) 1/frame.

        Iterates over pygame.event.get() and puts events in event queue.
        """
        pressed_keys = self.add_special_chars(list(self.is_key_pressed.values()))
        # pressed_keys stores keys currently pressed and is modified by keydown and keyup
        for event in pygame.event.get():
            # Event: Quit
            if event.type == pygame.QUIT:
                self.app.quit()
            # Event: Mouse-Button Down
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.put_mouse_down_in_event_queue(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.put_mouse_up_in_event_queue(event)
            elif event.type == pygame.MOUSEMOTION:
                pos = pygame.mouse.get_pos()
                self.to_event_queue("mouse_motion", pos)
                # key-events
            elif event.type == pygame.KEYUP:
                key = keys.get_key(event.unicode, event.key)
                if key:
                    self.is_key_pressed[key] = key
                    pressed_keys = self.add_special_chars(list(self.is_key_pressed.values()))
                self.to_event_queue("key_up", pressed_keys)
                if event.unicode != "":
                    self.to_event_queue("key_up_" + self.convert_special_chars(event.unicode), None)
                # REMOVE key from pressed keys, because keyup was called
                key = keys.get_key(event.unicode, event.key)
                if key and key in self.is_key_pressed.keys():
                    self.is_key_pressed.pop(key)
            elif event.type == pygame.KEYDOWN:
                key = keys.get_key(event.unicode, event.key)
                if key:
                    self.is_key_pressed[key] = key
                    pressed_keys = self.add_special_chars(list(self.is_key_pressed.values()))
                self.to_event_queue("key_down", pressed_keys)
                if event.unicode != "":
                    self.to_event_queue("key_down_" + self.convert_special_chars(event.unicode), None)
            elif event.type == pygame.VIDEORESIZE or event.type == pygame.VIDEOEXPOSE:
                for container in self.app.worlds_manager.worlds:
                    container.dirty = 1
                self.app.add_display_to_repaint_areas()
            # CHECK IF APP SHOULD QUIT
            if "\x11" in pressed_keys:
                self.app.quit()
            # CALL KEY PRESSED EVENT
        if self.is_key_pressed:
            self.to_event_queue("key_pressed", self.add_special_chars(list(self.is_key_pressed.values())))
        pos = pygame.mouse.get_pos()
        if self.is_mouse_pressed:
            for event in self.is_mouse_pressed:
                self.to_event_queue(event, pos)
        for key, value in self.is_key_pressed.items():
            if value != "":
                self.to_event_queue("key_pressed_" + value, None)

        return False

    def put_mouse_down_in_event_queue(self, event):
        """function is called in 'pygame_events_to_event_queue"""
        pos = pygame.mouse.get_pos()
        if event.button == 1:
            self.to_event_queue("mouse_left", pos)
            self.to_event_queue("mouse_left_down", pos)
            self.is_mouse_pressed.add("mouse_left")
        if event.button == 2:
            self.to_event_queue("mouse_middle", pos)
            self.to_event_queue("mouse_middle_down", pos)
            self.is_mouse_pressed.add("mouse_middle")
        if event.button == 3:
            self.to_event_queue("mouse_right", pos)
            self.to_event_queue("mouse_right_down", pos)
            self.is_mouse_pressed.add("mouse_right")
        if event.button == 4:
            self.to_event_queue("wheel_up", pos)
        if event.button == 5:
            self.to_event_queue("wheel_down", pos)

    def put_mouse_up_in_event_queue(self, event):
        """function is called in 'pygame_events_to_event_queue"""
        pos = pygame.mouse.get_pos()
        if event.button == 1:
            self.to_event_queue("mouse_left_up", pos)
            self.is_mouse_pressed.discard("mouse_left")
        if event.button == 2:
            self.to_event_queue("mouse_left_up", pos)
            self.is_mouse_pressed.discard("mouse_middle")
        if event.button == 3:
            self.to_event_queue("mouse_left_up", pos)
            self.is_mouse_pressed.discard("mouse_right")
