MkweliAML - Local Anti-Money Laundering Compliance Tool

MkweliAML is a simple, offline tool for KYC client screening against sanctions lists. It runs on your local machine with no internet required after setup. Designed for small teams in budget-constrained environments.

Key Features
- Add and manage clients (KYC data)
- Import sanctions lists (manual CSV downloads from official sources)
- Screen clients for matches
- Generate PDF/HTML reports
- Audit logging
- Secure master password authentication

System Requirements
- Python 3.8 or later (download from https://www.python.org/downloads/)
- For PDF reports (optional but recommended): Install system libraries for WeasyPrint (see below)

Setup Instructions
1. Unzip the Package: Extract the ZIP file to a folder (e.g., C:\MkweliAML on Windows or ~/MkweliAML on Linux/Mac).

2. Install System Dependencies for PDF Reports (skip if OK with HTML reports):
   - Windows:
     - Download and install GTK3 Runtime: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases (select the latest .exe, install with defaults).
     - Add GTK bin to PATH: Right-click This PC > Properties > Advanced system settings > Environment Variables > Edit "Path" > Add "C:\Program Files\GTK3-Runtime Win64\bin" (adjust if installed elsewhere).
   - Linux (Ubuntu/Debian):
     sudo apt update
     sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2 python3-dev
   - Linux (Fedora/RPM):
     sudo dnf install pango gdk-pixbuf2 libffi-devel cairo python3-devel
   - Mac:
     - Install Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     - Then: brew install pango cairo gdk-pixbuf libffi python
     - For M1/ARM: If issues, use arch -x86_64 brew install ... or check WeasyPrint docs.

3. Install Python Dependencies:
   - Open a terminal/command prompt in the unzipped folder.
   - Run: python install_dependencies.py (or python3 install_dependencies.py on Linux/Mac).
   - This creates a virtual environment (venv) and installs packages.

4. Run the App:
   - Windows: Double-click run_windows.bat.
   - Linux/Mac: Run ./run_linux.sh in terminal (make executable: chmod +x run_linux.sh).
   - Open browser: http://localhost:5000
   - Set master password on first launch (min 8 chars).

Usage
- Download Sanctions Lists: Manually get CSVs from:
  - OFAC (USA): https://ofac.treasury.gov/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists
  - UN: https://www.un.org/securitycouncil/content/un-sc-consolidated-list (XML - use convert_sanctions.py)
  - EU: https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions (XML/Excel - convert)
- Convert Non-CSV: Run python convert_sanctions.py input.xml output.csv (see script for help).
- Import Lists: Go to Sanctions Lists page, select name (e.g., "OFAC"), upload CSV.
- Add Clients: Clients page > Add form.
- Screen/Report: Clients page > Check Sanctions (modal), then Generate Report from modal or Reports page.
- Help: See Help page in app.

Troubleshooting
- PDF Not Working: Ensure system deps installed; restart app. Fallback to HTML.
- Port 5000 Busy: Change in app.py (port=5000 to another).
- Errors: Check terminal output. Re-run install_dependencies.py.
- Security Note: Use strong password; run locally only (no remote access without HTTPS).
- No Updates: Manually check for new ZIP versions if available.

For issues, consult script comments or Python docs. No support provided.

License: Proprietary - For internal use only.
Open to acquisitions for global impact!
