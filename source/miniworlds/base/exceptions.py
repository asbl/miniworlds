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
        self.message = f"Wrong number of arguments for {str(method)}, got {str(parameters)} but should be {str(sig.parameters)}"
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
        self.message = f"No valid world position for {actor}, type is {type(value)}  and should be a 2-tuple or Position"
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
        self.message = f"Method {method} is not overwritten or registered"


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
    def __init__(self, actor):
        self.message = f"origin must be 'center' or 'topleft' for actor {actor}"
        del actor
        super().__init__(self.message)


class WrongFilterType(MissingActorPartsError):
    def __init__(self, actor):
        self.message = f"wrong type for filter sensor results - Should be subclass of actor or instance of actor or string, but is: {type(actor)}"
        del actor
        super().__init__(self.message)
