from __future__ import annotations

NAMED_COLORS = {
    "black": (0, 0, 0, 255),
    "white": (255, 255, 255, 255),
    "red": (255, 0, 0, 255),
    "green": (0, 128, 0, 255),
    "blue": (0, 0, 255, 255),
    "yellow": (255, 255, 0, 255),
    "orange": (255, 165, 0, 255),
    "purple": (128, 0, 128, 255),
    "pink": (255, 192, 203, 255),
    "gray": (128, 128, 128, 255),
    "grey": (128, 128, 128, 255),
    "brown": (165, 42, 42, 255),
    "cyan": (0, 255, 255, 255),
    "magenta": (255, 0, 255, 255),
}


def normalize_color(value, colormode: float = 255):
    if value is None:
        return None
    if isinstance(value, str):
        lowered = value.lower()
        if lowered not in NAMED_COLORS:
            raise ValueError(f"unknown color string: {value!r}")
        return NAMED_COLORS[lowered]
    if isinstance(value, tuple):
        if len(value) not in (3, 4):
            raise ValueError("color tuples must have 3 or 4 components")
        factor = 255 / colormode
        components = tuple(int(component * factor) for component in value)
        if len(components) == 3:
            components = components + (255,)
        return components
    raise TypeError(f"unsupported color value: {value!r}")


def color_from_args(args, current, colormode: float = 255):
    if not args:
        return current
    if len(args) == 1:
        return normalize_color(args[0], colormode)
    return normalize_color(tuple(args), colormode)
