from inspect import signature


class MiniworldsError(RuntimeError):
    def __init__(self, message):
        super().__init__(message)


class NoRunError(MiniworldsError):
    def __init__(self):
        self.message = "[worldname].run() was not found in your code. This must be the last line in your code \ne.g.:\nworld.run()\n if your world-object is named world."
        super().__init__(self.message)


class MoveInDirectionTypeError(MiniworldsError):
    def __init__(self, direction):
        self.message = f"`direction` should be a direction (int, str) or a position (Position, tuple). Found {type(direction)}"
        super().__init__(self.message)


class WorldInstanceError(MiniworldsError):
    def __init__(self):
        self.message = "You can't use class World - You must use a specific class e.g. PixelWorld, TiledWorld or PhysicsWorld"
        super().__init__(self.message)


class WorldArgumentsError(MiniworldsError):
    def __init__(self, columns, rows):
        self.message = f"columns and rows should be int values but types are {type(columns)} and {type(rows)}"
        super().__init__(self.message)


class TiledWorldTooBigError(MiniworldsError):
    def __init__(self, columns, rows, tile_size):
        self.message = f"The playing field is too large ({rows} , {columns}) - The size must be specified in tiles, not pixels.\nDid you mean ({int(rows / tile_size)}, {int(rows / tile_size)})?"
        super().__init__(self.message)


class FileNotFoundError(MiniworldsError):
    def __init__(self, path):
        self.message = f"File not found. Is your file Path `{path}` correct?"
        super().__init__(self.message)


class WrongArgumentsError(MiniworldsError):
    def __init__(self, method, parameters):
        sig = signature(method)
        method_name = getattr(method, "__name__", str(method))
        self.message = (
            f"Wrong number of arguments for '{method_name}'. "
            f"Got {str(parameters)} but expected {str(sig.parameters)}.\n"
            f"Try: def {method_name}{sig}"
        )
        super().__init__(self.message)


class CostumeIsNoneError(MiniworldsError):
    def __init__(self):
        self.message = "Costume must not be none"
        super().__init__(self.message)


class NotCallableError(MiniworldsError):
    def __init__(self, method):
        self.message = f"{method} is not a method.."
        super().__init__(self.message)


class NotNullError(MiniworldsError):
    def __init__(self, method):
        self.message = f"{method} arguments should not be `None`"
        super().__init__(self.message)


class FirstArgumentShouldBeSelfError(MiniworldsError):
    def __init__(self, method):
        self.message = (
            f"Error calling {method}. Did you used `self` as first parameter?"
        )
        super().__init__(self.message)


class ColorException(MiniworldsError):
    def __init__(self):
        self.message = "color should be a 4-tuple (r, g, b, alpha"
        super().__init__(self.message)


class NoValidWorldPositionError(MiniworldsError):
    def __init__(self, value):
        self.message = f"No valid world position, type is {type(value)} and should be a 2-tuple or Position"
        super().__init__(self.message)


class NoValidPositionOnInitException(MiniworldsError):
    def __init__(self, actor, value):
        self.message = (
            f"Position for {actor} must be a tuple like (100, 200), "
            f"not {type(value).__name__}: {repr(value)}. "
            f"Try: actor.position = (100, 200)"
        )
        super().__init__(self.message)


class NoValidWorldRectError(MiniworldsError):
    def __init__(self, value):
        self.message = f"No valid world rect, type is {type(value)} and should be a 4-tuple or WorldRect"
        super().__init__(self.message)


class CostumeOutOfBoundsError(MiniworldsError):
    def __init__(self, actor, costume_count, costume_number):
        self.message = f"Actor {str(actor)} has {costume_count} costumes. You can't access costume #{costume_number}\nRemember: actors are counted from 0!"
        super().__init__(self.message)


class NoCostumeSetError(MiniworldsError):
    def __init__(self, actor):
        self.message = (
            f"Actor {str(actor)} has no costume - You need to setup a costume first."
        )
        super().__init__(self.message)


class SizeOnTiledWorldError(MiniworldsError):
    def __init__(self):
        self.message = (
            "You can't set size for actors on a tiled world (size is always (1,1)"
        )
        super().__init__(self.message)


class ActorArgumentShouldBeTuple(MiniworldsError):
    def __init__(self):
        self.message = "First argument to create a Actor [position] should be a Tuple. Maybe you forgot brackets?"
        super().__init__(self.message)


class PhysicsSimulationTypeError(MiniworldsError):
    def __init__(self):
        self.message = "Physics simulation should be `None`, `static`, `manual` or `simulated`(default)"
        super().__init__(self.message)


class ActorClassNotFound(MiniworldsError):
    def __init__(self, name):
        self.message = f"Actor class `{name}` not found"
        super().__init__(self.message)


class CantSetAutoFontSize(MiniworldsError):
    def __init__(self):
        self.message = "Can't set font-size because auto_font_size is set. Use actor.auto_size = False or actor.auto_size = 'actor'"
        super().__init__(self.message)


