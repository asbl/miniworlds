"""Unit tests for miniworlds.base.api_validation module.

Tests cover:
- InputPolicy constants (bool and direction synonyms)
- Type validation functions (ensure_bool, ensure_real, ensure_int)
- Position and color validation
- Learning mode coercion
- Direction normalization

Test constants used for hint_builder examples and parameter names.
"""

import unittest
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from miniworlds.base.api_validation import (
    DirectionInput,
    InputPolicy,
    coerce_bool_learning,
    coerce_position_learning,
    ensure_bool,
    ensure_color_like,
    ensure_int,
    ensure_position_tuple,
    ensure_real,
    ensure_rect_like,
    type_name,
    with_try_hint,
)

# Test constants for hint messages and parameter names
SAMPLE_PARAMETER_NAME: str = "param"
SAMPLE_EXAMPLE_BOOL: str = "param=True"
SAMPLE_EXAMPLE_REAL: str = "param=10"
SAMPLE_EXAMPLE_INT: str = "param=10"
SAMPLE_EXAMPLE_POSITION: str = "param=(10, 20)"
SAMPLE_EXAMPLE_DIRECTION: str = "param='up'"

# Test constants for numeric values
SAMPLE_INT_VALUE: int = 10
SAMPLE_FLOAT_VALUE: float = 3.14
SAMPLE_NEGATIVE_INT: int = -100
SAMPLE_NEGATIVE_FLOAT: float = -2.5
SAMPLE_ZERO: int = 0


def _create_hint_builder(prefix: str = "HINT:") -> Callable[[str, str], str]:
    """Create a hint builder function with the given prefix."""
    return lambda msg, example: f"{prefix} {msg}"


class TestInputPolicy(unittest.TestCase):
    """Tests for InputPolicy class constants."""

    def test_learning_bool_true_synonyms(self) -> None:
        """Test all true boolean synonyms are recognized."""
        expected_true: set[str] = {"true", "yes", "y", "1", "on"}
        self.assertEqual(
            InputPolicy.LEARNING_BOOL_TRUE,
            expected_true,
            "True synonyms should match expected set",
        )

    def test_learning_bool_false_synonyms(self) -> None:
        """Test all false boolean synonyms are recognized."""
        expected_false: set[str] = {"false", "no", "n", "0", "off"}
        self.assertEqual(
            InputPolicy.LEARNING_BOOL_FALSE,
            expected_false,
            "False synonyms should match expected set",
        )

    def test_learning_bool_sets_disjoint(self) -> None:
        """Test true and false synonym sets are disjoint."""
        intersection: set[str] = (
            InputPolicy.LEARNING_BOOL_TRUE & InputPolicy.LEARNING_BOOL_FALSE
        )
        self.assertEqual(
            intersection,
            set(),
            "True and false synonym sets should be disjoint",
        )

    def test_direction_synonyms_mapping(self) -> None:
        """Test direction synonyms map to canonical directions."""
        expected_canonical: set[str] = {"up", "right", "left", "down", "forward"}
        for synonym, canonical in InputPolicy.DIRECTION_SYNONYMS.items():
            self.assertIn(
                canonical,
                expected_canonical,
                f"Canonical direction '{canonical}' should be in expected set",
            )

    def test_direction_synonyms_count(self) -> None:
        """Test we have the expected number of direction synonyms."""
        # Should have synonyms for: up, right, left, down, forward
        self.assertGreater(
            len(InputPolicy.DIRECTION_SYNONYMS),
            10,
            "Should have more than 10 direction synonyms",
        )

    def test_direction_canonical_values(self) -> None:
        """Test canonical direction values are as expected."""
        self.assertEqual(
            set(InputPolicy.DIRECTION_CANONICAL),
            {"up", "right", "left", "down", "forward"},
            "Canonical directions should match expected set",
        )


