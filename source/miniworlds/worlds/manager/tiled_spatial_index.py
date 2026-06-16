from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Set, Tuple

if TYPE_CHECKING:
    from miniworlds.actors.actor import Actor


TilePosition = Tuple[int, int]


class TiledSpatialIndex:
    """Spatial index optimized for TiledWorld using tile-based grid partitioning.

    Unlike the pixel-based SpatialIndex, this uses discrete tile positions
    for efficient actor lookup in tiled worlds (RPGs, board games, etc.).

    The index partitions the world into chunks of tiles. Each chunk contains
    actors that are positioned within that chunk's tile range.
    """

    def __init__(self, chunk_size: int = 8) -> None:
        """Initialize the tiled spatial index.

        Args:
            chunk_size: Number of tiles per dimension in each chunk.
                       Larger values = fewer chunks but more actors per query.
                       Smaller values = more chunks but faster lookups.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        self.chunk_size = chunk_size
        self._chunks: DefaultDict[TilePosition, Set["Actor"]] = defaultdict(set)
        self._actor_chunks: dict["Actor", frozenset[TilePosition]] = {}
        self._positions: DefaultDict[TilePosition, Set["Actor"]] = defaultdict(set)
        self._actor_positions: dict["Actor", TilePosition] = {}

    def _chunk_for_position(self, position: Tuple[float, float]) -> TilePosition:
        """Calculate chunk coordinates for a given tile position."""
        x, y = int(position[0]), int(position[1])
        chunk_x = x // self.chunk_size
        chunk_y = y // self.chunk_size
        return (chunk_x, chunk_y)

    def _tile_span_for_actor(self, actor: "Actor") -> Tuple[int, int]:
        """Return the actor footprint in tile units."""
        position_manager = getattr(actor, "position_manager", None)
        scaled_size = getattr(position_manager, "_scaled_size", None)
        if scaled_size is not None:
            width, height = scaled_size
        else:
            size = getattr(actor, "size", (1, 1))
            if isinstance(size, (int, float)):
                width = height = size
            else:
                width, height = size

        return max(1, int(width)), max(1, int(height))

    def _chunks_for_actor(self, actor: "Actor") -> frozenset[TilePosition]:
        """Calculate all chunks that an actor occupies based on its tile footprint."""
        # For TiledWorld, actors are typically on a single tile
        # But larger actors may span multiple tiles
        position = actor.position
        width_tiles, height_tiles = self._tile_span_for_actor(actor)

        x, y = int(position[0]), int(position[1])

        chunks = set()
        for dx in range(width_tiles):
            for dy in range(height_tiles):
                tile_pos = (x + dx, y + dy)
                chunks.add(self._chunk_for_position(tile_pos))

        return frozenset(chunks)

    def update(self, actor: "Actor") -> None:
        """Update the actor's position in the spatial index."""
        new_chunks = self._chunks_for_actor(actor)
        old_chunks = self._actor_chunks.get(actor, frozenset())
        new_position = (actor.position[0], actor.position[1])
        old_position = self._actor_positions.get(actor)

        if new_chunks == old_chunks and new_position == old_position:
            return

        # Remove from old chunks
        for chunk in old_chunks - new_chunks:
            actors = self._chunks[chunk]
            actors.discard(actor)
            if not actors:
                del self._chunks[chunk]

        # Add to new chunks
        for chunk in new_chunks - old_chunks:
            self._chunks[chunk].add(actor)

        if old_position is not None and old_position != new_position:
            actors = self._positions[old_position]
            actors.discard(actor)
            if not actors:
                del self._positions[old_position]
        self._positions[new_position].add(actor)

        self._actor_chunks[actor] = new_chunks
        self._actor_positions[actor] = new_position

    def remove(self, actor: "Actor") -> None:
        """Remove an actor from the spatial index."""
        old_chunks = self._actor_chunks.pop(actor, frozenset())
        for chunk in old_chunks:
            actors = self._chunks[chunk]
            actors.discard(actor)
            if not actors:
                del self._chunks[chunk]
        old_position = self._actor_positions.pop(actor, None)
        if old_position is not None:
            actors = self._positions[old_position]
            actors.discard(actor)
            if not actors:
                del self._positions[old_position]

    def query_position(self, position: Tuple[float, float]) -> Set["Actor"]:
        """Query all actors at a specific tile position.

        Returns all actors in the same chunk as the given position.
        For precise single-tile queries, use query_exact_position.
        """
        chunk = self._chunk_for_position(position)
        return set(self._chunks.get(chunk, set()))

    def query_exact_position(self, position: Tuple[float, float]) -> Set["Actor"]:
        """Query all actors exactly at the given tile position.

        This is more precise than query_position as it filters by exact position.
        """
        return set(self._positions.get((position[0], position[1]), set()))

    def query_rect(
        self, min_pos: Tuple[float, float], max_pos: Tuple[float, float]
    ) -> Set["Actor"]:
        """Query all actors within a rectangular tile region.

        Args:
            min_pos: Minimum (x, y) tile position (inclusive)
            max_pos: Maximum (x, y) tile position (inclusive)
        """
        min_x, min_y = int(min_pos[0]), int(min_pos[1])
        max_x, max_y = int(max_pos[0]), int(max_pos[1])

        min_chunk_x = min_x // self.chunk_size
        min_chunk_y = min_y // self.chunk_size
        max_chunk_x = max_x // self.chunk_size
        max_chunk_y = max_y // self.chunk_size

        actors: Set["Actor"] = set()
        for chunk_x in range(min_chunk_x, max_chunk_x + 1):
            for chunk_y in range(min_chunk_y, max_chunk_y + 1):
                actors.update(self._chunks.get((chunk_x, chunk_y), set()))

        return {
            actor
            for actor in actors
            if min_x <= int(actor.position[0]) <= max_x
            and min_y <= int(actor.position[1]) <= max_y
        }

    def clear(self) -> None:
        """Clear all entries from the spatial index."""
        self._chunks.clear()
        self._actor_chunks.clear()
        self._positions.clear()
        self._actor_positions.clear()

    def __len__(self) -> int:
        return len(self._actor_chunks)

    def __contains__(self, actor: "Actor") -> bool:
        return actor in self._actor_chunks
