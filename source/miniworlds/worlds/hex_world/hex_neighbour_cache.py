"""Cache for the neighbour queries of hex tiles, corners, and edges."""

from __future__ import annotations

from typing import Callable, Iterable, List


class HexNeighbourCacheMixin:
    """Caches neighbour lists until the structure of the world changes.

    Corners and edges are only keyed by pure coordinate math, so the
    neighbour queries (`get_neighbour_corners`, `get_neighbour_edges`, ...)
    returned the same objects on every call but rebuilt them each time.
    The results are stored per element and dropped when the world's
    `_tile_structure_version` changes, exactly like the neighbour tile
    cache of `TileBase`.
    """

    def _cached_neighbours(self, name: str, build: Callable[[], Iterable]) -> List:
        """Return a fresh list of the cached result of `build` for `name`.

        A copy is returned, so callers can modify the list without
        corrupting the cache.
        """
        version = self._structure_version(self.world)
        cache = self.__dict__.get("_hex_neighbour_cache")
        if cache is None or cache[0] != version:
            cache = (version, {})
            self._hex_neighbour_cache = cache
        result = cache[1].get(name)
        if result is None:
            result = tuple(build())
            cache[1][name] = result
        return list(result)