class TestTypeHelpers(unittest.TestCase):
    """Tests for type helper functions."""

    def test_type_name_int(self) -> None:
        """Test type_name returns 'int' for integer values."""
        self.assertEqual(
            type_name(SAMPLE_INT_VALUE),
            "int",
            "type_name should return 'int' for integers",
        )

    def test_type_name_float(self) -> None:
        """Test type_name returns 'float' for float values."""
        self.assertEqual(
            type_name(SAMPLE_FLOAT_VALUE),
            "float",
            "type_name should return 'float' for floats",
        )

    def test_type_name_str(self) -> None:
        """Test type_name returns 'str' for string values."""
        self.assertEqual(
            type_name("hello"),
            "str",
            "type_name should return 'str' for strings",
        )

    def test_type_name_bool(self) -> None:
        """Test type_name returns 'bool' for boolean values."""
        self.assertEqual(
            type_name(True),
            "bool",
            "type_name should return 'bool' for booleans",
        )

    def test_type_name_none(self) -> None:
        """Test type_name returns 'NoneType' for None."""
        self.assertEqual(
            type_name(None),
            "NoneType",
            "type_name should return 'NoneType' for None",
        )

    def test_type_name_list(self) -> None:
        """Test type_name returns 'list' for list values."""
        self.assertEqual(
            type_name([1, 2]),
            "list",
            "type_name should return 'list' for lists",
        )

    def test_type_name_tuple(self) -> None:
        """Test type_name returns 'tuple' for tuple values."""
        self.assertEqual(
            type_name((1, 2)),
            "tuple",
            "type_name should return 'tuple' for tuples",
        )

    def test_with_try_hint_no_example(self) -> None:
        """Test with_try_hint without example."""
        message: str = "Error message"
        result: str = with_try_hint(message)
        self.assertEqual(
            result,
            message,
            "with_try_hint should return original message when no example",
        )

    def test_with_try_hint_with_example(self) -> None:
        """Test with_try_hint with example."""
        message: str = "Error message"
        example: str = SAMPLE_EXAMPLE_BOOL
        expected: str = f"{message}\nTry: {example}"
        result: str = with_try_hint(message, example)
        self.assertEqual(
            result,
            expected,
            "with_try_hint should append example to message",
        )


class TestEnsureBool(unittest.TestCase):
    """Tests for ensure_bool validation function."""

    def setUp(self) -> None:
        """Set up hint builder for all tests."""
        self.hint_builder: Callable[[str, str], str] = _create_hint_builder()

    def test_ensure_bool_valid_true(self) -> None:
        """Test ensure_bool accepts True."""
        ensure_bool(True, SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_BOOL)

    def test_ensure_bool_valid_false(self) -> None:
        """Test ensure_bool accepts False."""
        ensure_bool(
            False, SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_BOOL
        )

    def test_ensure_bool_rejects_string(self) -> None:
        """Test ensure_bool rejects string values."""
        with pytest.raises(TypeError) as exc_info:
            ensure_bool(
                "yes", SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_BOOL
            )
        error_msg: str = str(exc_info.value)
        self.assertIn(
            f"{SAMPLE_PARAMETER_NAME} must be bool",
            error_msg,
            "Error message should mention parameter name and type",
        )
        self.assertIn(
            "HINT:",
            error_msg,
            "Error message should include hint",
        )

    def test_ensure_bool_rejects_int(self) -> None:
        """Test ensure_bool rejects integer values (even 0 and 1)."""
        with pytest.raises(TypeError):
            ensure_bool(
                SAMPLE_INT_VALUE,
                SAMPLE_PARAMETER_NAME,
                self.hint_builder,
                SAMPLE_EXAMPLE_BOOL,
            )
        with pytest.raises(TypeError):
            ensure_bool(
                SAMPLE_ZERO,
                SAMPLE_PARAMETER_NAME,
                self.hint_builder,
                SAMPLE_EXAMPLE_BOOL,
            )

    def test_ensure_bool_rejects_float(self) -> None:
        """Test ensure_bool rejects float values."""
        with pytest.raises(TypeError):
            ensure_bool(
                SAMPLE_FLOAT_VALUE,
                SAMPLE_PARAMETER_NAME,
                self.hint_builder,
                SAMPLE_EXAMPLE_BOOL,
            )

    def test_ensure_bool_rejects_none(self) -> None:
        """Test ensure_bool rejects None."""
        with pytest.raises(TypeError):
            ensure_bool(
                None, SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_BOOL
            )


