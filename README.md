# MkweliAML

**Open-source Know-Your-Customer (KYC) & Anti-Money-Laundering (AML) sanctions screening tool.**

100% offline operation • Manual sanctions data • Fuzzy name matching • Professional PDF reports

---

## 🚀 Quick Start

### One-Command Startup

**Linux/macOS:**
```bash
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli
bash run_linux.sh
```

**Windows:**
```cmd
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli
run_windows.bat
```

The startup script handles:
- ✅ Python environment setup
- ✅ Dependency installation
- ✅ Database initialization
- ✅ Application startup

**Access:** http://localhost:5000  
**Login:** Password `admin123` (change immediately after first login)

---

## 📥 Sanctions Data Setup (Required)

MkweliAML uses **manually downloaded** sanctions lists for maximum data integrity and offline operation. No automatic downloads—you control the data source.

### Download Links

| Source | Download Link | Rename To |
|--------|---------------|-----------|
| **UN** | [UN SC Consolidated List](https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list) | `un_consolidated.xml` |
| **UK** | [UK Sanctions List](https://www.gov.uk/government/publications/the-uk-sanctions-list) | `uk_consolidated.xml` |
| **OFAC** | [OFAC SDN List](https://sanctionslist.ofac.treas.gov/Home/SdnList) | `ofac_consolidated.xml` |
| **EU** | [EU Sanctions Map](https://www.sanctionsmap.eu) | `eu_consolidated.xml` |

### Installation Steps

1. Download XML files from each source above
2. Rename files exactly as shown in the table
3. Place all 4 files in the `data/` folder
4. Start the app and click **"Reload Sanctions"** on Dashboard (or restart the app)

**Important:** The system detects when XML files change and automatically reloads updated data.

---

## ✨ Features

- **Multi-List Screening:** UN, UK, OFAC, EU consolidated sanctions lists
- **Fuzzy Name Matching:** 4-layer matching (exact → token → phonetic → fuzzy) with 70% threshold
- **Abbreviation Handling:** Expands JSC, LLC, Ltd, GmbH, etc. for better company matching
- **PDF Reports:** Professional screening reports with SHA256 integrity hash
- **Audit Trail:** IP address, timestamp, and report hash logging
- **100% Offline:** Works without internet after initial setup
- **Cross-Platform:** Windows, Linux, macOS support

---

## 📁 Project Structure

```
Mkweli/
├── app.py                 # Main Flask application
├── run_linux.sh          # Linux/macOS startup script
├── run_windows.bat       # Windows startup script
├── requirements.txt      # Python dependencies
├── data/                 # Place XML sanctions files here
│   ├── un_consolidated.xml
│   ├── uk_consolidated.xml
│   ├── ofac_consolidated.xml
│   └── eu_consolidated.xml
├── instance/             # Database (auto-created)
├── templates/            # HTML templates
├── static/               # CSS, JS, images
└── app/                  # Core modules
    ├── sanctions_service.py
    └── enhanced_matcher.py
```

---

## 🔄 Updating Sanctions Lists (14-Day Cycle)

Sanctions lists should be updated every **14 days** (or as per your compliance policy).

### Update Process

1. **Download** fresh XML files from the official sources (see table above)
2. **Replace** old files in `data/` folder with new ones (keep same names)
3. **Click** "Reload Sanctions" button on Dashboard, OR restart the app

The system automatically detects file changes via MD5 hash comparison and rebuilds the cache.

**See [UPDATE.md](UPDATE.md) for detailed update procedures.**

---

## 📦 Portability & Transfer

### Creating a Portable Package

```bash
# Create a zip for transfer to another machine
zip -r mkweli-portable.zip Mkweli/ -x "*.pyc" -x "__pycache__/*" -x "venv/*" -x "instance/*" -x "*.db"
```

### On the New Machine

1. Extract the zip
2. Run `bash run_linux.sh` (Linux/Mac) or `run_windows.bat` (Windows)
3. Add your sanctions XML files to `data/` folder
4. Click "Reload Sanctions" on Dashboard

**Note:** The virtual environment (`venv/`) and database are recreated automatically on first run.

---

## 🔒 Security Notes

- **Change default password** immediately after first login
- **HTTPS recommended** for production deployment
- **Session timeout:** 30 minutes of inactivity
- **No external API calls:** All screening is local

---

## 🛠 Manual Installation

If you prefer manual setup:

```bash
# 1. Clone repository
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start application
python app.py
```

---

## 📋 System Requirements

- **Python:** 3.8 or higher
- **OS:** Windows 10+, Ubuntu 18.04+, macOS 10.14+
- **RAM:** 2GB minimum (4GB recommended for large lists)
- **Disk:** 500MB for app + sanctions data

---

## 📄 Additional Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[UPDATE.md](UPDATE.md)** - Sanctions list update procedures

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.

---

**MkweliAML** - Making AML compliance accessible for everyone.
