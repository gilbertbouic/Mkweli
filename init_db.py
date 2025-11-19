# init_db.py - CLI: Creates DB/tables/user. Run: python init_db.py (all OS).
from app import app, db  # Safe: app.py defines db without running routes yet
from models import User
from sqlalchemy import text  # For textual SQL

def init_database():
    try:
        with app.app_context():
            db.create_all()  # Creates if missing
            db.session.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(name, alias_name, content='aliases', tokenize='porter')"))
            db.session.commit()
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', password='securepassword123')
                db.session.add(admin)
                db.session.commit()
            print("DB initialized.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    init_database()
