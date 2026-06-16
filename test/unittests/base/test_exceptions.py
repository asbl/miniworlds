"""Unit tests for miniworlds.base.exceptions module.

Tests cover all custom exception classes - verifying they can be instantiated
with appropriate arguments and that they inherit from MiniworldsError.

All exceptions in this module inherit from MiniworldsError, which itself
inherits from RuntimeError.
"""

import unittest
from typing import Optional

from miniworlds.base.exceptions import (
    ActorArgumentShouldBeTuple,
    ActorClassNotFound,
    CantSetAutoFontSize,
    ColorException,
    CornerNotFoundError,
    CostumeIsNoneError,
    CostumeOutOfBoundsError,
    EdgeNotFoundError,
    EllipseWrongArgumentsError,
    FileNotFoundError,
    FirstArgumentShouldBeSelfError,
    ImageIndexNotExistsError,
    LineFirstArgumentError,
    LineSecondArgumentError,
    MiniworldsError,
    MissingActorPartsError,
    MissingPositionManager,
    Missingworldsensor,
    MoveInDirectionTypeError,
    NoCostumeSetError,
    NoRunError,
    NotCallableError,
    NotImplementedOrRegisteredError,
    NotNullError,
    NoValidPositionOnInitException,
    NoValidWorldPositionError,
    NoValidWorldRectError,
    NoWorldError,
    OriginException,
    PhysicsSimulationTypeError,
    RectFirstArgumentError,
    RegisterError,
    SizeOnTiledWorldError,
    TiledWorldTooBigError,
    TileNotFoundError,
    WorldArgumentsError,
    WorldInstanceError,
    WrongArgumentsError,
    WrongFilterType,
)

# Test constants for exception messages
SAMPLE_PATH: str = "/path/to/missing/file.png"
SAMPLE_METHOD_NAME: str = "some_method"
SAMPLE_ACTOR_NAME: str = "DummyActor"


class TestMiniworldsError(unittest.TestCase):
    """Tests for the base MiniworldsError class."""

    def test_instantiation_with_custom_message(self) -> None:
        """Test that MiniworldsError can be instantiated with a custom message."""
        custom_message: str = "Test error message"
        error: MiniworldsError = MiniworldsError(custom_message)
        self.assertEqual(str(error), custom_message)

    def test_inherits_from_runtime_error(self) -> None:
        """Test that MiniworldsError is a subclass of RuntimeError."""
        self.assertTrue(issubclass(MiniworldsError, RuntimeError))


class TestNoRunError(unittest.TestCase):
    """Tests for NoRunError exception."""

    def test_instantiation_without_arguments(self) -> None:
        """Test that NoRunError can be instantiated without arguments."""
        error: NoRunError = NoRunError()
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_run_method(self) -> None:
        """Test that NoRunError message mentions the run() method."""
        error: NoRunError = NoRunError()
        message: str = str(error)
        self.assertIsNotNone(message, "Exception message should not be None")
        self.assertIn("run()", message, "Message should mention run() method")
        self.assertIn("world.run()", message, "Message should include example code")


class TestMoveInDirectionTypeError(unittest.TestCase):
    """Tests for MoveInDirectionTypeError exception."""

    def test_instantiation_with_type_argument(self) -> None:
        """Test that MoveInDirectionTypeError can be instantiated with a type argument."""
        error: MoveInDirectionTypeError = MoveInDirectionTypeError(int)
        self.assertIsInstance(error, MiniworldsError)

    def test_message_describes_direction_requirement(self) -> None:
        """Test that error message describes direction type requirements."""
        error: MoveInDirectionTypeError = MoveInDirectionTypeError(str)
        message: str = str(error)
        self.assertIn("direction", message.lower(), "Message should mention direction")
        self.assertIn("int", message, "Message should mention type")


class TestWorldInstanceError(unittest.TestCase):
    """Tests for WorldInstanceError exception."""

    def test_instantiation_without_arguments(self) -> None:
        """Test that WorldInstanceError can be instantiated without arguments."""
        error: WorldInstanceError = WorldInstanceError()
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_specific_world_classes(self) -> None:
        """Test that message mentions specific World subclass names."""
        error: WorldInstanceError = WorldInstanceError()
        message: str = str(error)
        self.assertIn("can't use class world", message.lower())
        self.assertIn("PixelWorld", message)
        self.assertIn("TiledWorld", message)
        self.assertIn("PhysicsWorld", message)


