from miniworlds import App, TiledWorld, Actor, CostumeOutOfBoundsError
from .screenshot_tester import ScreenshotTester
import unittest
import os
import random


class Test1206(unittest.TestCase):
    def setUp(self):
        def test_code():
            # Create a tiled world with 6 rows and 6 columns
            world = TiledWorld(6, 6)

            # Define and register the setup method for this world
            @world.register
            def setup_environment(self, test):
                # Print and verify world dimensions
                assert world.rows == 6
                assert world.columns == 6

                # Fill the background with varying grayscale rectangles
                for x in range(world.rows):
                    for y in range(world.columns):
                        color = (x * y) / (world.rows * world.columns) * 255
                        world.background.draw(
                            (color, color, color),
                            (x * world.tile_size, y * world.tile_size),
                            40,
                            40,
                        )

                # Create an actor at position (3, 3) using top-left as origin
                actor = Actor((3, 3), origin="topleft")

                assert actor.position == (3, 3)
                # Print and verify color detection at the actor's position
                print(actor.detect_color((63, 63, 63)))
                assert actor.detect_color((63, 63, 63)) is True

                # Check detected color in front of the actor (direction 90°, 1 tile ahead)
                assert actor.detect_color_at(distance=1, direction=90) == (85, 85, 85, 255)

            return world

        # Reset Miniworlds application state for testing
        App.reset(unittest=True, file=__file__)

        # Create the world and assign it
        world = test_code()

        # Set up screenshot-based tester
        TEST_FRAMES = [1]       # Frame(s) to capture
        QUIT_FRAME = 1          # Stop simulation after this frame
        tester = ScreenshotTester(TEST_FRAMES, QUIT_FRAME, self)
        tester.setup(world)

        # Call the registered world setup method
        if hasattr(world, "setup_environment"):
            world.setup_environment(self)

        # Store the world on the test case instance
        self.world = world

        return world

    def test_main(self):
        # Expect the app to quit after reaching QUIT_FRAME
        with self.assertRaises(SystemExit):
            self.world.run()


if __name__ == "__main__":
    unittest.main()
