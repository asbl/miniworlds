import abc
from abc import abstractmethod
from typing import Union, Tuple, List, TYPE_CHECKING

import miniworlds.appearances.managers.font_manager as font_manager
import miniworlds.appearances.managers.image_manager as image_manager
import miniworlds.appearances.managers.transformations_manager as transformations_manager
import miniworlds.tools.binding as binding
import miniworlds.tools.color as color_mod
import numpy
import pygame
from miniworlds.base.exceptions import MiniworldsError

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod


class MetaAppearance(abc.ABCMeta):
    def __call__(cls, *args, **kwargs):
        instance = type.__call__(
            cls, *args, **kwargs
        )  # create a new Appearance of type...
        instance.after_init()
        return instance


class Appearance(metaclass=MetaAppearance):
    """Base class of actor costumes and world backgrounds

    The class contains all methods and attributes to display and animate images of the objects, render text
    on the images or display overlays.
    """

    counter = 0

    RELOAD_ACTUAL_IMAGE = 1
    LOAD_NEW_IMAGE = 2

    def __init__(self):
        self.id = Appearance.counter + 1
        Appearance.counter += 1
        self.initialized = False
        self._flag_transformation_pipeline = False
        self.parent = None
        self.draw_shapes = []
        self.draw_images = []
        self._is_flipped = False
        self._is_animated = False
        self._is_textured = False
        self._is_centered = True
        self._is_upscaled = False
        self._is_scaled = False
        self._is_scaled_to_width = False
        self._is_scaled_to_height = False
        self._is_rotatable = False
        self._orientation = 0
        self._coloring = None  # Color for colorize operation
        self._transparency = False
        self._border = 0
        self._is_filled = False
        self._fill_color = (255, 0, 255, 255)
        self._border_color = None
        self._alpha = 255
        self._dirty = 0
        self._image = pygame.Surface((0, 0))  # size set in image()-method
        self.surface_loaded = False
        self.last_image = None
        self.font_manager = font_manager.FontManager(self)
        self.image_manager: "image_manager.ImageManager" = image_manager.ImageManager(
            self
        )
        self.transformations_manager = transformations_manager.TransformationsManager(
            self
        )
        self.image_manager.add_default_image()
        # properties
        self._texture_size = (0, 0)
        self._animation_speed = 10  #: The animation speed for animations
        self.loop = False
        self.animation_length = 0
        self._animation_start_frame = 0
        self._cached_rect = (-1, pygame.Rect(0, 0, 1, 1)) # frame, rect

    def _set_defaults(self, **kwargs) -> "Appearance":
        for key, value in kwargs.items():
            if value is not None:
                attr_name = f"_{key}"
                if hasattr(self, attr_name):
                    setattr(self, attr_name, value)
        self.set_dirty("all", self.LOAD_NEW_IMAGE)
        return self


    def set_image(self, source: Union[int, "Appearance", tuple]) -> bool:
        """Sets the displayed image of costume/background to selected index

        Args:
            source: The image index or an image.

        Returns:
            True, if image index exists

        Examples:

            Add two images two background and switch to image 2

            .. code-block:: python

                from miniworlds import *

                world = World()
                background = world.add_background("images/1.png")
                background.add_image("images/2.png")
                background.set_image(1)
                world.run()

        """
        if isinstance(source, int):
            return self.image_manager.set_image_index(source)
        elif isinstance(source, tuple):
            surface = image_manager.ImageManager.get_surface_from_color(source)
            self.image_manager.replace_image(
                surface, image_manager.ImageManager.COLOR, source
            )

    def after_init(self):
        # Called in metaclass
        self.set_dirty("all", Appearance.LOAD_NEW_IMAGE)
        self.initialized = True

    @property
    def font_size(self):
        return self.font_manager.font_size

    @font_size.setter
    def font_size(self, value):
        self.font_manager.set_font_size(value, update=True)

    def _set_font(self, font, font_size):
        self.font_manager.font_path = font
        self.font_manager.font_size = font_size

    @property
    def texture_size(self):
        self._texture_size

    @texture_size.setter
    def texture_size(self, value):
        self._texture_size = value
        self.set_dirty("texture", Appearance.RELOAD_ACTUAL_IMAGE)
        
    @property
    def animation_speed(self):
        return self._animation_speed

    @animation_speed.setter
    def animation_speed(self, value):
        self._animation_speed = value

    def _set_animation_speed(self, value):
        self.animation_speed = value

    def set_mode(self, **kwargs):
        if "texture_size" in kwargs:
            self._texture_size = kwargs["texture_size"]
        if "animation_speed" in kwargs:
            self.animation_speed = kwargs["animation_speed"]
        if "mode" in kwargs:
            mode = kwargs["mode"]
            if isinstance(mode, str):
                mode = [mode]
            if "textured" in mode:
                self._set_textured(True)
            elif "scaled" in mode:
                self._set_scaled(True)
            elif "scaled_to_width" in mode:
                self._set_scaled_to_width(True)
            elif "scaled_to_height" in mode:
                self._set_scaled_to_height(True)
            elif "upscaled" in mode:
                self._set_upscaled(True)
            elif "filled" in mode:
                self.set_filled(True)
            elif "flipped" in mode:
                self._set_flipped(True)
            elif "animated" in mode:
                self.is_animated(True)
            elif "rotatable" in mode:
                self._is_rotatable(True)
            elif "centered" in mode:
                self._set_centered(True)


    def get_modes(self):
        modes = {
            "textured": self._is_textured,
            "scaled": self._is_scaled,
            "scaled_to_width": self._is_scaled_to_width,
            "scaled_to_height": self._is_scaled_to_height,
            "upscaled": self._is_upscaled,
            "filled": self._is_filled,
            "flipped": self._is_flipped,
            "animated": self._is_animated,
            "rotatable": self._is_rotatable,
            "centered": self._is_centered,
        }
        return modes

    @property
    def is_textured(self):
        """
        bool: If True, the image is tiled over the background.

        Examples:

            Texture the board with the given image:

            .. code-block:: python

                from miniworlds import *

                world = World()
                background = world.add_background("images/stone.png")
                background.is_textured = True
                world.run()

            .. image:: ../_images/is_textured.png
                :alt: Textured image>

            Set texture size

            .. code-block:: python

                from miniworlds import *

                world = World()
                background = world.add_background("images/stone.png")
                background.is_textured = True
                background.texture_size = (15,15)
                world.run()

            .. image:: ../_images/is_textured1.png
                :alt: Textured image


        """
        return self._is_textured

    @is_textured.setter
    def is_textured(self, value):
        self._set_textured(value)

    def _set_textured(self, value: bool):
        """bool: If True, the image is tiled over the background.

        Args:
            value: True, if image should be displayed as textured.
        """
        self._is_textured = value
        self.set_dirty("texture", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def is_rotatable(self):
        """If True, costume will be rotated with token direction
        """
        return self._is_rotatable

    @is_rotatable.setter
    def is_rotatable(self, value):
        self._set_rotatable(value)

    @property
    def is_centered(self):
        return self._is_centered

    @is_centered.setter
    def is_centered(self, value):
        self._is_centered = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def is_filled(self):
        return self._is_filled

    @is_filled.setter
    def is_filled(self, value):
        self._set_filled(value)



    @property
    def is_flipped(self):
        """Flips the costume or background. The image is mirrored over the y-axis of costume/background.

        Examples:

            Flips actor:

            .. code-block:: python

                from miniworlds import *

                world = World()
                token = Token()
                token.add_costume("images/alien1.png")
                token.height= 400
                token.width = 100
                token.is_rotatable = False
                @token.register
                def act(self):
                    if self.world.frame % 100 == 0:
                        if self.costume.is_flipped:
                            self.costume.is_flipped = False
                        else:
                            self.costume.is_flipped = True
                world.run()

            .. image:: ../_images/flip1.png
                :alt: Textured image

            .. image:: ../_images/flip2.png
                :alt: Textured image

        """
        return self._is_flipped

    @is_flipped.setter
    def is_flipped(self, value):
        self._set_flipped(value)

    @property
    def is_upscaled(self):
        """If True, the image will be upscaled remaining aspect-ratio.
        """
        return self._is_upscaled

    @is_upscaled.setter
    def is_upscaled(self, value):
        self._set_upscaled(value)

    @property
    def is_scaled_to_width(self):
        return self._is_scaled_to_width

    @is_scaled_to_width.setter
    def is_scaled_to_width(self, value):
        self._set_scaled_to_width(value)

    @property
    def is_scaled_to_height(self):
        return self._is_scaled_to_height

    @is_scaled_to_height.setter
    def is_scaled_to_height(self, value):
        self._set_scaled_to_height(value)

    @property
    def fill_color(self):
        return self._fill_color

    @fill_color.setter
    def fill_color(self, value):
        self._fill_color = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def is_scaled(self):
        """Scales the token to parent-size without remaining aspect-ratio.
        """
        return self._is_scaled

    @is_scaled.setter
    def is_scaled(self, value):
        self._set_scaled(value)


    @property
    def orientation(self):
        """bool: If True, the image will be rotated by parent orientation before it is rotated.

        Examples:

            Both actors are moving up. The image of t2 is correctly aligned. t1 is looking in the wrong direction.

                .. code-block:: python



                    from miniworlds import *

                    world = TiledWorld()

                    t1 = Actor((4,4))
                    t1.add_costume("images/player.png")
                    t1.move()

                    t2 = Actor((4,5))
                    t2.add_costume("images/player.png")
                    t2.orientation = - 90
                    t2.move()

                    @t1.register
                    def act(self):
                        self.move()

                    @t2.register
                    def act(self):
                        self.move()

                    world.run()

            .. image:: ../_images/orientation.png
                :alt: Textured image

        """
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        self._orientation = value
        self.set_dirty("orientation", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def fill_color(self):
        return self._fill_color

    @fill_color.setter
    def fill_color(self, value):
        self._fill_color = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def coloring(self):
        """Defines a colored layer.

        `coloring` can be True or false.
        The color is defined by the attribute `appearance.color`.
        """
        return self._coloring

    @coloring.setter
    def coloring(self, value):
        self._coloring = value
        self.set_dirty("coloring", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def transparency(self):
        """Defines a transparency.

        If ``transparency``is ``True``, the che transparency value
        is defined by the attribute ``appearance.alpha``

        """
        return self._transparency

    @transparency.setter
    def transparency(self, value):
        self._transparency = value
        self.set_dirty("transparency", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def alpha(self):
        """defines transparency of Actor: 0: transparent, 255: visible
        If value < 1, it will be multiplied with 255.

        Examples:

            .. code-block:: python

                from miniworlds import *

                world = World(800,400)

                t = Actor((600,250))
                t.add_costume("images/alien1.png")
                t.costume.alpha = 50
                t.width = 40
                t.border = 1

                world.run()

            .. image:: ../_images/alpha.png
                :alt: Textured image

        """
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = value
        if 0 < value < 1:
            value = value * 255
        if value == 255:
            self.transparency = False
        else:
            self.transparency = True


    @property
    def is_animated(self):
        """If True, the costume will be animated.


        .. code-block:: python

            from miniworlds import *

            world = World(80,40)

            robo = Actor()
            robo.costume.add_images(["images/1.png"])
            robo.costume.add_images(["images/2.png","images/3.png","images/4.png"])
            robo.costume.animation_speed = 20
            robo.costume.is_animated = True
            world.run()

        .. video:: ../_static/animate.webm
            :autoplay:
            :width: 300
            :height: 100
        """
        return self._is_animated

    @is_animated.setter
    def is_animated(self, value: bool):
        self.set_animated(value)

    def set_animated(self, value: bool):
        self._is_animated = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)
        
    @property
    def color(self):
        """->See fill color"""
        return self._fill_color

    @color.setter
    def color(self, value):
        value = color_mod.Color.create(value).get()
        self._fill_color = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)


    @property
    def stroke_color(self):
        """see border color"""
        return self._border_color

    @stroke_color.setter
    def stroke_color(self, value):
        self.border_color = value

    @property
    def border_color(self):
        """border color of actor"""
        return self._border_color

    @border_color.setter
    def border_color(self, value: int):
        if value:
            self._border_color = value
            self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)
        else:
            self.border = None

    @property
    def border(self):
        """The border-size of actor.

        The value is 0, if actor has no border

        Returns:
            _type_: int
        """
        return self._border

    @border.setter
    def border(self, value: Union[int, None]):
        if not value:
            value = 0
        if not isinstance(value, int):
            raise TypeError("border value should be of type int")
        self._border = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)
       
    def flip(self, value):
        self.is_flipped = value

    @property
    def images(self):
        return self.image_manager.images_list

    @property
    def image(self) -> pygame.Surface:
        """Performs all actions in image pipeline"""
        return self.get_image()

    def _set_rotatable(self, value: bool):
        """
        If set to True, costume will be rotated with actor direction

        Args:
            value: True, if image should be rotated with Actor direction

        Returns:

        """
        self._is_rotatable = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_centered(self, value):
        self._is_centered = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_flipped(self, value: bool):
        """
        Flips the costume or background. The image is mirrored over the y-axis of costume/background.

        Args:
            value: True, if Appearance should be displayed as flipped.

        Returns:

        """
        self._is_flipped = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_filled(self, value: bool):
        """
        Flips the costume or background. The image is mirrored over the y-axis of costume/background.

        Args:
            value: True, if Appearance should be displayed as flipped.

        Returns:

        """
        self._is_filled = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_scaled(self, value: bool):
        """
        Sets the actor to parenz-size **without** remaining aspect-ratio.

        Args:
            value: True or False
        """
        if value:
            self._is_upscaled = False
            self._is_scaled_to_height = False
            self._is_scaled_to_width = False
        self._is_scaled = value
        self.set_dirty("scale", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_upscaled(self, value: bool):
        """
        If set to True, the image will be upscaled remaining aspect-ratio.

        Args:
            value: True or False
        """
        if value:
            self._is_scaled = False
            self._is_scaled_to_height = False
            self._is_scaled_to_width = False
        self._is_upscaled = value
        self.set_dirty("scale", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_scaled_to_width(self, value: bool):
        if value:
            self._is_upscaled = False
            self.is_scaled = False
            self._is_scaled_to_height = False
        self.is_scaled = False
        self._is_scaled_to_width = value
        self.set_dirty("scale", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_scaled_to_height(self, value):
        if value:
            self._is_upscaled = False
            self.is_scaled = False
            self._is_scaled_to_width = False
        self.is_scaled = False
        self._is_scaled_to_height = value
        self.set_dirty("scale", Appearance.RELOAD_ACTUAL_IMAGE)

    def remove_last_image(self):
        self.image_manager.remove_last_image()

    def add_image(self, source: Union[str, Tuple, pygame.Surface]) -> int:
        """Adds an image to the appearance

        Returns:
            Index of the created image.
        """
        if type(source) not in [str, pygame.Surface, tuple]:
            raise MiniworldsError(
                f"Error: Image source has wrong format (expected str or pygame.Surface, got {type(source)}"
            )
        return self.image_manager.add_image(source)

    def _set_image(self, source: Union[int, "Appearance", tuple]) -> bool:
        """Sets the displayed image of costume/background to selected index

        Args:
            source: The image index or an image.

        Returns:
            True, if image index exists

        Examples:

            Add two images two background and switch to image 2

            .. code-block:: python

                from miniworlds import *

                world = World()
                background = world.add_background("images/1.png")
                background.add_image("images/2.png")
                background._set_image(1)
                world.run()

        """
        if isinstance(source, int):
            return self.image_manager._set_image_index(source)
        elif type(source) == tuple:
            surface = image_manager.ImageManager.get_surface_from_color(source)
            self.image_manager.replace_image(
                surface, image_manager.ImageManager.COLOR, source
            )

    def add_images(self, sources: list):
        """Adds multiple images to background/costume.

        Each source in sources parameter must be a valid parameter for :py:attr:`Appearance.cimage`
        """
        assert isinstance(sources, list)
        for source in sources:
            self.add_image(source)

    def animate(self, loop=False):
        """Animates the costume

        Args:
            loop: If loop = True, the animation will be processed as loop. (you can stop this with self.loop)

        .. code-block:: python

            from miniworlds import *

            world = World(80,40)

            robo = Actor()
            robo.costume.add_images(["images/1.png"])
            robo.costume.add_images(["images/2.png","images/3.png","images/4.png"])
            robo.costume.animation_speed = 20
            robo.costume.is_animated = True
            world.run()

        .. video:: ../_static/animate.webm
            :autoplay:
            :width: 300
            :height: 100
        """
        self._animation_start_frame = self.world.frame
        self.is_animated = True
        if loop:
            self.loop = True

    def after_animation(self):
        """
        the method is overwritten in subclasses costume and appearance

        Examples:

            The actor will be removed after the animation - This can be used for explosions.

            .. code-block:: python

                from miniworlds import *

                world = World()
                actor = Actor()
                costume = actor.add_costume("images/1.png")
                costume.add_image("images/2.png")
                costume.animate()
                @costume.register
                def after_animation(self):
                    self.parent.remove()

                world.run()
        """
        pass

    def to_colors_array(self) -> numpy.ndarray:
        """Create an array from costume or background.
        The array can be re-written to appearance with ``.from_array``

        Examples:

            Convert a background image to grayscale

            .. code-block:: python

                from miniworlds import *

                world = World(600,400)
                world.add_background("images/sunflower.jpg")
                arr = world.background.to_colors_array()

                def brightness(r, g, b):
                    return (int(r) + int(g) + int(b)) / 3

                for x in range(len(arr)):
                    for y in range(len(arr[0])):
                        arr[x][y] = brightness(arr[x][y][0], arr[x][y][1], arr[x][y][2])

                world.background.from_array(arr)
                world.run()

            Output:

            .. image:: ../_images/sunflower5grey.png
                :alt: converted image
        """
        return pygame.surfarray.array3d(self.image)

    def from_array(self, arr: numpy.ndarray):
        """Create a background or costume from array. The array must be a ``numpy.ndarray,
        which can be created with ``.to_colors_array``

        Examples:

            Convert grey default-background to gradient

            .. code-block:: python

                from miniworlds import *

                world = World()
                arr = world.background.to_colors_array()
                for x in range(len(arr)):
                    for y in range(len(arr[0])):
                        arr[x][y][0] = ((x +1 ) / world.width) * 255
                        arr[x][y][1] = ((y +1 ) /world.width) * 255
                world.background.from_array(arr)
                world.run()


                world.background.from_array(arr)
                world.run()

            Output:

            .. image:: ../_images/gradient3.png
                :alt: converted image
        """
        surf = pygame.surfarray.make_surface(arr)
        self.image_manager.replace_image(surf, image_manager.ImageManager.SURFACE, None)

    def fill(self, value):
        """Set default fill color for borders and lines"""
        self._is_filled = value
        if self.is_filled:
            self.fill_color = color_mod.Color(value).get()
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    def set_filled(self, value):
        self._is_filled = value

    def get_color(self, position):
        x = int(position[0])
        y = int(position[1])
        if 0 <= x < self.image.get_width() and 0 <= y < self.image.get_height():
            return self.image.get_at((x, y))
        else:
            return None

    def get_rect(self):
        frame = self.actor.world.frame
        if frame < self._cached_rect[0]:
            return self._cached_rect[1]
        rect = self.image.get_rect()
        self._cached_rect = (frame, rect)
        return rect

    def draw(self, source, position, width, height):
        if isinstance(source, str):
            self.draw_on_image(source, position, width, height)
        elif isinstance(source, tuple):
            self.draw_color_on_image(source, position, width, height)

    def draw_on_image(self, path, position, width, height):
        file = self.image_manager.find_image_file(path)
        surface = self.image_manager.load_image(file)
        self.draw_image_append(
            surface, pygame.Rect(position[0], position[1], width, height)
        )
        self.set_dirty("draw_images", Appearance.RELOAD_ACTUAL_IMAGE)

    def draw_color_on_image(self, color, position, width, height):
        surface = pygame.Surface((width, height))
        surface.fill(color)
        self.draw_image_append(
            surface, pygame.Rect(position[0], position[1], width, height)
        )
        self.set_dirty("draw_images", Appearance.RELOAD_ACTUAL_IMAGE)

    def __str__(self):
        return (
            self.__class__.__name__
            + "with ID ["
            + str(self.id)
            + "] for parent:["
            + str(self.parent)
            + "], images: "
            + str(self.image_manager.images_list)
        )

    def get_image(self):
        """If dirty, the image will be reloaded.
        The image pipeline will be  processed, defined by "set_dirty"
        """
        if (
            self.dirty >= self.RELOAD_ACTUAL_IMAGE
            and not self._flag_transformation_pipeline
        ):
            self.dirty = 0
            self._flag_transformation_pipeline = True
            self._before_transformation_pipeline()
            image = self.image_manager.load_image_from_image_index()
            image = self.transformations_manager.process_transformation_pipeline(
                image, self
            )
            self._after_transformation_pipeline()
            self._flag_transformation_pipeline = False
            self._image = image
        return self._image

    def _before_transformation_pipeline(self):
        """Called in `get_image`, if image is "dirty" (e.g. size, rotation, ... has changed)
        after image transformation pipeline is processed
        """
        pass

    def _after_transformation_pipeline(self) -> None:
        """Called in `get_image`, if image is "dirty" (e.g. size, rotation, ... has changed)
        before image transformation pipeline is processed
        """
        pass

    def update(self):
        """Loads the next image,
        called 1/frame"""
        if self.parent:
            self._load_image()
            return 1

    def _load_image(self):
        """Loads the image,

        * switches image if necessary
        * processes transformations pipeline if necessary
        """
        if self.is_animated and self._animation_start_frame != self.world.frame:
            if self.world.frame != 0 and self.world.frame % self.animation_speed == 0:
                self.image_manager.next_image()
        self.get_image()

    def register(self, method: callable):
        """
        Register method for decorator. Registers method to actor or background.
        """
        bound_method = binding.bind_method(self, method)
        return bound_method

    def draw_shape_append(self, shape, arguments):
        self.draw_shapes.append((shape, arguments))

    def draw_shape_set(self, shape, arguments):
        self.draw_shapes = [(shape, arguments)]

    def draw_image_append(self, surface, rect):
        self.draw_images.append((surface, rect))

    def draw_image_set(self, surface, rect):
        self.draw_images = [(surface, rect)]

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        if value == 0:
            self._dirty = 0
        else:
            self.set_dirty(value)

    def set_dirty(self, value="all", status=1):
        if self.parent and hasattr(self, "transformations_manager"):
            if value and self.images and self.get_manager()._is_display_initialized:
                self._update_draw_shape()
                self.transformations_manager.flag_reload_actions_for_transformation_pipeline(
                    value
                )
            if status >= self._dirty:
                self._dirty = status
                self.parent.dirty = 1

    @abstractmethod
    def get_manager(self):
        """Implemented in subclasses Costume and Background"""

    @property
    @abstractmethod
    def world(self) -> "world_mod.World":
        """Implemented in subclasses Costume and Background"""

    def _update_draw_shape(self) -> None:
        self.draw_shapes = []
        if self.parent and self._inner_shape() and self.image_manager:
            if self._is_filled and not self.image_manager.is_image():
                self.draw_shape_append(
                    self._inner_shape()[0], self._inner_shape_arguments()
                )
        if self.parent and self._outer_shape() and self.border:
            self.draw_shape_append(
                self._outer_shape()[0], self._outer_shape_arguments()
            )

    def _inner_shape(self) -> tuple:
        """Returns inner shape of costume

        Returns:
            pygame.Rect: Inner shape (Rectangle with size of actor)
        """
        return pygame.draw.rect, [
            pygame.Rect(0, 0, self.parent.size[0], self.parent.size[1]),
            0,
        ]

    def _outer_shape(self) -> tuple:
        """Returns outer shape of costume

        Returns:
            pygame.Rect: Outer shape (Rectangle with size of actors without filling.)
        """
        return pygame.draw.rect, [
            pygame.Rect(0, 0, self.parent.size[0], self.parent.size[1]),
            self.border,
        ]

    def _inner_shape_arguments(self) -> List:
        """def setGets arguments for inner shape

        Returns:
            List[]: List of arguments
        """

        color = self.fill_color
        return [
            color,
        ] + self._inner_shape()[1]

    def _outer_shape_arguments(self) -> List:
        """Gets arguments for outer shape

        Returns:
            List[]: List of arguments
        """
        color = self.border_color
        return [
            color,
        ] + self._outer_shape()[1]
