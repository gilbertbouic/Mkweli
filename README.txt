MkweliAML - Open-Source AML & KYC Tool for Low-Budget Users

Overview:
- Free, local sanctions screening using official sources (UN, OFAC, UK, EU, Canada).
- Auto-fetches lists on startup; stores in local DB (no cloud to avoid manipulation).
- Manual uploads fallback. Data retained offline.
- Setup: python init_db.py; python app.py
- Offline: Comment @app.before_first_request in app.py.
- Logs: Check logs/app.log for errors (e.g., format changes).
- Tests: Run python -m unittest tests/test_parsers.py for parser validation.

Requirements: See requirements.txt (no extras needed).

For format changes: Manual upload or update parsers in app.py.
