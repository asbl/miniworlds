import tempfile
import unittest
from pathlib import Path

from miniworlds.worlds.data.db_manager import DBManager


class TestDBManager(unittest.TestCase):
    def test_insert_uses_parameterized_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "world.db"
            db = DBManager(str(db_path))
            self.addCleanup(db.close_connection)
            db.cursor.execute("CREATE TABLE test_data (name TEXT, value INTEGER)")

            db.insert("test_data", {"name": "O'Reilly", "value": 7})
            db.commit()

            row = db.select_single_row("SELECT name, value FROM test_data")

            self.assertEqual(row, ("O'Reilly", 7))


if __name__ == "__main__":
    unittest.main()