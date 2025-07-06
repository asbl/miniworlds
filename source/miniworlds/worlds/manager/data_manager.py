from typing import Tuple, Union, Optional, List, cast, Callable
import miniworlds.actors.actor as actor_mod

class DataManager:

    def __init__(self, world, app):
        self.world = world  
        self.app = app  
    
    def load_world_from_db(self, file: str):
        """
        Loads a sqlite db file.
        """
        return import_factory.ImportWorldFromDB(file, self.__class__).load()

    def load_actors_from_db(
        self, file: str, actor_classes: list
    ) -> List["actor_mod.Actor"]:
        """Loads all actors from db. Usually you load the actors in __init__() or in on_setup()

        Args:
            file (str): reference to db file
            actor_classes (list): a list of all Actor Classes which should be imported.

        Returns:
            [type]: All Actors
        """
        return import_factory.ImportActorsFromDB(file, actor_classes).load()

    def save_to_db(self, file):
        """
        Saves the current world an all actors to database.
        The file is stored as db file and can be opened with sqlite.

        Args:
            file: The file as relative location

        Returns:

        """
        export = export_factory.ExportWorldToDBFactory(file, self)
        export.remove_file()
        export.save()
        export_factory.ExportActorsToDBFactory(file, self.actors).save()