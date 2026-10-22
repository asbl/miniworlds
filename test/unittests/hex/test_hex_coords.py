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


class TestCubeRing:
    def test_ring_with_radius_zero_is_the_center(self):
        assert hex_coords.cube_ring((2, 3, -5), 0) == [(2, 3, -5)]

    def test_negative_radius_returns_empty_list(self):
        assert hex_coords.cube_ring((2, 3, -5), -1) == []

    def test_ring_with_radius_one_contains_all_neighbors(self):
        center = (2, 3, -5)
        ring = hex_coords.cube_ring(center, 1)
        assert len(ring) == 6
        assert len(set(ring)) == 6
        for cube in ring:
            assert hex_coords.cube_distance(center, cube) == 1

    @pytest.mark.parametrize("radius", [2, 3, 4])
    def test_ring_contains_exact_distance_positions(self, radius):
        center = (2, 3, -5)
        ring = hex_coords.cube_ring(center, radius)
        assert len(ring) == 6 * radius
        assert len(set(ring)) == 6 * radius
        for cube in ring:
            assert hex_coords.cube_distance(center, cube) == radius

    def test_rings_do_not_overlap(self):
        center = (10, 10, -20)
        all_positions = []
        for radius in range(4):
            all_positions.extend(hex_coords.cube_ring(center, radius))
        assert len(all_positions) == len(set(all_positions))


class TestCubeDestination:
    def test_one_step_matches_neighbors(self):
        start = (3, 3)
        cube = hex_coords.offset_to_cube(start)
        for direction, vector in hex_coords.CUBE_DIRECTIONS.items():
            destination = hex_coords.cube_destination(start, direction, 1)
            expected = hex_coords.cube_to_offset(
                (cube[0] + vector[0], cube[1] + vector[1], cube[2] + vector[2])
            )
            assert destination == expected, direction

    def test_distance_moves_in_steps_of_one_hex(self):
        assert hex_coords.cube_destination((3, 3), "no", 2) == (4, 1)
        assert hex_coords.cube_destination((3, 3), "w", 3) == (0, 3)

    def test_distance_zero_stays_on_position(self):
        assert hex_coords.cube_destination((3, 3), "no", 0) == (3, 3)

    def test_invalid_direction_raises_helpful_error(self):
        from miniworlds.base.exceptions import DirectionNotFoundError

        with pytest.raises(DirectionNotFoundError):
            hex_coords.cube_destination((3, 3), "nord", 1)


class TestDirectionDegrees:
    def test_all_hex_directions_have_degrees(self):
        assert set(hex_coords.DIRECTION_DEGREES) == set(hex_coords.CUBE_DIRECTIONS)

    def test_degrees_are_sixty_degrees_apart(self):
        degrees = sorted(hex_coords.DIRECTION_DEGREES.values())
        assert degrees == [30, 90, 150, 210, 270, 330]

    def test_degree_lookup_is_inverse_of_name_lookup(self):
        for name, degrees in hex_coords.DIRECTION_DEGREES.items():
            assert hex_coords.DEGREE_DIRECTIONS[degrees] == name


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
