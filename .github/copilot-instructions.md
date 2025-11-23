# Mkweli AML Codebase Guide

## Project Overview
Mkweli is a **sanctions screening tool** for KYC/AML compliance. It manually loads UN, UK, OFAC, and EU sanctions lists (XML format), performs fuzzy name matching (~82% threshold), and generates SHA256-hashed PDF reports. The app runs **100% offline** after initial data import.

**Key principle**: Data-driven safety—all sanctions data is locally sourced, never downloaded programmatically.

---

## Architecture

### Component Structure (Modular + Flask Blueprints)

- **`app.py`** — Flask bootstrap (config, db binding, blueprint registration). Registers 4 blueprints: `auth`, `main`, `sanctions`, `clients`.
- **`models.py`** — SQLAlchemy models with **inline validation/sanitization** (User, Individual, Entity, Alias, Log, Sanction). Single responsibility: schema + validation.
- **`routes.py`** — Blueprint definitions for auth (login/logout), main (dashboard), sanctions (list updates).
- **`clients.py`** — Screening endpoint. CSV/Excel ingestion → `perform_screening()` → PDF generation with org details header → SHA256 log.
- **`utils.py`** — Core logic: XML parsing (UN/OFAC/UK/EU formats), fuzzy name matching (`fuzzywuzzy.fuzz`), PDF generation (`WeasyPrint`), activity logging.
- **`forms.py`** — WTForms with validators. Email login, phone regex (`^\+?[\d\s-]{7,20}$`), tax regex (`^[\w-]{5,20}$`).
- **`database.py`** — Thread-safe SQLite wrapper (context manager, row_factory).
- **`config.py`** — Config classes (Development/Production). Session timeout 30 min, 16MB max upload, HTTPONLY cookies.
- **`extensions.py`** — Shared db instance (avoids circular imports).

### Data Flow
1. Admin **manually downloads** 4 XML files → places in `/data` folder
2. **Update Lists route** → `parse_xml()` → validates/extracts fields → `incorporate_to_db()` → populates Individual/Entity/Alias/Sanction tables
3. User **uploads CSV/Excel** with [name, dob, nationality]
4. `perform_screening()` → fuzzy match (threshold 82%) against all individuals/entities → collects matches
5. `generate_pdf_report()` → renders Jinja2 template → WeasyPrint HTML→PDF → SHA256 hash
6. `log_activity()` → records report hash, IP, timestamp to Log table (audit trail)

**Critical assumption**: All sanctions data is **locally curated**; no auto-download or API sync.

---

## Key Patterns & Conventions

### 1. Validation Strategy: **Inline + Model-Level**
- **Models.py**: User sanitizes username (regex: `^[\w.@+-]+$`, 3-150 chars, lowercase). Password requires 12+ chars, uppercase, digit, special char.
- **Forms.py**: WTForms validators for HTTP input (Email, Length, Regexp).
- **Rationale**: Defense in depth—validates at form + model layer. Prevents SQL injection + XSS via Jinja2 auto-escape.
- **Example**: User creation → `User(username, password)` calls `sanitize_username()` + `set_password()` before insert.

### 2. Blueprint Pattern (No Circular Imports)
- Define blueprints in module-level files (`routes.py`, `clients.py`), **don't import app**.
- Register in `app.py` after app initialization.
- Access app config via `request` or `current_app` if needed inside routes.
- **Rationale**: Keeps blueprints decoupled; enables testing + reusability.

### 3. Fuzzy Matching: **Threshold 82%**
- Uses `fuzzywuzzy.fuzz.token_set_ratio()` or similar.
- Matches full name first; if no hit, tries aliases.
- **Don't hardcode thresholds** in functions—add to `config.py` as `FUZZY_THRESHOLD = 82`.

### 4. PDF Generation + Hashing
- `generate_pdf_report()` returns tuple: `(pdf_buffer, report_hash)`.
- Hash computed **after** PDF generation (SHA256 of binary PDF).
- Logged in `Log` table for audit compliance.
- **Use case**: Auditors can verify report integrity.

### 5. Error Handling: **ValueError + Flash**
- Validation errors raise `ValueError` (e.g., "Invalid username: 3-150 chars...").
- Routes catch + flash user-friendly messages (avoid leaking internals).
- Test with `self.assertIn(b'Expected message', response.data)`.