class TestEnsureReal(unittest.TestCase):
    """Tests for ensure_real validation function."""

    def setUp(self) -> None:
        """Set up hint builder for all tests."""
        self.hint_builder: Callable[[str, str], str] = _create_hint_builder()

    def test_ensure_real_valid_int(self) -> None:
        """Test ensure_real accepts integer values."""
        ensure_real(
            SAMPLE_INT_VALUE,
            SAMPLE_PARAMETER_NAME,
            self.hint_builder,
            SAMPLE_EXAMPLE_REAL,
        )

    def test_ensure_real_valid_float(self) -> None:
        """Test ensure_real accepts float values."""
        ensure_real(
            SAMPLE_FLOAT_VALUE,
            SAMPLE_PARAMETER_NAME,
            self.hint_builder,
            SAMPLE_EXAMPLE_REAL,
        )

    def test_ensure_real_valid_negative(self) -> None:
        """Test ensure_real accepts negative values."""
        ensure_real(
            SAMPLE_NEGATIVE_INT,
            SAMPLE_PARAMETER_NAME,
            self.hint_builder,
            SAMPLE_EXAMPLE_REAL,
        )
        ensure_real(
            SAMPLE_NEGATIVE_FLOAT,
            SAMPLE_PARAMETER_NAME,
            self.hint_builder,
            SAMPLE_EXAMPLE_REAL,
        )

    def test_ensure_real_rejects_bool(self) -> None:
        """Test ensure_real rejects boolean values (even though bool is subclass of int)."""
        with pytest.raises(TypeError):
            ensure_real(
                True, SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_REAL
            )
        with pytest.raises(TypeError):
            ensure_real(
                False, SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_REAL
            )

    def test_ensure_real_rejects_string(self) -> None:
        """Test ensure_real rejects string values."""
        with pytest.raises(TypeError):
            ensure_real(
                "10", SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_REAL
            )

    def test_ensure_real_rejects_none(self) -> None:
        """Test ensure_real rejects None."""
        with pytest.raises(TypeError):
            ensure_real(
                None, SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_REAL
            )


class TestEnsureInt(unittest.TestCase):
    """Tests for ensure_int validation function."""

    def setUp(self) -> None:
        """Set up hint builder for all tests."""
        self.hint_builder: Callable[[str, str], str] = _create_hint_builder()

    def test_ensure_int_valid(self) -> None:
        """Test ensure_int accepts integer values."""
        ensure_int(
            SAMPLE_INT_VALUE,
            SAMPLE_PARAMETER_NAME,
            self.hint_builder,
            SAMPLE_EXAMPLE_INT,
        )
        ensure_int(
            SAMPLE_NEGATIVE_INT,
            SAMPLE_PARAMETER_NAME,
            self.hint_builder,
            SAMPLE_EXAMPLE_INT,
        )
        ensure_int(
            SAMPLE_ZERO, SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_INT
        )

    def test_ensure_int_rejects_bool(self) -> None:
        """Test ensure_int rejects boolean values."""
        with pytest.raises(TypeError):
            ensure_int(
                True, SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_INT
            )
        with pytest.raises(TypeError):
            ensure_int(
                False, SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_INT
            )

    def test_ensure_int_rejects_float(self) -> None:
        """Test ensure_int rejects float values."""
        with pytest.raises(TypeError):
            ensure_int(
                SAMPLE_FLOAT_VALUE,
                SAMPLE_PARAMETER_NAME,
                self.hint_builder,
                SAMPLE_EXAMPLE_INT,
            )

    def test_ensure_int_rejects_string(self) -> None:
        """Test ensure_int rejects string values."""
        with pytest.raises(TypeError):
            ensure_int(
                "10", SAMPLE_PARAMETER_NAME, self.hint_builder, SAMPLE_EXAMPLE_INT
            )


# Wrapper functions for ensure_* validation functions
# These match the expected signature (value, parameter_name)
def _ensure_real_wrapper(value: Any, parameter_name: str) -> None:
    """Wrapper for ensure_real with consistent signature."""
    hint_builder: Callable[[str, str], str] = _create_hint_builder()
    ensure_real(value, parameter_name, hint_builder, SAMPLE_EXAMPLE_REAL)


def _ensure_int_wrapper(value: Any, parameter_name: str) -> None:
    """Wrapper for ensure_int with consistent signature."""
    hint_builder: Callable[[str, str], str] = _create_hint_builder()
    ensure_int(value, parameter_name, hint_builder, SAMPLE_EXAMPLE_INT)


