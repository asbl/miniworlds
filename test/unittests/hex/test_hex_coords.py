"""Unit tests for the hex coordinate mathematics (pure functions, no world)."""

import pytest

from miniworlds.worlds.hex_world import hex_coords


class TestOffsetCubeConversion:
    @pytest.mark.parametrize("column", [0, 1, 2, 3, 4])
    @pytest.mark.parametrize("row", [0, 1, 2, 3, 4])
    def test_roundtrip_offset_to_cube_to_offset(self, column, row):
        cube = hex_coords.offset_to_cube((column, row))
        assert cube[0] + cube[1] + cube[2] == 0
        assert hex_coords.cube_to_offset(cube) == (column, row)

    def test_offset_to_cube_known_values(self):
        # Odd-r: odd rows are shifted half a hex to the right.
        assert hex_coords.offset_to_cube((0, 0)) == (0, 0, 0)
        assert hex_coords.offset_to_cube((1, 0)) == (1, 0, -1)
        assert hex_coords.offset_to_cube((0, 1)) == (0, 1, -1)
        assert hex_coords.offset_to_cube((1, 1)) == (1, 1, -2)


class TestCubeDistance:
    def test_distance_to_self_is_zero(self):
        cube = hex_coords.offset_to_cube((3, 3))
        assert hex_coords.cube_distance(cube, cube) == 0

    def test_distance_to_all_neighbors_is_one(self):
        cube = hex_coords.offset_to_cube((3, 3))
        for vector in hex_coords.CUBE_DIRECTIONS.values():
            neighbour = (
                cube[0] + vector[0],
                cube[1] + vector[1],
                cube[2] + vector[2],
            )
            assert hex_coords.cube_distance(cube, neighbour) == 1

    def test_distance_two_hexes_apart(self):
        assert hex_coords.cube_distance((0, 0, 0), (2, -1, -1)) == 2


class TestPixelConversion:
    @pytest.mark.parametrize("column", [0, 1, 2, 3])
    @pytest.mark.parametrize("row", [0, 1, 2, 3])
    def test_center_pixel_maps_back_to_same_hex(self, column, row):
        size = 40
        center = hex_coords.hex_center((column, row), size)
        cube = hex_coords.pixel_to_cube(center, size)
        assert hex_coords.cube_to_offset(cube) == (column, row)

    def test_odd_rows_are_shifted_right(self):
        size = 40
        even_row = hex_coords.hex_center((0, 0), size)
        odd_row = hex_coords.hex_center((0, 1), size)
        assert odd_row[0] == pytest.approx(even_row[0] + hex_coords.hex_width(size) / 2)
        assert odd_row[1] == pytest.approx(even_row[1] + 1.5 * size)

    def test_pixel_inside_hex_maps_to_that_hex(self):
        size = 40
        center = hex_coords.hex_center((2, 2), size)
        # A point between center and the eastern edge is still inside the hex.
        point = (center[0] + hex_coords.hex_width(size) / 4, center[1])
        cube = hex_coords.pixel_to_cube(point, size)
        assert hex_coords.cube_to_offset(cube) == (2, 2)

    def test_cube_round_prefers_nearest_center(self):
        assert hex_coords.cube_round((0.3, 0.3, -0.6)) == (0, 0, 0)
        assert hex_coords.cube_round((0.6, 0.2, -0.8)) == (1, 0, -1)


class TestCornerIdentity:
    def test_corner_is_shared_by_three_hexes(self):
        # The "n" corner of (3, 3) is the "sw" corner of its "no" neighbor
        # and the "so" corner of its "nw" neighbor.
        assert hex_coords.corner_position((3, 3), "n") == hex_coords.corner_position((4, 2), "sw")
        assert hex_coords.corner_position((3, 3), "n") == hex_coords.corner_position((3, 2), "so")

    def test_all_corner_directions_produce_distinct_keys(self):
        keys = [hex_coords.corner_position((2, 2), d) for d in hex_coords.CORNER_DIRECTIONS]
        assert len(set(keys)) == 6


class TestEdgeIdentity:
    def test_edge_is_shared_by_two_hexes(self):
        # The "o" edge of (3, 3) is the "w" edge of its eastern neighbor.
        assert hex_coords.edge_position((3, 3), "o") == hex_coords.edge_position((4, 3), "w")
        assert hex_coords.edge_position((3, 3), "no") == hex_coords.edge_position((4, 2), "sw")

    def test_all_edge_directions_produce_distinct_keys(self):
        keys = [hex_coords.edge_position((2, 2), d) for d in hex_coords.EDGE_DIRECTIONS]
        assert len(set(keys)) == 6


class TestCornerGeometry:
    def test_corner_pixel_offsets_enclose_the_hex(self):
        size = 40
        points = hex_coords.corner_pixel_points((0, 0), size)
        center = hex_coords.hex_center((0, 0), size)
        # All corners lie on the circumcircle.
        for point in points:
            distance = ((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2) ** 0.5
            assert distance == pytest.approx(size)

    def test_edge_center_is_midpoint_of_its_corners(self):
        size = 40
        center = hex_coords.hex_center((0, 0), size)
        edge_offset = hex_coords.edge_pixel_offset("o", size)
        first, second = hex_coords.EDGE_CORNERS["o"]
        first_offset = hex_coords.corner_pixel_offset(first, size)
        second_offset = hex_coords.corner_pixel_offset(second, size)
        expected_x = center[0] + (first_offset[0] + second_offset[0]) / 2
        expected_y = center[1] + (first_offset[1] + second_offset[1]) / 2
        assert (center[0] + edge_offset[0], center[1] + edge_offset[1]) == (expected_x, expected_y)


class TestWorldPixelSize:
    def test_world_size_grows_with_rows_and_columns(self):
        small = hex_coords.world_pixel_size(3, 3, 40)
        large = hex_coords.world_pixel_size(7, 7, 40)
        assert large[0] > small[0]
        assert large[1] > small[1]
