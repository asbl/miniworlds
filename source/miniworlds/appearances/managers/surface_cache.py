"""Byte-bounded, content-keyed cache for opt-in shared sprite transforms."""
from collections import OrderedDict
import hashlib

import pygame


class SurfaceCache:
    def __init__(self, max_bytes=32 * 1024 * 1024):
        self.bytes_used = 0
        self._entries = OrderedDict()
        self.set_budget(max_bytes)

    def set_budget(self, max_bytes):
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 0:
            raise ValueError("max_bytes must be a non-negative integer")
        self.max_bytes = max_bytes
        while self.bytes_used > max_bytes:
            _, (_, size) = self._entries.popitem(last=False)
            self.bytes_used -= size

    def clear(self):
        self._entries.clear()
        self.bytes_used = 0

    def transform(self, stage, image, parameters, render):
        digest = hashlib.sha256(pygame.image.tostring(image, "RGBA")).digest()
        colorkey = image.get_colorkey()
        key = (stage, image.get_size(), digest, image.get_alpha(),
               tuple(colorkey) if colorkey is not None else None, parameters)
        cached = self._entries.get(key)
        if cached is not None:
            self._entries.move_to_end(key)
            # Each appearance retains ownership; custom drawing may mutate it.
            return cached[0].copy()
        result = render()
        size = result.get_pitch() * result.get_height()
        if size <= self.max_bytes:
            self._entries[key] = (result.copy(), size)
            self.bytes_used += size
            while self.bytes_used > self.max_bytes:
                _, (_, removed_size) = self._entries.popitem(last=False)
                self.bytes_used -= removed_size
        return result


shared_surface_cache = SurfaceCache()
