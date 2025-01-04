import miniworlds.worlds.data.db_manager as db_manager


class ImportFactory():
    def __init__(self):
        pass

    def load(self):
        """
        Implemented in subclasses
        """
        pass


class ImportWorldFactory():
    def __init__(self, world_class):
        self.world_class = world_class
        self.world = self.world_class()

class ImportActorsFactory():
    def __init__(self, actor_classes):
        self.actor_classes = actor_classes


class ImportDBFactory():
    def __init__(self, file):
        self.db = db_manager.DBManager(file)


class ImportWorldFromDB(ImportFactory, ImportDBFactory, ImportWorldFactory):
    def __init__(self, file, world):
        ImportDBFactory.__init__(self, file)
        ImportWorldFactory.__init__(self, world)

    def load(self):
        """
        Loads a sqlite db file.
        """
        data = self.db.select_single_row(
            "SELECT world_class, width, height, tile_size FROM world")
        self.world.columns = int(data[1])
        self.world.rows = int(data[2])
        self.world.tile_size = int(data[3])
        self.world._loaded_from_db = True
        self.world.switch_world(self.world)
        return self.world


class ImportActorsFromDB(ImportDBFactory, ImportActorsFactory, ImportFactory):
    def __init__(self, file, actor_classes):
        ImportDBFactory.__init__(self, file)
        ImportActorsFactory.__init__(self, actor_classes)

    def load(self):
        data = self.db.select_all_rows("SELECT actor_id, actor_class, x, y, direction FROM actor")
        if data:
            actor_list = []
            for actor_data in data:
                class_name = actor_data[1]
                x = actor_data[2]
                y = actor_data[3]
                direction = actor_data[4]
                new_actor_class_name = class_name
                for actor_class in self.actor_classes:
                    if actor_class.__name__.lower() == new_actor_class_name.lower():
                        new_actor_class = actor_class
                if new_actor_class is not None:
                    new_actor = new_actor_class(position=(x, y))  # Create actor
                    new_actor.direction = direction
                    actor_list.append(new_actor)
        return actor_list