class TestWorldArgumentsError(unittest.TestCase):
    """Tests for WorldArgumentsError exception."""

    def test_instantiation_with_float_dimensions(self) -> None:
        """Test that WorldArgumentsError can be instantiated with float dimensions."""
        error: WorldArgumentsError = WorldArgumentsError(100.5, 200)
        self.assertIsInstance(error, MiniworldsError)

    def test_message_shows_invalid_types(self) -> None:
        """Test that message shows the invalid argument types."""
        error: WorldArgumentsError = WorldArgumentsError(100.5, 200)
        message: str = str(error)
        self.assertIn("int values", message.lower())
        self.assertIn("float", message.lower())
        self.assertIn("int", message.lower())


class TestTiledWorldTooBigError(unittest.TestCase):
    """Tests for TiledWorldTooBigError exception."""

    def test_instantiation_with_dimensions_and_tile_size(self) -> None:
        """Test that TiledWorldTooBigError can be instantiated with dimensions and tile size."""
        error: TiledWorldTooBigError = TiledWorldTooBigError(1000, 1000, 40)
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_tiles_not_pixels(self) -> None:
        """Test that message clarifies tiles vs pixels confusion."""
        error: TiledWorldTooBigError = TiledWorldTooBigError(1000, 1000, 40)
        message: str = str(error)
        self.assertIn("too large", message.lower())
        self.assertIn("1000", message)
        self.assertIn("tiles", message.lower())


class TestFileNotFoundError(unittest.TestCase):
    """Tests for FileNotFoundError exception."""

    def test_instantiation_with_file_path(self) -> None:
        """Test that FileNotFoundError can be instantiated with a file path."""
        error: FileNotFoundError = FileNotFoundError(SAMPLE_PATH)
        self.assertIsInstance(error, MiniworldsError)

    def test_message_includes_file_path(self) -> None:
        """Test that error message includes the missing file path."""
        error: FileNotFoundError = FileNotFoundError(SAMPLE_PATH)
        message: str = str(error)
        self.assertIn("File not found", message)
        self.assertIn(SAMPLE_PATH, message)


class TestWrongArgumentsError(unittest.TestCase):
    """Tests for WrongArgumentsError exception."""

    def test_instantiation_with_method_and_parameters(self) -> None:
        """Test that WrongArgumentsError can be instantiated with method and parameters."""

        def dummy_method(a: int, b: int) -> None:
            pass

        error: WrongArgumentsError = WrongArgumentsError(dummy_method, [1, 2, 3])
        self.assertIsInstance(error, MiniworldsError)

    def test_message_describes_argument_mismatch(self) -> None:
        """Test that message describes the argument count mismatch."""

        def dummy_method(a: int, b: int) -> None:
            pass

        error: WrongArgumentsError = WrongArgumentsError(dummy_method, [1, 2, 3])
        message: str = str(error)
        self.assertIn("Wrong number of arguments", message)
        self.assertIn("dummy_method", message)


class TestCostumeIsNoneError(unittest.TestCase):
    """Tests for CostumeIsNoneError exception."""

    def test_instantiation_without_arguments(self) -> None:
        """Test that CostumeIsNoneError can be instantiated without arguments."""
        error: CostumeIsNoneError = CostumeIsNoneError()
        self.assertIsInstance(error, MiniworldsError)

    def test_message_clarifies_none_not_allowed(self) -> None:
        """Test that message clarifies None is not allowed for costumes."""
        error: CostumeIsNoneError = CostumeIsNoneError()
        message: str = str(error)
        self.assertEqual(message, "Costume must not be none")


class TestNotCallableError(unittest.TestCase):
    """Tests for NotCallableError exception."""

    def test_instantiation_with_method_name(self) -> None:
        """Test that NotCallableError can be instantiated with a method name."""
        error: NotCallableError = NotCallableError(SAMPLE_METHOD_NAME)
        self.assertIsInstance(error, MiniworldsError)

    def test_message_identifies_non_callable(self) -> None:
        """Test that message identifies the non-callable item."""
        error: NotCallableError = NotCallableError(SAMPLE_METHOD_NAME)
        message: str = str(error)
        self.assertIn("not a method", message.lower())
        self.assertIn(SAMPLE_METHOD_NAME, message)


