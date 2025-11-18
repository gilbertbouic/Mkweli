MkweliAML - Sanctions Checker

Local run (Ubuntu/Win/Mac):
1. venv: Ubuntu/Mac - source venv/bin/activate ; Win - venv\Scripts\activate.
2. Install: pip install flask-login flask-wtf flask-sqlalchemy reportlab werkzeug
3. Init DB: python init_db.py (creates tables/user—change pw in code).
4. Run: flask run
5. Browser: http://127.0.0.1:5000 — login admin/test (change pw).

Features: Auth (login), client wizard (add/check), PDF reports (gen/view), sanctions upload/export.

Git: Branch/PR for changes.

Troubleshoot: Logs for errors, test with unittest.