class TestEnsurePositionTuple(unittest.TestCase):
    """Tests for ensure_position_tuple validation function."""

    def setUp(self) -> None:
        """Set up ensure_real wrapper for all tests."""
        self.ensure_real_fn: Callable[[Any, str], None] = _ensure_real_wrapper
        self.hint_builder: Callable[[str, str], str] = _create_hint_builder()

    def test_ensure_position_tuple_valid(self) -> None:
        """Test ensure_position_tuple accepts valid 2-tuples with numeric values."""
        ensure_position_tuple(
            (SAMPLE_INT_VALUE, 20),
            SAMPLE_PARAMETER_NAME,
            self.ensure_real_fn,
            self.hint_builder,
        )
        ensure_position_tuple(
            (SAMPLE_FLOAT_VALUE, SAMPLE_NEGATIVE_FLOAT),
            SAMPLE_PARAMETER_NAME,
            self.ensure_real_fn,
            self.hint_builder,
        )

    def test_ensure_position_tuple_rejects_list(self) -> None:
        """Test ensure_position_tuple rejects lists."""
        with pytest.raises(TypeError):
            ensure_position_tuple(
                [SAMPLE_INT_VALUE, 20],
                SAMPLE_PARAMETER_NAME,
                self.ensure_real_fn,
                self.hint_builder,
            )

    def test_ensure_position_tuple_rejects_3_tuple(self) -> None:
        """Test ensure_position_tuple rejects 3-tuples."""
        with pytest.raises(TypeError):
            ensure_position_tuple(
                (SAMPLE_INT_VALUE, 20, 30),
                SAMPLE_PARAMETER_NAME,
                self.ensure_real_fn,
                self.hint_builder,
            )

    def test_ensure_position_tuple_rejects_1_tuple(self) -> None:
        """Test ensure_position_tuple rejects 1-tuples."""
        with pytest.raises(TypeError):
            ensure_position_tuple(
                (SAMPLE_INT_VALUE,),
                SAMPLE_PARAMETER_NAME,
                self.ensure_real_fn,
                self.hint_builder,
            )

    def test_ensure_position_tuple_rejects_non_numeric(self) -> None:
        """Test ensure_position_tuple rejects non-numeric values in tuple."""
        with pytest.raises(TypeError):
            ensure_position_tuple(
                ("10", 20),
                SAMPLE_PARAMETER_NAME,
                self.ensure_real_fn,
                self.hint_builder,
            )


class TestEnsureRectLike(unittest.TestCase):
    """Tests for ensure_rect_like validation function."""

    def setUp(self) -> None:
        """Set up ensure_real wrapper and hint builder for all tests."""
        self.ensure_real_fn: Callable[[Any, str], None] = _ensure_real_wrapper
        self.hint_builder: Callable[[str, str], str] = _create_hint_builder()

    def test_ensure_rect_like_valid_pygame_rect(self) -> None:
        """Test ensure_rect_like accepts pygame.Rect."""
        import pygame

        pg_rect: pygame.Rect = pygame.Rect(10, 20, 30, 40)
        ensure_rect_like(
            pg_rect,
            SAMPLE_PARAMETER_NAME,
            pygame.Rect,
            self.ensure_real_fn,
            self.hint_builder,
        )

    def test_ensure_rect_like_valid_4_tuple(self) -> None:
        """Test ensure_rect_like accepts valid 4-tuples."""
        import pygame

        ensure_rect_like(
            (SAMPLE_INT_VALUE, 20, 30, 40),
            SAMPLE_PARAMETER_NAME,
            pygame.Rect,
            self.ensure_real_fn,
            self.hint_builder,
        )

    def test_ensure_rect_like_rejects_3_tuple(self) -> None:
        """Test ensure_rect_like rejects 3-tuples."""
        import pygame

        with pytest.raises(TypeError):
            ensure_rect_like(
                (SAMPLE_INT_VALUE, 20, 30),
                SAMPLE_PARAMETER_NAME,
                pygame.Rect,
                self.ensure_real_fn,
                self.hint_builder,
            )

    def test_ensure_rect_like_rejects_non_numeric(self) -> None:
        """Test ensure_rect_like rejects non-numeric values."""
        import pygame

        with pytest.raises(TypeError):
            ensure_rect_like(
                (SAMPLE_INT_VALUE, "20", 30, 40),
                SAMPLE_PARAMETER_NAME,
                pygame.Rect,
                self.ensure_real_fn,
                self.hint_builder,
            )