### 6. Logging: **Activity + Audit Trail**
- `log_activity(user_id, action, ip, report_hash)` records to `Log` table.
- Always log: screening runs, report generation, list updates.
- IP captured from `request.remote_addr`.

---

## Developer Workflows

### Setup
```bash
python install_dependencies.py   # Creates venv + installs deps
python init_db.py                # Creates db + admin user (admin/securepassword123)
bash run_linux.sh                # Ubuntu/Mac start (activates venv + runs app.py)
python app.py                    # Direct start (requires activated venv)
```

### Data Import (Manual + Required)
1. Download 4 XML files (UN, OFAC, UK, EU) per README links.
2. Rename & place in `/data/` folder (e.g., `un_consolidated.xml`).
3. Login → Sanctions Lists page → "Update Lists" button.
4. App parses all 4 files + populates Individual/Entity/Sanction tables.

### Testing
```bash
python -m unittest test_app.py          # Main tests (app routes, auth, validation)
python -m pytest tests/                 # Core + parser tests (if pytest installed)
```

**Test structure**:
- `test_app.py`: Auth, validation, security (e.g., no debug in prod, form limits, Jinja escaping).
- `tests/test_core.py`: Screening logic, report generation.
- `tests/test_parsers.py`: XML parsing for each sanctions source.

**Key mock patterns**: `@patch('utils.perform_screening', return_value=[...])` to avoid real data loads.

### Running
- **Linux/Mac**: `bash run_linux.sh` (auto-activates venv).
- **Windows**: `python run_windows.bat` (or manually activate venv + `python app.py`).
- **URL**: http://127.0.0.1:5000

---

## File I/O & Security Patterns

### File Upload (Clients Screening)
- **Allowed**: CSV, Excel (`.csv`, `.xlsx`).
- **Validation**: `secure_filename()` (Werkzeug) + check extension.
- **Storage**: Temp upload to `app.config['UPLOAD_FOLDER']`, deleted after processing (cleanup in `finally` block).
- **Max size**: 16MB (config `MAX_CONTENT_LENGTH`).

### XML Parsing (Sanctions Data)
- Loads from **local `/data` folder only** (no HTTP downloads).
- Parses with `xml.etree.ElementTree` (safe, no XXE by default).
- Extracts: name, DOB, nationality, aliases, addresses.
- Error handling: Logs missingfields, continues (robust to malformed entries).

### Database Paths
- Cross-platform: Use `os.path.join()`, not hardcoded `/` or `\`.
- Example: `db_path = os.path.join(os.path.dirname(__file__), 'instance', 'site.db')`.

---

## Testing & Validation Tips

### Common Test Patterns
1. **Auth**: POST `/login` with valid/invalid credentials → check redirect + session cookie.
2. **Validation**: Create User with invalid input → expect `ValueError` with message.
3. **Security**: Mock production config (`app.config['DEBUG'] = False`) → verify no debug info.
4. **File handling**: Use `secure_filename()` + test path traversal (`../../badfile`).
5. **HTML escaping**: Render template with untrusted input → verify `<script>` tags escaped.

### Mocking Best Practices
- Mock external calls (`requests.get`, file downloads) to avoid test flakiness.
- Use `unittest.mock.patch` with `return_value` for function mocking.
- Example: Mock `parse_xml()` to return fixed data.

---

## Known Quirks & Gotchas

1. **No auto-download**: Sanctions data is **manually curated**. Don't add auto-fetch without explicit approval (data integrity requirement).
2. **SQLite only**: No migration to PostgreSQL/MySQL without major refactoring (db.py is SQLite-specific).
3. **Thread-local connections**: `database.py` uses `threading.local()` for cursor management—don't bypass this.
4. **Session timeout**: 30 min inactivity → auto-logout. Warn users in UI.
5. **PDF generation**: WeasyPrint is slow on large datasets; batch reports if needed.
6. **HTTPS in production**: `SESSION_COOKIE_SECURE=False` for local dev; **must enable for production**.

---

## References

- **Data sources**: UN, OFAC, UK, EU lists (XML; renamed manually).
- **Fuzzy match library**: `fuzzywuzzy` (token_set_ratio ≥ 82%).
- **PDF**: `WeasyPrint` (HTML → PDF; slow but accurate).
- **ORM**: SQLAlchemy (models.py) + SQLite backend.
- **Web framework**: Flask 3.1.2 + WTForms for validation.
- **Task runner**: No CI/CD yet; tests run locally.

