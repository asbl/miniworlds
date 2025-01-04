import os
import miniworlds.worlds.data.db_manager as db_manager


class ExportFactory():

    def save(self):
        """
        Implemented in concrete factory
        """
        pass


class ExportDBFactory:
    def __init__(self, file):
        self.file = file
        self.db = db_manager.DBManager(file)

    def remove_file(self):
        if os.path.exists(self.file):
            os.remove(self.file)
        self.db = db_manager.DBManager(self.file)

class ExportWorldFactory:
    def __init__(self, world):
        self.world = world


class ExportActorsFactory:
    def __init__(self, actors):
        self.actors = actors
        self.actors_serialized = list()
        for actor in self.actors:
            if not (hasattr(actor, "export") and actor.export == False):
                actor_dict = {"x": actor.position[0],
                            "y": actor.position[1],
                            "direction": actor.direction,
                            "actor_class": actor.__class__.__name__}
                self.actors_serialized.append(actor_dict)


class ExportWorldToDBFactory(ExportFactory, ExportDBFactory, ExportWorldFactory):
    def __init__(self, file, world):
        ExportDBFactory.__init__(self, file)
        ExportWorldFactory.__init__(self, world)

    def save(self):
        query_world = """CREATE TABLE `world` (
                        `world_class`   TEXT,
                        `tile_size`		INTEGER,
                        `height`		INTEGER,
                        `width`		    INTEGER
                        );
                        """
        cur = self.db.cursor
        cur.execute(query_world)
        self.db.commit()
        world_dict = {"world_class": self.world.__class__.__name__,
                      "tile_size": self.world.tile_size,
                      "height": self.world.rows,
                      "width": self.world.columns,                      
                      }
        self.db.insert(table="world", row=world_dict)
        self.db.commit()
        self.db.close_connection()


class ExportActorsToDBFactory(ExportFactory, ExportDBFactory, ExportActorsFactory):
    def __init__(self, file, actors):
        ExportDBFactory.__init__(self, file)
        ExportActorsFactory.__init__(self, actors)

    def save(self):
        query_actors = """     CREATE TABLE `actor` (
                        `actor_id`		INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                        `x`			    INTEGER,
                        `y`		        INTEGER,
                        `direction`     FLOAT,
                        `actor_class`	TEXT
                        );
                        """
        cur = self.db.cursor
        cur.execute(query_actors)
        self.db.commit()
        for row in self.actors_serialized:
            self.db.insert(table="actor", row=row)
        self.db.commit()
        self.db.close_connection()

