import sqlite3
import os
import pandas as pd
from datetime import datetime

def init_database():
    connection = sqlite3.connect('mkweli_aml.db')
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            id_number TEXT,
            date_of_birth TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            risk_score INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sanctions_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_list TEXT NOT NULL,
            original_id TEXT,
            full_name TEXT NOT NULL,
            other_info TEXT,
            list_version_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_action TEXT NOT NULL,
            client_id INTEGER,
            details TEXT,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS list_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_name TEXT UNIQUE NOT NULL,
            last_updated TIMESTAMP
        )
    ''')

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(full_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sanctions_name ON sanctions_list(full_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')

    cursor.execute('SELECT system_id FROM system_auth LIMIT 1')
    if not cursor.fetchone():
        import secrets
        system_id = secrets.token_hex(16)
        cursor.execute(
            'INSERT INTO system_auth (system_id, master_password_hash) VALUES (?, ?)',
            (system_id, '')
        )

    # Load initial sanctions from database.xlsx if exists and table empty
    xlsx_path = 'database.xlsx'
    cursor.execute('SELECT COUNT(*) FROM sanctions_list')
    if cursor.fetchone()[0] == 0 and os.path.exists(xlsx_path):
        try:
            xls = pd.ExcelFile(xlsx_path)
            imported_count = 0
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                names = [str(cell).split(':', 1)[-1].strip() if ':' in str(cell) else str(cell).strip() for cell in df.iloc[:, 0] if pd.notna(cell) and str(cell).strip()]
                for name in names:
                    cursor.execute('''
                        INSERT INTO sanctions_list (source_list, full_name, other_info, list_version_date)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (sheet_name.upper(), name, 'From official UK/US/UN lists',))
                imported_count += len(names)
                cursor.execute('''
                    INSERT OR REPLACE INTO list_metadata (list_name, last_updated)
                    VALUES (?, CURRENT_TIMESTAMP)
                ''', (sheet_name.upper(),))
            print(f'Imported {imported_count} sanctions entries from database.xlsx')
        except Exception as e:
            print(f'Error loading XLSX: {str(e)}')

    connection.commit()
    connection.close()

    print("MkweliAML database initialized successfully!")

if __name__ == '__main__':
    init_database()
