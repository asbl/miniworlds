from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from miniworlds import Actor, World
from miniworlds.base.app import App


class TestPersistenceRoundtrip(unittest.TestCase):
    def tearDown(self):
        App.reset(unittest=True, file=__file__)

    def test_world_save_and_load_roundtrip_preserves_dimensions(self):
        App.reset(unittest=True, file=__file__)
        world = World(120, 90)

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "world.db"
            world.save_to_db(str(db_path))

            world.switch_world = Mock()
            loaded_world = world.load_world_from_db(str(db_path))

            self.assertEqual(loaded_world.columns, 120)
            self.assertEqual(loaded_world.rows, 90)
            world.switch_world.assert_called_once_with(loaded_world)

    def test_actor_save_and_load_roundtrip_preserves_position_and_direction(self):
        App.reset(unittest=True, file=__file__)
        source_world = World(100, 100)
        actor = Actor((7, 9), world=source_world)
        actor.direction = 135

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "actors.db"
            source_world.save_to_db(str(db_path))

            target_world = World(40, 40)
            loaded_actors = target_world.load_actors_from_db(str(db_path), [Actor])

            self.assertEqual(len(loaded_actors), 1)
            loaded_actor = loaded_actors[0]
            self.assertEqual(loaded_actor.position, (7, 9))
            self.assertEqual(loaded_actor.direction, 135)
            self.assertIs(loaded_actor.world, target_world)


if __name__ == "__main__":
    unittest.main()