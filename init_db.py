# init_db.py - CLI: Creates DB/tables/user. Run: python init_db.py (all OS).
from app import app, db  # Safe: app.py defines db without running routes yet
from models import User

def init_database():
    try:
        with app.app_context():
            db.create_all()  # Creates if missing
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', password='securepassword123')
                db.session.add(admin)
                db.session.commit()
            print("DB initialized.")  # Feedback
    except Exception as e:
        print(f"Error: {str(e)}")  # User-friendly

if __name__ == '__main__':
    init_database()