class TestEnsureColorLike(unittest.TestCase):
    """Tests for ensure_color_like validation function."""

    def setUp(self) -> None:
        """Set up ensure_int wrapper and hint builder for all tests."""
        self.ensure_real_fn: Callable[[Any, str], None] = _ensure_int_wrapper
        self.hint_builder: Callable[[str, str], str] = _create_hint_builder()

    def test_ensure_color_like_valid_3_tuple(self) -> None:
        """Test ensure_color_like accepts valid 3-tuples (RGB)."""
        ensure_color_like(
            (255, SAMPLE_ZERO, SAMPLE_ZERO),
            SAMPLE_PARAMETER_NAME,
            self.ensure_real_fn,
            self.hint_builder,
        )

    def test_ensure_color_like_valid_4_tuple(self) -> None:
        """Test ensure_color_like accepts valid 4-tuples (RGBA)."""
        ensure_color_like(
            (255, SAMPLE_ZERO, SAMPLE_ZERO, 128),
            SAMPLE_PARAMETER_NAME,
            self.ensure_real_fn,
            self.hint_builder,
        )

    def test_ensure_color_like_rejects_2_tuple(self) -> None:
        """Test ensure_color_like rejects 2-tuples."""
        with pytest.raises(TypeError):
            ensure_color_like(
                (255, SAMPLE_ZERO),
                SAMPLE_PARAMETER_NAME,
                self.ensure_real_fn,
                self.hint_builder,
            )

    def test_ensure_color_like_rejects_5_tuple(self) -> None:
        """Test ensure_color_like rejects 5-tuples."""
        with pytest.raises(TypeError):
            ensure_color_like(
                (255, SAMPLE_ZERO, SAMPLE_ZERO, 128, 50),
                SAMPLE_PARAMETER_NAME,
                self.ensure_real_fn,
                self.hint_builder,
            )

    def test_ensure_color_like_rejects_non_numeric(self) -> None:
        """Test ensure_color_like rejects non-numeric values."""
        with pytest.raises(TypeError):
            ensure_color_like(
                (255, "0", SAMPLE_ZERO),
                SAMPLE_PARAMETER_NAME,
                self.ensure_real_fn,
                self.hint_builder,
            )


