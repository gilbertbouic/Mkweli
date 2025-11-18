import sqlite3
import os

def init_database():
    # Connect to the SQLite database (it will be created if it doesn't exist)
    connection = sqlite3.connect('mkweli_aml.db')
    cursor = connection.cursor()

    # 1. Table for storing clients (KYC data)
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

    # 2. Table for storing sanctions lists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sanctions_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_list TEXT NOT NULL, -- e.g., 'OFAC', 'UN'
            original_id TEXT, -- The ID from the original list
            full_name TEXT NOT NULL,
            other_info TEXT, -- Could include address, type of sanction, etc.
            list_version_date TEXT -- To track when this entry was added from the source
        )
    ''')

    # 3. Table for audit logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_action TEXT NOT NULL,
            client_id INTEGER, -- Can be NULL if action isn't client-specific
            details TEXT,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    ''')

    # 4. Table to track the last update of each sanctions list
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS list_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_name TEXT UNIQUE NOT NULL, -- e.g., 'OFAC SDN'
            last_updated TIMESTAMP
        )
    ''')

    # 5. System authentication table
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

    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(full_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sanctions_name ON sanctions_list(full_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')

    # Initialize system auth if not exists
    cursor.execute('SELECT system_id FROM system_auth LIMIT 1')
    if not cursor.fetchone():
        import secrets
        system_id = secrets.token_hex(16)
        cursor.execute(
            'INSERT INTO system_auth (system_id, master_password_hash) VALUES (?, ?)',
            (system_id, '')  # Empty until first setup
        )

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

    print("MkweliAML Professional Edition database initialized successfully!")
    print("System ready for master password setup on first launch.")

if __name__ == '__main__':
    init_database()
