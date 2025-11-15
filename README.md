# MkweliAML - Open-Source Browser-Based AML/KYC Sanctions Screening Tool

MkweliAML is a lightweight, privacy-focused Anti-Money Laundering (AML) and Know Your Customer (KYC) compliance tool. Designed for NGOs, small organizations, and compliance teams in resource-limited environments, it runs locally in your browser via a simple Python server. No cloud dependencies, no internet required after setup—ensuring data privacy.

Key features:
- **Setup Wizard**: Guides through master password setup, sanctions list import, and first client addition.
- **Sanctions Management**: Import consolidated lists from XLSX (e.g., UN, UK, US/EU sources) or fetch from GitHub. Auto-parses and stores in local SQLite DB.
- **Client Management**: Add/delete clients, perform fuzzy-matched sanctions checks (using fuzzywuzzy for accurate name matching), update risk scores.
- **Reports**: Generate HTML/PDF reports with SHA-256 hashes for integrity, match details, and source documentation.
- **Dashboard**: Stats on clients, flagged cases, recent activity, and list status.
- **Security**: Master password hashing, failed login lockouts, audit logs.
- **Cross-Platform**: Runs on Ubuntu, Windows, Mac via simple scripts.

Built with assistance from Grok AI for ethical, democratized development. Licensed under Apache-2.0.

## Installation

1. **Prerequisites**:
   - Python 3.8+ (tested on 3.12).
   - Git (optional for cloning).

2. **Clone the Repo**:
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli

3. **Set Up Virtual Environment**:
- Ubuntu/Mac:
- python3 -m venv venv
source venv/bin/activate

- Windows:
python -m venv venv
venv\Scripts\activate

4. **Install Dependencies**:
pip install -r requirements.txt
- Note: For PDF reports (optional), install WeasyPrint separately (system deps may be needed: see https://weasyprint.readthedocs.io/en/stable/installation.html). If not installed, falls back to HTML reports.

5. **Initialize Database** (if not present):
python init_db.py


## Usage

1. **Run the App**:
- Ubuntu/Mac: `./run_linux.sh`
- Windows: `run_windows.bat`
- Access at http://localhost:5000 in your browser.

2. **First-Time Setup**:
- Set a strong master password (min 8 chars).
- Import sanctions lists: Upload `database.xlsx` (compiled from official UN/UK/US sources) or fetch from a GitHub URL.
- Add your first client to complete the wizard.

3. **Core Workflow**:
- **Sanctions Lists**: Manage/import in the dedicated page. Supports consolidated XLSX with sheets for sources (e.g., UN, UK, US).
- **Clients**: Add via form, check sanctions (fuzzy match against DB), view risk scores.
- **Reports**: Generate per-client with hashes for audit-proofing.
- **Settings**: Customize org name.
- **Logs**: Auto-cleared monthly; manual clear available.

4. **Updating Sanctions**:
- Monthly: Download fresh lists from official sources (UN: https://www.un.org/securitycouncil/content/un-sc-consolidated-list, UK: https://www.gov.uk/government/publications/the-uk-sanctions-list, US/OFAC: https://ofac.treasury.gov/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists).
- Compile into XLSX (sheets named "UN", "UK", "US"), re-import via the app.

## Testing Locally
To verify it's functional on your machine (before going public):
1. Delete `mkweli_aml.db` (fresh start).
2. Run `python init_db.py`.
3. Start the app (`./run_linux.sh`).
4. In browser: Set password, import `database.xlsx`, add a test client (e.g., name "Abdul Rahman"), check sanctions (should flag matches), generate report.
5. Check console/DB for errors. If issues (e.g., import fails), share output—it's likely a simple fix like path or dep.

## Contributing
Pull requests welcome! For bugs/features:
- Open an issue.
- Fork, branch, PR.

Support development via [Buy Me a Coffee](https://www.buymeacoffee.com/mkweli) for positive impact in democratized compliance tools.

## License
Apache-2.0 (see LICENSE).

## Credits
Developed by Gilbert Clement Bouic, with assistance from Grok AI by xAI for accessible, ethical tech.