class TestCoerceBoolLearning(unittest.TestCase):
    """Tests for coerce_bool_learning function."""

    def test_coerce_bool_learning_disabled(self) -> None:
        """Test coercion is skipped when learning_mode is False."""
        warn_mock: MagicMock = MagicMock()
        result: str = coerce_bool_learning(
            "yes", SAMPLE_PARAMETER_NAME, False, warn_mock
        )
        self.assertEqual(
            result,
            "yes",
            "Value should be unchanged when learning_mode is False",
        )
        warn_mock.assert_not_called()

    def test_coerce_bool_learning_true_synonyms(self) -> None:
        """Test coercion of true synonyms in learning mode."""
        warn_mock: MagicMock = MagicMock()
        for synonym in ["true", "yes", "y", "1", "on"]:
            result: bool = coerce_bool_learning(
                synonym, SAMPLE_PARAMETER_NAME, True, warn_mock
            )
            self.assertEqual(
                result,
                True,
                f"Synonym '{synonym}' should coerce to True",
            )
            warn_mock.assert_called()
            warn_mock.reset_mock()

    def test_coerce_bool_learning_false_synonyms(self) -> None:
        """Test coercion of false synonyms in learning mode."""
        warn_mock: MagicMock = MagicMock()
        for synonym in ["false", "no", "n", "0", "off"]:
            result: bool = coerce_bool_learning(
                synonym, SAMPLE_PARAMETER_NAME, True, warn_mock
            )
            self.assertEqual(
                result,
                False,
                f"Synonym '{synonym}' should coerce to False",
            )
            warn_mock.assert_called()
            warn_mock.reset_mock()

    def test_coerce_bool_learning_int_values(self) -> None:
        """Test coercion of integer 0 and 1 in learning mode."""
        warn_mock: MagicMock = MagicMock()
        # Only integers 0 and 1 are coerced to bool
        result: bool = coerce_bool_learning(1, SAMPLE_PARAMETER_NAME, True, warn_mock)
        self.assertEqual(
            result,
            True,
            "Integer 1 should coerce to True",
        )
        warn_mock.assert_called()

        warn_mock.reset_mock()
        result = coerce_bool_learning(
            SAMPLE_ZERO, SAMPLE_PARAMETER_NAME, True, warn_mock
        )
        self.assertEqual(
            result,
            False,
            "Integer 0 should coerce to False",
        )
        warn_mock.assert_called()

    def test_coerce_bool_learning_other_int_values_unchanged(self) -> None:
        """Test that other integer values (not 0 or 1) pass through unchanged."""
        warn_mock: MagicMock = MagicMock()
        result: int = coerce_bool_learning(
            SAMPLE_INT_VALUE, SAMPLE_PARAMETER_NAME, True, warn_mock
        )
        self.assertEqual(
            result,
            SAMPLE_INT_VALUE,
            "Integer 10 should pass through unchanged (only 0 and 1 are coerced)",
        )
        warn_mock.assert_not_called()

    def test_coerce_bool_learning_already_bool(self) -> None:
        """Test that bool values pass through unchanged."""
        warn_mock: MagicMock = MagicMock()
        result: bool = coerce_bool_learning(
            True, SAMPLE_PARAMETER_NAME, True, warn_mock
        )
        self.assertEqual(
            result,
            True,
            "True should pass through unchanged",
        )
        warn_mock.assert_not_called()

        result = coerce_bool_learning(False, SAMPLE_PARAMETER_NAME, True, warn_mock)
        self.assertEqual(
            result,
            False,
            "False should pass through unchanged",
        )
        warn_mock.assert_not_called()

    def test_coerce_bool_learning_unknown_string(self) -> None:
        """Test that unknown strings pass through unchanged."""
        warn_mock: MagicMock = MagicMock()
        unknown: str = "unknown"
        result: str = coerce_bool_learning(
            unknown, SAMPLE_PARAMETER_NAME, True, warn_mock
        )
        self.assertEqual(
            result,
            unknown,
            "Unknown string should pass through unchanged",
        )
        warn_mock.assert_not_called()


class TestCoercePositionLearning(unittest.TestCase):
    """Tests for coerce_position_learning function."""

    def test_coerce_position_learning_disabled(self) -> None:
        """Test coercion is skipped when learning_mode is False."""
        warn_mock: MagicMock = MagicMock()
        original_list: list[int] = [SAMPLE_INT_VALUE, 20]
        result: list[int] = coerce_position_learning(
            original_list, SAMPLE_PARAMETER_NAME, False, warn_mock
        )
        self.assertEqual(
            result,
            original_list,
            "List should be unchanged when learning_mode is False",
        )
        warn_mock.assert_not_called()

    def test_coerce_position_learning_list_to_tuple(self) -> None:
        """Test coercion of list to tuple in learning mode."""
        warn_mock: MagicMock = MagicMock()
        input_list: list[int] = [SAMPLE_INT_VALUE, 20]
        result: tuple[int, int] = coerce_position_learning(
            input_list, SAMPLE_PARAMETER_NAME, True, warn_mock
        )
        self.assertEqual(
            result,
            (SAMPLE_INT_VALUE, 20),
            "List should be converted to tuple",
        )
        warn_mock.assert_called_once()

    def test_coerce_position_learning_tuple_unchanged(self) -> None:
        """Test that tuples pass through unchanged."""
        warn_mock: MagicMock = MagicMock()
        original_tuple: tuple[int, int] = (SAMPLE_INT_VALUE, 20)
        result: tuple[int, int] = coerce_position_learning(
            original_tuple, SAMPLE_PARAMETER_NAME, True, warn_mock
        )
        self.assertEqual(
            result,
            original_tuple,
            "Tuple should pass through unchanged",
        )
        warn_mock.assert_not_called()

    def test_coerce_position_learning_non_list(self) -> None:
        """Test that non-list values pass through unchanged."""
        warn_mock: MagicMock = MagicMock()
        non_list: str = "10,20"
        result: str = coerce_position_learning(
            non_list, SAMPLE_PARAMETER_NAME, True, warn_mock
        )
        self.assertEqual(
            result,
            non_list,
            "Non-list value should pass through unchanged",
        )
        warn_mock.assert_not_called()


