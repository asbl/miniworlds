import sqlite3
from collections.abc import Mapping

import miniworlds.base.app as app


class DBManager():

    def __init__(self, file):
        self.file = file
        self.connection = app.App.get_platform().connect_sqlite(self.file)
        self.cursor = self.connection.cursor()

    def insert(self, table: str, row: dict) -> bool:
        try:
            if not isinstance(row, Mapping) or not row:
                raise ValueError("row must be a non-empty mapping")
            cols = ", ".join(row.keys())
            placeholders = ", ".join("?" for _ in row)
            sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            self.connection.execute(sql, tuple(row.values()))
            return True
        except Exception:
            self.close_connection()
            raise

    def close_connection(self):
        self.connection.close()

    def select_single_row(self, statement: str):
        self.cursor.execute(statement)
        return self.cursor.fetchone()

    def select_all_rows(self, statement: str):
        self.cursor.execute(statement)
        return self.cursor.fetchall()

    def commit(self):
        self.connection.commit()