class TestNotNullError(unittest.TestCase):
    """Tests for NotNullError exception."""

    def test_instantiation_with_method_name(self) -> None:
        """Test that NotNullError can be instantiated with a method name."""
        error: NotNullError = NotNullError(SAMPLE_METHOD_NAME)
        self.assertIsInstance(error, MiniworldsError)

    def test_message_warns_about_none(self) -> None:
        """Test that message warns about None not being allowed."""
        error: NotNullError = NotNullError(SAMPLE_METHOD_NAME)
        message: str = str(error)
        self.assertIn("should not be", message.lower())
        self.assertIn("`None`", message)


class TestFirstArgumentShouldBeSelfError(unittest.TestCase):
    """Tests for FirstArgumentShouldBeSelfError exception."""

    def test_instantiation_with_method_name(self) -> None:
        """Test that FirstArgumentShouldBeSelfError can be instantiated with a method name."""
        error: FirstArgumentShouldBeSelfError = FirstArgumentShouldBeSelfError(
            SAMPLE_METHOD_NAME
        )
        self.assertIsInstance(error, MiniworldsError)

    def test_message_suggests_self_parameter(self) -> None:
        """Test that message suggests using self as first parameter."""
        error: FirstArgumentShouldBeSelfError = FirstArgumentShouldBeSelfError(
            SAMPLE_METHOD_NAME
        )
        message: str = str(error)
        self.assertIn("self", message.lower())
        self.assertIn("first parameter", message.lower())


class TestColorException(unittest.TestCase):
    """Tests for ColorException exception."""

    def test_instantiation_without_arguments(self) -> None:
        """Test that ColorException can be instantiated without arguments."""
        error: ColorException = ColorException()
        self.assertIsInstance(error, MiniworldsError)

    def test_message_describes_color_format(self) -> None:
        """Test that message describes the expected color format."""
        error: ColorException = ColorException()
        message: str = str(error)
        self.assertIn("color", message.lower())
        self.assertIn("4-tuple", message)


class TestNoValidWorldPositionError(unittest.TestCase):
    """Tests for NoValidWorldPositionError exception."""

    def test_instantiation_with_type(self) -> None:
        """Test that NoValidWorldPositionError can be instantiated with a type."""
        error: NoValidWorldPositionError = NoValidWorldPositionError(str)
        self.assertIsInstance(error, MiniworldsError)

    def test_message_describes_position_requirement(self) -> None:
        """Test that message describes position type requirements."""
        error: NoValidWorldPositionError = NoValidWorldPositionError(str)
        message: str = str(error)
        self.assertIn("No valid world position", message)


class TestNoValidPositionOnInitException(unittest.TestCase):
    """Tests for NoValidPositionOnInitException exception."""

    def test_instantiation_with_actor_and_value(self) -> None:
        """Test that exception can be instantiated with actor and invalid value."""

        class DummyActor:
            def __str__(self) -> str:
                return SAMPLE_ACTOR_NAME

        error: NoValidPositionOnInitException = NoValidPositionOnInitException(
            DummyActor(), "invalid_value"
        )
        self.assertIsInstance(error, MiniworldsError)

    def test_message_shows_actor_and_invalid_value(self) -> None:
        """Test that message shows actor and the invalid position value."""

        class DummyActor:
            def __str__(self) -> str:
                return SAMPLE_ACTOR_NAME

        error: NoValidPositionOnInitException = NoValidPositionOnInitException(
            DummyActor(), "invalid_value"
        )
        message: str = str(error)
        self.assertIn("Position", message)
        self.assertIn("must be a tuple", message.lower())


class TestNoValidWorldRectError(unittest.TestCase):
    """Tests for NoValidWorldRectError exception."""

    def test_instantiation_with_type(self) -> None:
        """Test that NoValidWorldRectError can be instantiated with a type."""
        error: NoValidWorldRectError = NoValidWorldRectError(str)
        self.assertIsInstance(error, MiniworldsError)

    def test_message_describes_rect_requirement(self) -> None:
        """Test that message describes rect type requirements."""
        error: NoValidWorldRectError = NoValidWorldRectError(str)
        message: str = str(error)
        self.assertIn("No valid world rect", message)


