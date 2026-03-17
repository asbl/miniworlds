from __future__ import annotations

import sys
from typing import Optional, Tuple, Union, cast

import miniworlds.appearances.appearance as appearance
import miniworlds.appearances.background as background_mod


class WorldBackgroundFacade:
    def __init__(self, world):
        self.world = world

    @property
    def background(self) -> background_mod.Background:
        return self.world.backgrounds.background

    def set_background_property(
        self, source: Union[str, Tuple[int, int, int], appearance.Appearance]
    ) -> None:
        try:
            if isinstance(source, appearance.Appearance):
                self.world.backgrounds.background = source
            else:
                self.world.backgrounds.add_background(source)
        except (FileNotFoundError, FileExistsError):
            _, exc_value, _ = sys.exc_info()
            raise exc_value.with_traceback(None)

    def switch_background(
        self, background: Union[int, appearance.Appearance]
    ) -> background_mod.Background:
        try:
            return cast(
                background_mod.Background,
                self.world.backgrounds.switch_appearance(background),
            )
        except FileNotFoundError:
            _, exc_value, _ = sys.exc_info()
            raise exc_value.with_traceback(None)

    def remove_background(
        self, background: Optional[Union[int, appearance.Appearance]] = None
    ) -> None:
        self.world.backgrounds.remove_appearance(background)

    def set_background(
        self, source: Union[str, Tuple[int, int, int]]
    ) -> background_mod.Background:
        try:
            return self.world.backgrounds.set_background(source)
        except FileNotFoundError:
            _, exc_value, _ = sys.exc_info()
            raise exc_value.with_traceback(None)

    def add_background(
        self, source: Union[str, Tuple[int, int, int]]
    ) -> background_mod.Background:
        try:
            return self.world.backgrounds.add_background(source)
        except FileNotFoundError:
            _, exc_value, _ = sys.exc_info()
            raise exc_value.with_traceback(None)

    def has_background(self) -> bool:
        return self.world.backgrounds.has_appearance()