from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from miniworlds.worlds.data.export_factory import (
    ExportActorsFactory,
    ExportActorsToDBFactory,
    ExportDBFactory,
    ExportWorldToDBFactory,
)
from miniworlds.worlds.data.import_factory import ImportActorsFromDB, ImportWorldFromDB


class Hero:
    def __init__(self, position=(0, 0), world=None):
        self.position = position
        self.world = world
        self.direction = 0


class VisibleActor(Hero):
    pass


class HiddenActor(Hero):
    export = False


class ExplicitActor(Hero):
    export = True


class SavedWorld:
    def __init__(self):
        self.rows = 6
        self.columns = 8
        self.tile_size = 32


class ImportedWorld:
    pass


class TestImportExportFactory(unittest.TestCase):
    def test_export_actors_factory_skips_non_exportable_actors(self):
        visible_actor = VisibleActor((1, 2))
        visible_actor.direction = 90
        hidden_actor = HiddenActor((3, 4))
        hidden_actor.direction = 180
        explicit_actor = ExplicitActor((5, 6))
        explicit_actor.direction = 270

        factory = ExportActorsFactory([visible_actor, hidden_actor, explicit_actor])

        self.assertEqual(
            factory.actors_serialized,
            [
                {"x": 1, "y": 2, "direction": 90, "actor_class": "VisibleActor"},
                {"x": 5, "y": 6, "direction": 270, "actor_class": "ExplicitActor"},
            ],
        )

    def test_export_db_factory_remove_file_recreates_db_manager(self):
        first_db = MagicMock()
        second_db = MagicMock()

        with patch(
            "miniworlds.worlds.data.export_factory.db_manager.DBManager",
            side_effect=[first_db, second_db],
        ):
            factory = ExportDBFactory("save.db")
            with patch(
                "miniworlds.worlds.data.export_factory.os.path.exists",
                return_value=True,
            ) as path_exists:
                with patch("miniworlds.worlds.data.export_factory.os.remove") as remove_file:
                    factory.remove_file()

        path_exists.assert_called_once_with("save.db")
        remove_file.assert_called_once_with("save.db")
        self.assertIs(factory.db, second_db)

    def test_export_world_to_db_saves_world_metadata(self):
        db = MagicMock()
        db.cursor = MagicMock()
        world = SavedWorld()

        with patch(
            "miniworlds.worlds.data.export_factory.db_manager.DBManager",
            return_value=db,
        ):
            factory = ExportWorldToDBFactory("save.db", world)
            factory.save()

        db.cursor.execute.assert_called_once()
        db.insert.assert_called_once_with(
            table="world",
            row={
                "world_class": "SavedWorld",
                "tile_size": 32,
                "height": 6,
                "width": 8,
            },
        )
        self.assertEqual(db.commit.call_count, 2)
        db.close_connection.assert_called_once_with()

    def test_export_actors_to_db_saves_only_serialized_actors(self):
        db = MagicMock()
        db.cursor = MagicMock()
        visible_actor = VisibleActor((2, 3))
        visible_actor.direction = 45
        hidden_actor = HiddenActor((4, 5))
        hidden_actor.direction = 180
        explicit_actor = ExplicitActor((6, 7))
        explicit_actor.direction = 315

        with patch(
            "miniworlds.worlds.data.export_factory.db_manager.DBManager",
            return_value=db,
        ):
            factory = ExportActorsToDBFactory(
                "save.db", [visible_actor, hidden_actor, explicit_actor]
            )
            factory.save()

        db.cursor.execute.assert_called_once()
        self.assertEqual(
            db.insert.call_args_list,
            [
                unittest.mock.call(
                    table="actor",
                    row={
                        "x": 2,
                        "y": 3,
                        "direction": 45,
                        "actor_class": "VisibleActor",
                    },
                ),
                unittest.mock.call(
                    table="actor",
                    row={
                        "x": 6,
                        "y": 7,
                        "direction": 315,
                        "actor_class": "ExplicitActor",
                    },
                ),
            ],
        )
        self.assertEqual(db.commit.call_count, 2)
        db.close_connection.assert_called_once_with()

    def test_import_world_from_db_sets_loaded_state(self):
        db = MagicMock()
        db.select_single_row.return_value = ("StoredWorld", 11, 12, 24)

        with patch(
            "miniworlds.worlds.data.import_factory.db_manager.DBManager",
            return_value=db,
        ):
            loader = ImportWorldFromDB("save.db", ImportedWorld)
            world = loader.load()

        self.assertIsInstance(world, ImportedWorld)
        self.assertEqual(world.columns, 11)
        self.assertEqual(world.rows, 12)
        self.assertEqual(world.tile_size, 24)
        self.assertTrue(world._loaded_from_db)
        db.close_connection.assert_called_once_with()

    def test_import_actors_from_db_matches_case_insensitive_names(self):
        db = MagicMock()
        db.select_all_rows.return_value = [
            (1, "hero", 4, 5, 90),
            (2, "UnknownActor", 9, 9, 180),
        ]
        world = SimpleNamespace()

        with patch(
            "miniworlds.worlds.data.import_factory.db_manager.DBManager",
            return_value=db,
        ):
            loader = ImportActorsFromDB("save.db", [Hero], world)
            actors = loader.load()

        self.assertEqual(len(actors), 1)
        self.assertIsInstance(actors[0], Hero)
        self.assertEqual(actors[0].position, (4, 5))
        self.assertEqual(actors[0].direction, 90)
        self.assertIs(actors[0].world, world)
        db.close_connection.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()