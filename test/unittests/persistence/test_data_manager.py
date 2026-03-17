import unittest
from unittest.mock import MagicMock, patch

from miniworlds.worlds.manager.data_manager import DataManager


class DummyWorld:
    def __init__(self):
        self.switch_world = MagicMock()
        self.actors = [MagicMock()]


class TestDataManager(unittest.TestCase):
    def test_load_world_from_db_switches_to_loaded_world(self):
        world = DummyWorld()
        data_manager = DataManager(world, MagicMock())
        loader = MagicMock()
        loaded_world = MagicMock()
        loader.load.return_value = loaded_world

        with patch(
            "miniworlds.worlds.manager.data_manager.import_factory.ImportWorldFromDB",
            return_value=loader,
        ) as import_world:
            result = data_manager.load_world_from_db("save.db")

        import_world.assert_called_once_with("save.db", world.__class__)
        world.switch_world.assert_called_once_with(loaded_world)
        self.assertIs(result, loaded_world)

    def test_save_to_db_exports_world_then_actors(self):
        world = DummyWorld()
        data_manager = DataManager(world, MagicMock())
        world_export = MagicMock()
        actor_export = MagicMock()

        with patch(
            "miniworlds.worlds.manager.data_manager.export_factory.ExportWorldToDBFactory",
            return_value=world_export,
        ) as export_world:
            with patch(
                "miniworlds.worlds.manager.data_manager.export_factory.ExportActorsToDBFactory",
                return_value=actor_export,
            ) as export_actors:
                data_manager.save_to_db("save.db")

        export_world.assert_called_once_with("save.db", world)
        world_export.remove_file.assert_called_once_with()
        world_export.save.assert_called_once_with()
        export_actors.assert_called_once_with("save.db", world.actors)
        actor_export.save.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()