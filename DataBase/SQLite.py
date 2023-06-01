import sqlite3


class SQLite:
    def __init__(self, db_file: str):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def execute(self, query: str):
        self.cursor.execute(query)

    def executemany(self, query: str, data: list):
        self.cursor.executemany(query, data)

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def commit(self):
        self.conn.commit()

    def __del__(self):
        self.cursor.close()
        self.conn.close()