class TestDirectionInput(unittest.TestCase):
    """Tests for DirectionInput class."""

    def test_normalize_string_synonyms(self) -> None:
        """Test normalization of direction string synonyms."""
        for synonym, canonical in InputPolicy.DIRECTION_SYNONYMS.items():
            result: str = DirectionInput.normalize(synonym)
            self.assertEqual(
                result,
                canonical,
                f"Synonym '{synonym}' should normalize to '{canonical}'",
            )

    def test_normalize_canonical_directions(self) -> None:
        """Test that canonical directions are unchanged."""
        for direction in InputPolicy.DIRECTION_CANONICAL:
            result: str = DirectionInput.normalize(direction)
            self.assertEqual(
                result,
                direction,
                f"Canonical direction '{direction}' should be unchanged",
            )

    def test_normalize_non_string(self) -> None:
        """Test that non-string values pass through unchanged."""
        self.assertEqual(
            DirectionInput.normalize(90),
            90,
            "Integer 90 should pass through unchanged",
        )
        self.assertEqual(
            DirectionInput.normalize(SAMPLE_ZERO),
            SAMPLE_ZERO,
            "Integer 0 should pass through unchanged",
        )
        self.assertEqual(
            DirectionInput.normalize((SAMPLE_INT_VALUE, 20)),
            (SAMPLE_INT_VALUE, 20),
            "Tuple should pass through unchanged",
        )

    def test_normalize_case_insensitive(self) -> None:
        """Test that direction normalization is case-insensitive."""
        self.assertEqual(
            DirectionInput.normalize("UP"),
            "up",
            "'UP' should normalize to 'up'",
        )
        self.assertEqual(
            DirectionInput.normalize("Up"),
            "up",
            "'Up' should normalize to 'up'",
        )
        self.assertEqual(
            DirectionInput.normalize("RIGHT"),
            "right",
            "'RIGHT' should normalize to 'right'",
        )
        self.assertEqual(
            DirectionInput.normalize("ReChTs"),
            "right",
            "'ReChTs' should normalize to 'right'",
        )

    def test_normalize_with_whitespace(self) -> None:
        """Test that direction normalization strips whitespace."""
        self.assertEqual(
            DirectionInput.normalize("  up  "),
            "up",
            "'  up  ' should normalize to 'up'",
        )
        self.assertEqual(
            DirectionInput.normalize(" right "),
            "right",
            "' right ' should normalize to 'right'",
        )

    def test_normalize_unknown_direction(self) -> None:
        """Test that unknown directions are returned as-is."""
        unknown: str = "diagonal"
        result: str = DirectionInput.normalize(unknown)
        self.assertEqual(
            result,
            unknown,
            "Unknown direction should be returned as-is",
        )

    def test_ensure_valid_direction_string(self) -> None:
        """Test ensure accepts valid direction strings."""
        hint_builder: Callable[[str, str], str] = _create_hint_builder()
        ensure_position_tuple_fn: Callable[[Any, str], None] = _ensure_real_wrapper

        # Should not raise for valid strings
        DirectionInput.ensure(
            "up",
            SAMPLE_PARAMETER_NAME,
            False,
            ensure_position_tuple_fn,
            hint_builder,
        )
        DirectionInput.ensure(
            "right",
            SAMPLE_PARAMETER_NAME,
            False,
            ensure_position_tuple_fn,
            hint_builder,
        )

    def test_ensure_valid_direction_numeric(self) -> None:
        """Test ensure accepts numeric values."""
        hint_builder: Callable[[str, str], str] = _create_hint_builder()
        ensure_real_fn: Callable[[Any, str], None] = _ensure_real_wrapper

        DirectionInput.ensure(
            90, SAMPLE_PARAMETER_NAME, False, ensure_real_fn, hint_builder
        )

    def test_ensure_allow_none(self) -> None:
        """Test ensure accepts None when allow_none is True."""
        hint_builder: Callable[[str, str], str] = _create_hint_builder()
        ensure_real_fn: Callable[[Any, str], None] = _ensure_real_wrapper

        DirectionInput.ensure(
            None, SAMPLE_PARAMETER_NAME, True, ensure_real_fn, hint_builder
        )


if __name__ == "__main__":
    unittest.main()
