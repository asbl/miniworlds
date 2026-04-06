from __future__ import annotations

from difflib import get_close_matches
from numbers import Real
from typing import Callable, Optional


class InputPolicy:
    """Shared input policy for public beginner-facing APIs."""

    LEARNING_BOOL_TRUE = {"true", "yes", "y", "1", "on"}
    LEARNING_BOOL_FALSE = {"false", "no", "n", "0", "off"}

    DIRECTION_SYNONYMS = {
        "u": "up",
        "top": "up",
        "north": "up",
        "oben": "up",
        "r": "right",
        "east": "right",
        "rechts": "right",
        "l": "left",
        "west": "left",
        "links": "left",
        "d": "down",
        "south": "down",
        "unten": "down",
        "ahead": "forward",
        "straight": "forward",
        "vor": "forward",
    }
    DIRECTION_CANONICAL = ("up", "right", "left", "down", "forward")


def type_name(value) -> str:
    return type(value).__name__


def with_try_hint(message: str, example: str | None = None) -> str:
    if not example:
        return message
    return f"{message}\nTry: {example}"


def ensure_bool(value, parameter_name: str, hint_builder: Callable[[str, Optional[str]], str], example: str) -> None:
    if not isinstance(value, bool):
        raise TypeError(
            hint_builder(
                f"{parameter_name} must be bool, got {type(value).__name__}: {value!r}",
                example,
            )
        )


def ensure_real(value, parameter_name: str, hint_builder: Callable[[str, Optional[str]], str], example: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(
            hint_builder(
                f"{parameter_name} must be int or float, got {type(value).__name__}: {value!r}",
                example,
            )
        )


def ensure_int(value, parameter_name: str, hint_builder: Callable[[str, Optional[str]], str], example: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            hint_builder(
                f"{parameter_name} must be int, got {type(value).__name__}: {value!r}",
                example,
            )
        )


def ensure_position_tuple(
    value,
    parameter_name: str,
    ensure_real_fn: Callable[[object, str], None],
    hint_builder: Callable[[str, Optional[str]], str],
) -> None:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TypeError(
            hint_builder(
                f"{parameter_name} must be a tuple (x, y), got {type_name(value)}: {value!r}",
                f"{parameter_name} = (100, 200)",
            )
        )
    ensure_real_fn(value[0], f"{parameter_name}[0]")
    ensure_real_fn(value[1], f"{parameter_name}[1]")


def ensure_rect_like(
    value,
    parameter_name: str,
    rect_type,
    ensure_real_fn: Callable[[object, str], None],
    hint_builder: Callable[[str, Optional[str]], str],
) -> None:
    if isinstance(value, rect_type):
        return
    if not isinstance(value, tuple) or len(value) != 4:
        raise TypeError(
            hint_builder(
                f"{parameter_name} must be pygame.Rect or tuple (x, y, width, height), got {type_name(value)}: {value!r}",
                f"{parameter_name} = (10, 20, 30, 40)",
            )
        )
    for index, part in enumerate(value):
        ensure_real_fn(part, f"{parameter_name}[{index}]")


def ensure_color_like(
    value,
    parameter_name: str,
    ensure_real_fn: Callable[[object, str], None],
    hint_builder: Callable[[str, Optional[str]], str],
) -> None:
    if not isinstance(value, tuple):
        raise TypeError(
            hint_builder(
                f"{parameter_name} must be a tuple like (r, g, b) or (r, g, b, a), got {type_name(value)}: {value!r}",
                f"{parameter_name} = (255, 0, 0)",
            )
        )
    if len(value) not in (3, 4):
        raise TypeError(
            f"{parameter_name} must contain 3 or 4 values, got {len(value)} in {value!r}"
        )
    for index, part in enumerate(value):
        ensure_real_fn(part, f"{parameter_name}[{index}]")


def coerce_bool_learning(value, parameter_name: str, learning_mode: bool, warn: Callable[[str], None]):
    if isinstance(value, bool) or not learning_mode:
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in InputPolicy.LEARNING_BOOL_TRUE:
            warn(f"Learning mode: converted {parameter_name} from {value!r} to True")
            return True
        if normalized in InputPolicy.LEARNING_BOOL_FALSE:
            warn(f"Learning mode: converted {parameter_name} from {value!r} to False")
            return False
    if isinstance(value, int) and value in (0, 1):
        warn(f"Learning mode: converted {parameter_name} from {value!r} to {bool(value)!r}")
        return bool(value)
    return value


def coerce_position_learning(value, parameter_name: str, learning_mode: bool, warn: Callable[[str], None]):
    if not learning_mode:
        return value
    if isinstance(value, list) and len(value) == 2:
        warn(f"Learning mode: converted {parameter_name} from list to tuple")
        return (value[0], value[1])
    return value


class DirectionInput:
    @staticmethod
    def normalize(value):
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        normalized = InputPolicy.DIRECTION_SYNONYMS.get(normalized, normalized)
        if normalized in InputPolicy.DIRECTION_CANONICAL:
            return normalized
        close_match = get_close_matches(
            normalized, list(InputPolicy.DIRECTION_CANONICAL), n=1, cutoff=0.8
        )
        if close_match:
            return close_match[0]
        return normalized

    @staticmethod
    def ensure(
        value,
        parameter_name: str,
        allow_none: bool,
        ensure_position_tuple_fn: Callable[[object, str], None],
        hint_builder: Callable[[str, Optional[str]], str],
    ) -> None:
        if value is None and allow_none:
            return
        if isinstance(value, str):
            return
        if (
            hasattr(value, "x")
            and hasattr(value, "y")
            and isinstance(getattr(value, "x"), Real)
            and isinstance(getattr(value, "y"), Real)
            and not isinstance(getattr(value, "x"), bool)
            and not isinstance(getattr(value, "y"), bool)
        ):
            return
        if isinstance(value, tuple):
            ensure_position_tuple_fn(value, parameter_name)
            return
        if isinstance(value, Real) and not isinstance(value, bool):
            return
        raise TypeError(
            hint_builder(
                f"{parameter_name} must be int, float, str, or tuple (x, y), got {type_name(value)}: {value!r}",
                f"{parameter_name} = 'right'",
            )
        )