class NotImplementedOrRegisteredError(MiniworldsError):
    def __init__(self, method):
        method_name = getattr(method, "__name__", str(method))
        owner = getattr(method, "__self__", None)
        owner_name = owner.__class__.__name__ if owner is not None else "YourClass"
        owner_module = owner.__class__.__module__ if owner is not None else ""
        is_world_owner = owner_module.startswith("miniworlds.worlds") or owner_name.endswith("World")
        owner_base = "World" if is_world_owner else "Actor"
        register_target = "world" if is_world_owner else owner_name.lower()
        signature_hints = []
        if method_name.startswith("on_key_down"):
            signature_hints.append("def on_key_down(self, key):")
        elif method_name.startswith("on_key_pressed"):
            signature_hints.append("def on_key_pressed(self, key):")
        elif method_name.startswith("on_key_up"):
            signature_hints.append("def on_key_up(self, key):")

        if method_name == "on_setup":
            signature_hints.append("def on_setup(self):")

        if method_name.startswith("on_mouse_") or method_name.startswith("on_clicked_"):
            signature_hints.append(f"def {method_name}(self, position):")

        if method_name == "on_message":
            signature_hints.append("def on_message(self, message):")

        hint_block = ""
        if signature_hints:
            joined_hints = "\n".join(f"   - {hint}" for hint in signature_hints)
            hint_block = f"\nCommon signatures:\n{joined_hints}"

        self.message = (
            f"Event handler '{method_name}' is not overwritten or registered.\n"
            f"(Meaning: not implemented or not registered.)\n"
            f"Try one of these options:\n"
            f"1) Subclass implementation:\n"
            f"   class {owner_name}({owner_base}):\n"
            f"       def {method_name}(self, ...):\n"
            f"           pass\n"
            f"2) Register a handler:\n"
            f"   @{register_target}.register\n"
            f"   def {method_name}(self, ...):\n"
            f"       pass"
            f"{hint_block}"
        )
        super().__init__(self.message)


class EllipseWrongArgumentsError(MiniworldsError):
    def __init__(self):
        self.message = (
            "Wrong arguments for Ellipse (position: tuple, width: float, height: float"
        )
        super().__init__(self.message)


class RectFirstArgumentError(MiniworldsError):
    def __init__(self, start_position):
        self.message = f"Error: First argument `position` of Rectangle should be tuple or Position, value. Found {start_position}, type: {type(start_position)}"
        super().__init__(self.message)


class LineFirstArgumentError(MiniworldsError):
    def __init__(self, start_position):
        self.message = f"Error: First argument `start_position` of Line should be tuple , value. Found {start_position}, type: {type(start_position)}"
        super().__init__(self.message)


class LineSecondArgumentError(MiniworldsError):
    def __init__(self, end_position):
        self.message = f"Error: Second argument 'end_position' of Line should be tuple, value. Found {end_position}, type: {type(end_position)}"
        super().__init__(self.message)


class NoWorldError(MiniworldsError):
    def __init__(self):
        self.message = "Error: Create a world before you place Actors"
        super().__init__(self.message)


class ImageIndexNotExistsError(MiniworldsError):
    def __init__(self, appearance, index):
        self.message = f"Error: Image index {index} does not exist for {appearance}.\n You can't set costume or background -image to a non-existing image"
        super().__init__(self.message)


class TileNotFoundError(MiniworldsError):
    def __init__(self, position):
        self.message = f"No valid Tile found for position {position}"
        super().__init__(self.message)


class CornerNotFoundError(MiniworldsError):
    def __init__(self, position):
        self.message = f"No valid Corner found for position {position}"
        super().__init__(self.message)


class EdgeNotFoundError(MiniworldsError):
    def __init__(self, position):
        self.message = f"No valid Edge found for position {position}"
        super().__init__(self.message)


class RegisterError(MiniworldsError):
    def __init__(self, method, instance):
        self.message = f"You can't register {method} to the instance {instance}"
        super().__init__(self.message)


class MissingActorPartsError(MiniworldsError):
    pass


class Missingworldsensor(MissingActorPartsError):
    def __init__(self, actor):
        self.message = "INTERNAL ERROR: Missing sensor_manager"
        del actor
        super().__init__(self.message)


class MissingPositionManager(MissingActorPartsError):
    def __init__(self, actor):
        self.message = "INTERNAL ERROR: Missing position_manager"
        del actor
        super().__init__(self.message)


class OriginException(MissingActorPartsError):
    def __init__(self, actor, value=None):
        if value is None:
            self.message = f"origin must be 'center' or 'topleft' for actor {actor}"
        else:
            self.message = f"Actor origin must be 'center' or 'topleft', not '{value}'"
        del actor
        super().__init__(self.message)


class WrongFilterType(MissingActorPartsError):
    def __init__(self, actor):
        self.message = (
            f"Actor filter must be:\n"
            f"  - An Actor class, like: actor_type=Enemy\n"
            f"  - An Actor name string, like: actor_type='Enemy'\n"
            f"  - Got {type(actor).__name__}: {repr(actor)}"
        )
        del actor
        super().__init__(self.message)