class TestCostumeOutOfBoundsError(unittest.TestCase):
    """Tests for CostumeOutOfBoundsError exception."""

    def test_instantiation_with_actor_costume_count_and_index(self) -> None:
        """Test that CostumeOutOfBoundsError can be instantiated with actor, count, and index."""

        class DummyActor:
            def __str__(self) -> str:
                return SAMPLE_ACTOR_NAME

        error: CostumeOutOfBoundsError = CostumeOutOfBoundsError(DummyActor(), 3, 5)
        self.assertIsInstance(error, MiniworldsError)

    def test_message_shows_details(self) -> None:
        """Test that message shows actor, costume count, and attempted index."""

        class DummyActor:
            def __str__(self) -> str:
                return SAMPLE_ACTOR_NAME

        error: CostumeOutOfBoundsError = CostumeOutOfBoundsError(DummyActor(), 3, 5)
        message: str = str(error)
        self.assertIn(SAMPLE_ACTOR_NAME, message)
        self.assertIn("3 costumes", message)
        self.assertIn("5", message)
        self.assertIn("counted from 0", message)


class TestNoCostumeSetError(unittest.TestCase):
    """Tests for NoCostumeSetError exception."""

    def test_instantiation_with_actor(self) -> None:
        """Test that NoCostumeSetError can be instantiated with an actor."""

        class DummyActor:
            def __str__(self) -> str:
                return SAMPLE_ACTOR_NAME

        error: NoCostumeSetError = NoCostumeSetError(DummyActor())
        self.assertIsInstance(error, MiniworldsError)

    def test_message_identifies_actor_and_issue(self) -> None:
        """Test that message identifies the actor and the issue."""

        class DummyActor:
            def __str__(self) -> str:
                return SAMPLE_ACTOR_NAME

        error: NoCostumeSetError = NoCostumeSetError(DummyActor())
        message: str = str(error)
        self.assertIn(SAMPLE_ACTOR_NAME, message)
        self.assertIn("no costume", message.lower())


class TestSizeOnTiledWorldError(unittest.TestCase):
    """Tests for SizeOnTiledWorldError exception."""

    def test_instantiation_without_arguments(self) -> None:
        """Test that SizeOnTiledWorldError can be instantiated without arguments."""
        error: SizeOnTiledWorldError = SizeOnTiledWorldError()
        self.assertIsInstance(error, MiniworldsError)

    def test_message_explains_tiled_world_constraint(self) -> None:
        """Test that message explains size constraint on tiled worlds."""
        error: SizeOnTiledWorldError = SizeOnTiledWorldError()
        message: str = str(error)
        self.assertIn("can't set size", message.lower())
        self.assertIn("tiled world", message.lower())


class TestActorArgumentShouldBeTuple(unittest.TestCase):
    """Tests for ActorArgumentShouldBeTuple exception."""

    def test_instantiation_without_arguments(self) -> None:
        """Test that ActorArgumentShouldBeTuple can be instantiated without arguments."""
        error: ActorArgumentShouldBeTuple = ActorArgumentShouldBeTuple()
        self.assertIsInstance(error, MiniworldsError)

    def test_message_describes_first_argument_requirement(self) -> None:
        """Test that message describes the first argument should be a tuple."""
        error: ActorArgumentShouldBeTuple = ActorArgumentShouldBeTuple()
        message: str = str(error)
        self.assertIn("First argument", message)
        self.assertIn("Tuple", message)


class TestPhysicsSimulationTypeError(unittest.TestCase):
    """Tests for PhysicsSimulationTypeError exception."""

    def test_instantiation_without_arguments(self) -> None:
        """Test that PhysicsSimulationTypeError can be instantiated without arguments."""
        error: PhysicsSimulationTypeError = PhysicsSimulationTypeError()
        self.assertIsInstance(error, MiniworldsError)

    def test_message_lists_valid_simulation_types(self) -> None:
        """Test that message lists all valid simulation type values."""
        error: PhysicsSimulationTypeError = PhysicsSimulationTypeError()
        message: str = str(error)
        self.assertIn("Physics simulation", message)
        self.assertIn("None", message)
        self.assertIn("static", message)
        self.assertIn("manual", message)
        self.assertIn("simulated", message)


