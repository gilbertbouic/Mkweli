 MkweliAML

Open-source,Know-Your-Customer(KYC) & Anti-Money-Laundering (AML) financial sanctions screening tool.
Manually downloaded sanctions lists · Fuzzy name matching.
Professional PDF reports for donors and Auditors 

https://github.com/gilbertbouic/Mkweli

## Features

- Manual loading of UN, UK, OFAC, EU sanctions lists (XML)
- Fuzzy name + DOB + nationality matching (threshold 82%)
- Professional PDF screening reports with your organisation details in header
- SHA256 hash on every generated report (integrity)
- Detailed per-session activity log with IP, timestamp, action and report SHA256
- Cross-platform: Ubuntu/Linux, Windows, macOS
- Docker support for one-command deployment

## Quick Start

git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli
python -m venv venv

# Ubuntu / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

python install_dependencies.py   # creates venv & installs everything
python init_db.py               # creates database + admin user
python app.py                   # starts the app.

Open browser → http://127.0.0.1:5000
First login: admin / securepassword123 (change immediately in Settings)
Manual Sanctions Lists Download (REQUIRED)
The tool now can be used 100% offline.

Download Links: 
 UN Consolidated List,https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list
Downloads as : consolidatedLegacyByPRN.xml. Rename - “un_consolidated.xml”

 UK Consolidated List: https://www.gov.uk/government/publications/the-uk-sanctions-list
Downloads as: UK-Sanctions-List.xml. Rename - “uk_consolidated.xml”

 OFACConsolidatedList,https://sanctionslist.ofac.treas.gov/Home/SdnList 
Downloads as sdn.xml. Rename - “ofac_consolidated.xml”

 EU Consolidated List: https://www.sanctionsmap.eu
Consolidated lists of financial sanctions → Consolidated Financial Sanctions File 1.0 → Access- download URL.
Downloads as yyyymmdd-FULL(xsd).xml. Rename - “eu_consolidated.xml”

Place all 4 files in the MkweliAML/data folder.

Start the app (python app.py or your run script).
Login.
Go to Sanctions Lists page.
Click Update Lists button.
The app will parse all 4 files from the /data folder and load into database.
Screen clients
Create Reports and Logs with SHA256 validation
