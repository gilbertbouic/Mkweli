# extensions.py - Initializes extensions like SQLAlchemy (avoids circular imports).
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # Instance created here; bound later in app.py
