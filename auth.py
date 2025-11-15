import hashlib
import secrets
from datetime import datetime, timedelta
from database import db

class AuthSystem:
    def __init__(self):
        self._init_auth_table()
    
    def _init_auth_table(self):
        with db.get_cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_auth (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    master_password_hash TEXT NOT NULL,
                    setup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP NULL,
                    system_id TEXT UNIQUE NOT NULL
                )
            ''')
            
            cursor.execute('SELECT system_id FROM system_auth LIMIT 1')
            if not cursor.fetchone():
                system_id = secrets.token_hex(16)
                cursor.execute(
                    'INSERT INTO system_auth (system_id, master_password_hash) VALUES (?, ?)',
                    (system_id, '')
                )
    
    def setup_master_password(self, password):
        with db.get_cursor() as cursor:
            password_hash = self._hash_password(password)
            cursor.execute(
                'UPDATE system_auth SET master_password_hash = ?, setup_date = CURRENT_TIMESTAMP',
                (password_hash,)
            )
        return True
    
    def verify_password(self, password):
        with db.get_cursor() as cursor:
            cursor.execute(
                'SELECT master_password_hash, failed_attempts, locked_until FROM system_auth LIMIT 1'
            )
            result = cursor.fetchone()
            
            if not result:
                return False
            
            stored_hash, failed_attempts, locked_until = result
            
            if locked_until and datetime.now() < datetime.fromisoformat(locked_until):
                return False
            
            if self._hash_password(password) == stored_hash:
                cursor.execute(
                    'UPDATE system_auth SET failed_attempts = 0, last_login = CURRENT_TIMESTAMP, locked_until = NULL'
                )
                return True
            else:
                failed_attempts += 1
                if failed_attempts >= 5:
                    lock_time = datetime.now() + timedelta(minutes=30)
                    cursor.execute(
                        'UPDATE system_auth SET failed_attempts = ?, locked_until = ?',
                        (failed_attempts, lock_time.isoformat())
                    )
                else:
                    cursor.execute(
                        'UPDATE system_auth SET failed_attempts = ?',
                        (failed_attempts,)
                    )
                return False
    
    def is_password_set(self):
        with db.get_cursor() as cursor:
            cursor.execute('SELECT master_password_hash FROM system_auth LIMIT 1')
            result = cursor.fetchone()
            return result and result[0] != ''
    
    def get_system_id(self):
        with db.get_cursor() as cursor:
            cursor.execute('SELECT system_id FROM system_auth LIMIT 1')
            result = cursor.fetchone()
            return result[0] if result else None
    
    def _hash_password(self, password):
        salt = "mkweli_aml_2023_salt"
        return hashlib.sha256((password + salt).encode()).hexdigest()
