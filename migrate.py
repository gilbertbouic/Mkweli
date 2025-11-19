# migrate.py - CLI for DB migrations. Run: flask db <command> (e.g., init, migrate, upgrade).
from app import app, db
from flask_migrate import Migrate

migrate = Migrate(app, db)  # Init (uses Flask CLI—no deprecated script)

# Commands via flask db (built-in): flask db init; flask db migrate -m "msg"; flask db upgrade
# Error handling: Flask CLI catches issues (e.g., "No changes" OK)