class TestActorClassNotFound(unittest.TestCase):
    """Tests for ActorClassNotFound exception."""

    def test_instantiation_with_class_name(self) -> None:
        """Test that ActorClassNotFound can be instantiated with a class name."""
        error: ActorClassNotFound = ActorClassNotFound("NonExistentClass")
        self.assertIsInstance(error, MiniworldsError)

    def test_message_identifies_missing_class(self) -> None:
        """Test that message identifies the missing actor class."""
        class_name: str = "NonExistentClass"
        error: ActorClassNotFound = ActorClassNotFound(class_name)
        message: str = str(error)
        self.assertIn(class_name, message)
        self.assertIn("not found", message.lower())


class TestCantSetAutoFontSize(unittest.TestCase):
    """Tests for CantSetAutoFontSize exception."""

    def test_instantiation_without_arguments(self) -> None:
        """Test that CantSetAutoFontSize can be instantiated without arguments."""
        error: CantSetAutoFontSize = CantSetAutoFontSize()
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_auto_font_size(self) -> None:
        """Test that message mentions auto_font_size setting."""
        error: CantSetAutoFontSize = CantSetAutoFontSize()
        message: str = str(error)
        self.assertIn("auto_font_size", message.lower())
        self.assertIn("font-size", message.lower())


class TestNotImplementedOrRegisteredError(unittest.TestCase):
    """Tests for NotImplementedOrRegisteredError exception."""

    def test_instantiation_with_regular_method(self) -> None:
        """Test instantiation with a regular method."""

        class DummyClass:
            def some_method(self) -> None:
                pass

        error: NotImplementedOrRegisteredError = NotImplementedOrRegisteredError(
            DummyClass.some_method
        )
        self.assertIsInstance(error, MiniworldsError)

    def test_message_includes_method_name(self) -> None:
        """Test that message includes the method name."""

        class DummyClass:
            def some_method(self) -> None:
                pass

        error: NotImplementedOrRegisteredError = NotImplementedOrRegisteredError(
            DummyClass.some_method
        )
        message: str = str(error)
        self.assertIn("some_method", message)

    def test_suggests_signature_for_on_key_down(self) -> None:
        """Test that error suggests correct signature for on_key_down."""

        class DummyClass:
            def on_key_down(self, key: str) -> None:
                pass

        error: NotImplementedOrRegisteredError = NotImplementedOrRegisteredError(
            DummyClass.on_key_down
        )
        message: str = str(error)
        self.assertIn("on_key_down", message)
        self.assertIn("def on_key_down(self, key):", message)

    def test_suggests_signature_for_on_setup(self) -> None:
        """Test that error suggests correct signature for on_setup."""

        class DummyClass:
            def on_setup(self) -> None:
                pass

        error: NotImplementedOrRegisteredError = NotImplementedOrRegisteredError(
            DummyClass.on_setup
        )
        message: str = str(error)
        self.assertIn("on_setup", message)
        self.assertIn("def on_setup(self):", message)


class TestEllipseWrongArgumentsError(unittest.TestCase):
    """Tests for EllipseWrongArgumentsError exception."""

    def test_instantiation_without_arguments(self) -> None:
        """Test that EllipseWrongArgumentsError can be instantiated without arguments."""
        error: EllipseWrongArgumentsError = EllipseWrongArgumentsError()
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_ellipse(self) -> None:
        """Test that message mentions Ellipse."""
        error: EllipseWrongArgumentsError = EllipseWrongArgumentsError()
        message: str = str(error)
        self.assertIn("Ellipse", message)


class TestRectFirstArgumentError(unittest.TestCase):
    """Tests for RectFirstArgumentError exception."""

    def test_instantiation_with_invalid_position(self) -> None:
        """Test that RectFirstArgumentError can be instantiated with invalid position."""
        error: RectFirstArgumentError = RectFirstArgumentError("invalid_position")
        self.assertIsInstance(error, MiniworldsError)

    def test_message_identifies_first_argument_issue(self) -> None:
        """Test that message identifies first argument should be position."""
        error: RectFirstArgumentError = RectFirstArgumentError("invalid_position")
        message: str = str(error)
        self.assertIn("First argument", message)
        self.assertIn("position", message.lower())


class TestLineFirstArgumentError(unittest.TestCase):
    """Tests for LineFirstArgumentError exception."""

    def test_instantiation_with_invalid_start_position(self) -> None:
        """Test that LineFirstArgumentError can be instantiated with invalid position."""
        error: LineFirstArgumentError = LineFirstArgumentError("invalid_position")
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_start_position(self) -> None:
        """Test that message mentions start_position."""
        error: LineFirstArgumentError = LineFirstArgumentError("invalid_position")
        message: str = str(error)
        self.assertIn("start_position", message.lower())


