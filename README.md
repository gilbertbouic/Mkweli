# MkweliAML - Portable AML Screening Tool

Open-source Know-Your-Customer (KYC) & Anti-Money-Laundering (AML) financial sanctions screening tool with **embedded sanctions data** that works immediately after installation.

**Key Features:**
- ✅ **Pre-loaded sanctions data** (UN, UK, OFAC, EU) - works out of the box
- ✅ **Cross-platform** (Ubuntu, Windows, macOS)
- ✅ **Automatic 14-day update reminders** for sanctions data
- ✅ **Offline-capable** - no internet required for screening
- ✅ **Fuzzy name matching** (82% threshold) + DOB + nationality
- ✅ **Professional PDF reports** with SHA256 integrity verification
- ✅ **Detailed audit logs** with IP, timestamp, actions

---

## **Quick Start (Linux/Ubuntu)**

```bash
# 1. Clone repository
git clone https://github.com/gilbertbouic/Mkweli. git
cd Mkweli

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python3 init_db.py

# 5. Start application
python3 app.py
```

**Then open:** http://127.0.0. 1:5000  
**Default login:** `admin` / `securepassword123` (change in Settings immediately)

---

## **Quick Start (Windows)**

```bash
# 1. Clone repository
# MkweliAML - Portable AML Screening Tool

Open-source Know-Your-Customer (KYC) & Anti-Money-Laundering (AML) financial sanctions screening tool with **embedded sanctions data** that works immediately after installation.

**Key Features:**
- ✅ **Pre-loaded sanctions data** (UN, UK, OFAC, EU) - works out of the box
- ✅ **Cross-platform** (Ubuntu, Windows, macOS)
- ✅ **Automatic 14-day update reminders** for sanctions data
- ✅ **Offline-capable** - no internet required for screening
- ✅ **Fuzzy name matching** (82% threshold) + DOB + nationality
- ✅ **Professional PDF reports** with SHA256 integrity verification
- ✅ **Detailed audit logs** with IP, timestamp, actions

---

## **Quick Start (Linux/Ubuntu)**

```bash
# 1. Clone repository
git clone https://github.com/gilbertbouic/Mkweli. git
cd Mkweli

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python3 init_db.py

# 5. Start application
python3 app.py
```

**Then open:** http://127.0.0. 1:5000  
**Default login:** `admin` / `securepassword123` (change in Settings immediately)

---

## **Quick Start (Windows)**

```bash
# 1. Clone repository
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4.  Initialize database
python init_db. py

# 5. Start application
python app.py
```

**Then open:** http://127. 0.0.1:5000

---

## **What's Included**

The repository comes with **160MB of pre-configured sanctions data**:
- `data/un_consolidated.xml` (19MB) - UN Security Council list
- `data/eu_consolidated.xml` (23MB) - EU consolidated sanctions
- `data/uk_consolidated. xml` (19MB) - UK consolidated sanctions
- `data/ofac_consolidated.xml` (100MB) - US OFAC SDN list

**No manual downloads required! ** The app will automatically parse these on first run. 

---

## **Updating Sanctions Data (Every 14 Days)**

The app shows an alert on the Dashboard when data is older than 14 days. 

### Manual Update

1 Download latest xml files from official sources,to your downloads folder. (links below)
2. Rename the files to match those in /data folder. Delete and replace files in /data folder with the same names.
4. Go to **Dashboard** page in the app → Click **"Reload Lists"**
5. App automatically re-parses new files

### Paid service (contact repo owner): Use Git Pull Updates
We update the sanctions files in the repo every 14 days:
```bash
git pull origin main
# Sanctions files update automatically in data/ folder
```

---

## **Official Sanctions List Sources**

Update every 14 days using these links:

| Source | URL | File Name | Rename To |
|--------|-----|-----------|-----------|
| **UN** | https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list |           Change name: `un_consolidated.xml` |
| **UK** | https://www.gov.uk/government/publications/the-uk-sanctions-list |               Change name: `uk_consolidated.xml` |
| **OFAC** | https://sanctionslist. ofac.treas.gov/Home/SdnList Change name :`ofac_consolidated.xml` |
| **EU** | https://www.sanctionsmap.eu |  Change name: `eu_consolidated.xml` |

---

## **Database Initialization**

The `init_db.py` script:
- Creates SQLite database with optimized schema
- Creates default admin user
- **Automatically loads all sanctions data from `/data` folder**
- Builds search indexes for fast name matching

No additional steps needed!

---

## **Architecture**

```
Mkweli/
├── data/                          # Sanctions data (160MB)
│   ├── eu_consolidated.xml        # ✅ Pre-loaded
│   ├── ofac_consolidated.xml      # ✅ Pre-loaded
│   ├── uk_consolidated.xml        # ✅ Pre-loaded
│   └── un_consolidated.xml        # ✅ Pre-loaded
├── app.py                         # Main Flask application
├── app/                           # Application modules
│   ├── sanctions_service.py       # Automatic data loading
│   ├── xml_sanctions_parser.py    # Multi-format parser
│   └── ... 
├── templates/                     # HTML templates
├── static/                        # CSS/JS
├── mkweli_aml.db                 # SQLite database (auto-created)
├── requirements.txt               # Python dependencies
├── init_db.py                     # Database setup script
└── README.md                      # This file
```

---

## **Troubleshooting**

### **Port Already in Use**
```bash
# Run on different port
python3 app.py --port 5001
```

### **Database Locked**
```bash
# Delete and reinitialize
rm mkweli_aml.db
python3 init_db.py
```

### **Sanctions Data Not Loading**
```bash
# Check if data files exist
ls -lh data/

# If missing, ensure all 4 XML files are in data/ folder
# Then restart app
```

### **Slow Screening on First Run**
First time parsing 160MB of data takes ~30-60 seconds. Subsequent searches are instant (cached).

---

## **Security Notes**

- Change default admin password immediately
- Database contains no personal data (only sanctions matches)
- All reports are SHA256-hashed for audit trail
- Tool is 100% offline-capable (no cloud dependency)

---

## **Support & Updates**

- Repository: https://github.com/gilbertbouic/Mkweli
- Issues: https://github.com/gilbertbouic/Mkweli/issues

---

## **License**

See LICENSE file for details. 
