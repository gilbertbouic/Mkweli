import sqlite3
import threading
from contextlib import contextmanager

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._local = threading.local()
    
    def get_connection(self):
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    
    def close(self):
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection

# Initialize database instance
db = Database('mkweli_aml.db')