class TestLineSecondArgumentError(unittest.TestCase):
    """Tests for LineSecondArgumentError exception."""

    def test_instantiation_with_invalid_end_position(self) -> None:
        """Test that LineSecondArgumentError can be instantiated with invalid position."""
        error: LineSecondArgumentError = LineSecondArgumentError("invalid_position")
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_end_position(self) -> None:
        """Test that message mentions end_position."""
        error: LineSecondArgumentError = LineSecondArgumentError("invalid_position")
        message: str = str(error)
        self.assertIn("end_position", message.lower())


class TestNoWorldError(unittest.TestCase):
    """Tests for NoWorldError exception."""

    def test_instantiation_without_arguments(self) -> None:
        """Test that NoWorldError can be instantiated without arguments."""
        error: NoWorldError = NoWorldError()
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_world_requirement(self) -> None:
        """Test that message mentions world requirement."""
        error: NoWorldError = NoWorldError()
        message: str = str(error)
        self.assertIn("world", message.lower())


class TestImageIndexNotExistsError(unittest.TestCase):
    """Tests for ImageIndexNotExistsError exception."""

    def test_instantiation_with_appearance_and_index(self) -> None:
        """Test that ImageIndexNotExistsError can be instantiated with appearance and index."""
        error: ImageIndexNotExistsError = ImageIndexNotExistsError("appearance", 5)
        self.assertIsInstance(error, MiniworldsError)

    def test_message_identifies_missing_index(self) -> None:
        """Test that message identifies the missing image index."""
        error: ImageIndexNotExistsError = ImageIndexNotExistsError("appearance", 5)
        message: str = str(error)
        self.assertIn("image", message.lower())


class TestTileNotFoundError(unittest.TestCase):
    """Tests for TileNotFoundError exception."""

    def test_instantiation_with_position(self) -> None:
        """Test that TileNotFoundError can be instantiated with a position."""
        error: TileNotFoundError = TileNotFoundError((10, 20))
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_tile_and_position(self) -> None:
        """Test that message mentions tile and position."""
        error: TileNotFoundError = TileNotFoundError((10, 20))
        message: str = str(error)
        self.assertIn("tile", message.lower())


class TestCornerNotFoundError(unittest.TestCase):
    """Tests for CornerNotFoundError exception."""

    def test_instantiation_with_position(self) -> None:
        """Test that CornerNotFoundError can be instantiated with a position."""
        error: CornerNotFoundError = CornerNotFoundError((10, 20))
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_corner_and_position(self) -> None:
        """Test that message mentions corner and position."""
        error: CornerNotFoundError = CornerNotFoundError((10, 20))
        message: str = str(error)
        self.assertIn("corner", message.lower())


class TestEdgeNotFoundError(unittest.TestCase):
    """Tests for EdgeNotFoundError exception."""

    def test_instantiation_with_position(self) -> None:
        """Test that EdgeNotFoundError can be instantiated with a position."""
        error: EdgeNotFoundError = EdgeNotFoundError((10, 20))
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_edge_and_position(self) -> None:
        """Test that message mentions edge and position."""
        error: EdgeNotFoundError = EdgeNotFoundError((10, 20))
        message: str = str(error)
        self.assertIn("edge", message.lower())


class TestRegisterError(unittest.TestCase):
    """Tests for RegisterError exception."""

    def test_instantiation_with_method_and_instance(self) -> None:
        """Test that RegisterError can be instantiated with method and instance."""

        class DummyActor:
            pass

        error: RegisterError = RegisterError(SAMPLE_METHOD_NAME, DummyActor())
        self.assertIsInstance(error, MiniworldsError)

    def test_message_identifies_registration_failure(self) -> None:
        """Test that message identifies the registration failure."""

        class DummyActor:
            pass

        error: RegisterError = RegisterError(SAMPLE_METHOD_NAME, DummyActor())
        message: str = str(error)
        self.assertIn(SAMPLE_METHOD_NAME, message)


