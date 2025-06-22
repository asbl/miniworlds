import os
from pathlib import Path
from typing import List, Union, Tuple, Dict, Optional, TypedDict

import pygame

import miniworlds.base.manager.app_file_manager as file_manager
from miniworlds.base.exceptions import ImageIndexNotExistsError, MiniworldsError


class ImageDictEntry(TypedDict):
    """Typed structure for entries in images_list."""
    image: pygame.Surface
    type: int
    source: Union[str, Tuple, None]


class ImageManager:
    """Manages loading, storing, and switching images for an appearance."""

    # Global image cache to avoid redundant disk loads
    _images_dict: Dict[str, pygame.Surface] = {}

    # Default folder for image resources
    IMAGE_FOLDER = "./images/"

    # Image source types
    IMAGE = 1     # loaded from file
    COLOR = 2     # generated from a color tuple
    SURFACE = 3   # passed as an existing surface

    def __init__(self, appearance):
        self.appearance = appearance
        self.image_index = 0
        self.images_list: List[ImageDictEntry] = []
        self.current_animation_images: Optional[List[ImageDictEntry]] = None
        self.animation_frame = 0
        self.has_image = False
        self.add_default_image()

    @staticmethod
    def _normalize_path(path: str) -> str:
        return str(path).replace("/", os.sep).replace("\\", os.sep)


    @staticmethod
    def load_image(path: Union[str, Path]) -> pygame.Surface:
        """Loads an image from disk with caching."""
        canonical_path = str(path).replace("/", os.sep).replace("\\", os.sep)

        if canonical_path in ImageManager._images_dict:
            return ImageManager._images_dict[canonical_path]

        try:
            image = pygame.image.load(canonical_path).convert_alpha()
        except pygame.error:
            raise FileExistsError(f"File '{path}' does not exist or is invalid.")

        ImageManager._images_dict[canonical_path] = image
        return image

    def find_image_file(self, path: str) -> str:
        """Resolves image path using the application's file manager."""
        return file_manager.FileManager.get_image_path(path)

    @staticmethod
    def cache_images_in_image_folder() -> None:
        """Pre-loads all images in the default folder into memory."""
        extensions = ["*.jpg", "*.jpeg", "*.png"]
        images = []
        for ext in extensions:
            images.extend(Path(ImageManager.IMAGE_FOLDER).rglob(ext))
        for img_path in images:
            ImageManager.load_image(img_path)

    def add_default_image(self) -> int:
        """Adds a 1x1 image filled with the appearance's fill color if no image exists yet."""
        if not self.has_image and not self.images_list:
            self.appearance.is_scaled = True
            surf = pygame.Surface((1, 1), pygame.SRCALPHA)
            surf.fill(self.appearance.fill_color)
            self.images_list.append({
                "image": surf,
                "type": self.COLOR,
                "source": self.appearance.fill_color
            })
            self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)
        return len(self.images_list) - 1

    def add_first_image(self, source: Union[str, list, pygame.Surface, Tuple]) -> None:
        """Handles scaling logic when the first image is added."""
        if len(self.images_list) == 1:
            self.images_list.pop(0)
        self._add_scaling(source)
        self.add_image_from_source(source)

    def add_image(self, source: Union[str, pygame.Surface, Tuple, List[str]]) -> int:
        """Adds an image from the given source (path, color, surface, or list)."""
        if not self.has_image and source:
            self.add_first_image(source)
            self.has_image = True
        elif source:
            return self.add_image_from_source(source)
        else:
            raise MiniworldsError("Unexpected image addition behavior.")

    def add_image_from_source(self, source: Union[str, list, pygame.Surface, Tuple]) -> int:
        """Routes source to correct method depending on its type."""
        if isinstance(source, str):
            return self.add_image_from_path(source)
        elif isinstance(source, list):
            return self.add_image_from_paths(source)
        elif isinstance(source, pygame.Surface):
            return self.add_image_from_surface(source)
        elif isinstance(source, tuple):
            return self.add_image_from_color(source)
        else:
            raise MiniworldsError(f"Unsupported image source type: {type(source)}")

    def _add_scaling(self, source: Union[str, list, pygame.Surface, Tuple]) -> None:
        """Adjusts scaling flags based on image source type."""
        if isinstance(source, (str, list)):
            self.appearance.is_upscaled = True
        elif isinstance(source, tuple):
            self.appearance.is_scaled = True

    @staticmethod
    def get_surface_from_color(color: Tuple) -> pygame.Surface:
        """Generates a surface filled with a single color."""
        surf = pygame.Surface((1, 1), pygame.SRCALPHA)
        surf.fill(color)
        return surf

    def add_image_from_color(self, color: Tuple) -> int:
        """Adds a new surface filled with the given color."""
        surf = self.get_surface_from_color(color)
        self.images_list.append({"image": surf, "type": self.COLOR, "source": color})
        self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)
        return len(self.images_list) - 1

    def get_source_from_current_image(self) -> Union[str, pygame.Surface, Tuple]:
        """Returns the original source of the current image."""
        return self.images_list[self.image_index]["source"]

    def is_image(self) -> bool:
        """Checks if current image was loaded from a file (not a color or surface)."""
        return self.images_list[self.image_index]["type"] == self.IMAGE

    def add_image_from_paths(self, paths: List[str]) -> int:
        """Adds multiple images from file paths."""
        for path in paths:
            self.add_image_from_path(path)
        return len(self.images_list) - 1

    def add_image_from_path(self, path: str) -> int:
        path = self._normalize_path(self.find_image_file(path))
        
        # Avoid duplicate entries
        for idx, entry in enumerate(self.images_list):
            if entry["type"] == ImageManager.IMAGE and entry["source"] == path:
                return idx  # already exists

        _image = self.load_image(path)
        self.images_list.append(
            {"image": _image, "type": ImageManager.IMAGE, "source": path}
        )
        self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)
        return len(self.images_list) - 1

    def add_image_from_surface(self, surface: pygame.Surface) -> int:
        """Adds an existing surface as an image."""
        self.images_list.append({
            "image": surface,
            "type": self.SURFACE,
            "source": None
        })
        self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)
        return len(self.images_list) - 1

    def get_surface(self, index: int) -> ImageDictEntry:
        """Returns the image dictionary entry at the given index."""
        try:
            return self.images_list[index]
        except IndexError:
            raise ImageIndexNotExistsError(index, self)

    def replace_image(self, image: pygame.Surface, type: int, source: Union[str, Tuple, None]) -> None:
        """Replaces the current image entry with a new one."""
        self.images_list[self.image_index] = {
            "image": image,
            "type": type,
            "source": source
        }
        self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)

    def reset_image_index(self) -> None:
        """Resets image index after animations."""
        if self.current_animation_images:
            self.image_index = len(self.images_list) - 1

    def next_image(self) -> None:
        """Advances to the next image (for animations)."""
        if self.appearance.is_animated:
            if self.image_index < len(self.images_list) - 1:
                self.image_index += 1
            else:
                if not self.appearance.loop:
                    self.appearance.is_animated = False
                    self.appearance.after_animation()
                self.image_index = 0
            self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)

    def first_image(self) -> None:
        """Resets to the first image."""
        self.image_index = 0

    def load_image_from_image_index(self) -> pygame.Surface:
        """Returns the current image surface."""
        if self.images_list and self.image_index < len(self.images_list):
            return self.images_list[self.image_index]["image"]
        return self.load_surface()

    def set_image_index(self, value: int) -> bool:
        """Changes the current image index to a specific value."""
        if value == -1:
            value = len(self.images_list) - 1
        if 0 <= value < len(self.images_list):
            old_index = self.image_index
            self.image_index = value
            if old_index != self.image_index:
                self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)
            return True
        raise ImageIndexNotExistsError(value, self)

    def load_surface(self) -> pygame.Surface:
        """Returns a blank fallback surface if image loading fails."""
        if not self.appearance.surface_loaded:
            image = pygame.Surface(
                (self.appearance.parent.width, self.appearance.parent.height),
                pygame.SRCALPHA
            )
            image.set_alpha(255)
            return image

    def end_animation(self, appearance) -> None:
        """Ends the animation and resets relevant state."""
        appearance.is_animated = False
        appearance.loop = False
        appearance.set_image(0)
        self.animation_frame = 0

    def remove_last_image(self) -> None:
        """Removes the last image in the list."""
        del self.images_list[-1]
        self.appearance.set_image(-1)
        self.appearance.set_dirty("all", self.appearance.LOAD_NEW_IMAGE)