class TestMissingActorPartsError(unittest.TestCase):
    """Tests for MissingActorPartsError exception and its subclasses."""

    def test_instantiation_with_message(self) -> None:
        """Test that MissingActorPartsError can be instantiated with a message."""
        error: MissingActorPartsError = MissingActorPartsError("test message")
        self.assertIsInstance(error, MiniworldsError)
        self.assertEqual(str(error), "test message")


class TestMissingPositionManager(unittest.TestCase):
    """Tests for MissingPositionManager exception."""

    def test_instantiation_with_actor(self) -> None:
        """Test that MissingPositionManager can be instantiated with an actor."""

        class DummyActor:
            pass

        error: MissingPositionManager = MissingPositionManager(DummyActor())
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_position_manager(self) -> None:
        """Test that message mentions position manager."""

        class DummyActor:
            pass

        error: MissingPositionManager = MissingPositionManager(DummyActor())
        message: str = str(error)
        self.assertIn("position", message.lower())


class TestMissingworldsensor(unittest.TestCase):
    """Tests for Missingworldsensor exception."""

    def test_instantiation_with_actor(self) -> None:
        """Test that Missingworldsensor can be instantiated with an actor."""

        class DummyActor:
            pass

        error: Missingworldsensor = Missingworldsensor(DummyActor())
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_sensor(self) -> None:
        """Test that message mentions sensor."""

        class DummyActor:
            pass

        error: Missingworldsensor = Missingworldsensor(DummyActor())
        message: str = str(error)
        self.assertIn("sensor", message.lower())


class TestOriginException(unittest.TestCase):
    """Tests for OriginException exception."""

    def test_instantiation_with_actor(self) -> None:
        """Test that OriginException can be instantiated with an actor."""

        class DummyActor:
            pass

        error: OriginException = OriginException(DummyActor())
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_origin(self) -> None:
        """Test that message mentions origin setting."""

        class DummyActor:
            pass

        error: OriginException = OriginException(DummyActor())
        message: str = str(error)
        self.assertIn("origin", message.lower())


class TestWrongFilterType(unittest.TestCase):
    """Tests for WrongFilterType exception."""

    def test_instantiation_with_actor(self) -> None:
        """Test that WrongFilterType can be instantiated with an actor."""

        class DummyActor:
            pass

        error: WrongFilterType = WrongFilterType(DummyActor())
        self.assertIsInstance(error, MiniworldsError)

    def test_message_mentions_filter(self) -> None:
        """Test that message mentions filter type."""

        class DummyActor:
            pass

        error: WrongFilterType = WrongFilterType(DummyActor())
        message: str = str(error)
        self.assertIn("filter", message.lower())


class TestExceptionInheritance(unittest.TestCase):
    """Tests to verify all exceptions inherit from MiniworldsError."""

    def test_all_exceptions_inherit_from_miniworlds_error(self) -> None:
        """Verify all custom exceptions inherit from MiniworldsError."""
        exceptions_to_test: list = [
            NoRunError,
            MoveInDirectionTypeError,
            WorldInstanceError,
            WorldArgumentsError,
            TiledWorldTooBigError,
            FileNotFoundError,
            WrongArgumentsError,
            CostumeIsNoneError,
            NotCallableError,
            NotNullError,
            FirstArgumentShouldBeSelfError,
            ColorException,
            NoValidWorldPositionError,
            NoValidPositionOnInitException,
            NoValidWorldRectError,
            CostumeOutOfBoundsError,
            NoCostumeSetError,
            SizeOnTiledWorldError,
            ActorArgumentShouldBeTuple,
            PhysicsSimulationTypeError,
            ActorClassNotFound,
            CantSetAutoFontSize,
            NotImplementedOrRegisteredError,
            EllipseWrongArgumentsError,
            RectFirstArgumentError,
            LineFirstArgumentError,
            LineSecondArgumentError,
            NoWorldError,
            ImageIndexNotExistsError,
            TileNotFoundError,
            CornerNotFoundError,
            EdgeNotFoundError,
            RegisterError,
            MissingActorPartsError,
            MissingPositionManager,
            Missingworldsensor,
            OriginException,
            WrongFilterType,
        ]

        for exc_class in exceptions_to_test:
            with self.subTest(exception_class=exc_class):
                self.assertTrue(
                    issubclass(exc_class, MiniworldsError),
                    f"{exc_class.__name__} should inherit from MiniworldsError",
                )


if __name__ == "__main__":
    unittest.main()
