# MkweliAML - Sanctions List Update Guide

This guide covers the 14-day update cycle for sanctions lists.

---

## 🔄 Update Schedule

**Recommended:** Update sanctions lists every **14 days** to ensure compliance with changing regulations.

| Day | Task |
|-----|------|
| Day 1 | Download fresh lists from all 4 sources |
| Day 1 | Replace files in `data/` folder |
| Day 1 | Click "Reload Sanctions" or restart app |
| Day 14 | Repeat |

---

## 📥 Step-by-Step Update Process

### Step 1: Download Fresh XML Files

Download from each source:

| Source | URL | Expected Filename | Rename To |
|--------|-----|-------------------|-----------|
| **UN** | [UN SC Consolidated List](https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list) | `consolidatedLegacyByPRN.xml` | `un_consolidated.xml` |
| **UK** | [UK Sanctions List](https://www.gov.uk/government/publications/the-uk-sanctions-list) | `UK-Sanctions-List.xml` | `uk_consolidated.xml` |
| **OFAC** | [OFAC SDN List](https://sanctionslist.ofac.treas.gov/Home/SdnList) | `sdn.xml` | `ofac_consolidated.xml` |
| **EU** | [EU Sanctions Map](https://www.sanctionsmap.eu) | `yyyymmdd-FULL(xsd).xml` | `eu_consolidated.xml` |

**EU List Note:** Navigate to "Consolidated lists of financial sanctions" → "Consolidated Financial Sanctions File 1.0" → Download.

### Step 2: Replace Files in data/ Folder

```bash
# Navigate to your MkweliAML installation
cd /path/to/Mkweli

# Backup old files (optional but recommended)
mkdir -p data/backup
cp data/*.xml data/backup/

# Replace with new files
cp ~/Downloads/un_consolidated.xml data/
cp ~/Downloads/uk_consolidated.xml data/
cp ~/Downloads/ofac_consolidated.xml data/
cp ~/Downloads/eu_consolidated.xml data/
```

### Step 3: Reload Sanctions Data

**Option A: Via Dashboard (Recommended)**
1. Open http://localhost:5000 in browser
2. Login
3. Click the **"Reload Sanctions"** button on Dashboard
4. Wait for confirmation message

**Option B: Restart Application**
```bash
# Stop the running app (Ctrl+C if running in terminal)
# Then restart
bash run_linux.sh  # Linux/Mac
run_windows.bat    # Windows
```

The system automatically detects file changes and rebuilds the cache.

### Step 4: Verify Update

Check the Dashboard shows:
- Updated entity count
- New "Loaded" date

Test a screening to verify new data is active.

---

## ⚠️ Important: File Naming

Files **must** be named exactly:
- `un_consolidated.xml`
- `uk_consolidated.xml`
- `ofac_consolidated.xml`
- `eu_consolidated.xml`

The system identifies source by filename. Wrong names = wrong parsing = missing entities.

---

## 🔒 Updating Air-Gapped (Offline) Systems

For systems without internet access:

### On Connected Machine

1. Download all 4 XML files
2. Rename as required
3. Transfer to USB drive:
```bash
mkdir usb_update
cp un_consolidated.xml usb_update/
cp uk_consolidated.xml usb_update/
cp ofac_consolidated.xml usb_update/
cp eu_consolidated.xml usb_update/
```

### On Offline Machine

1. Mount USB drive
2. Copy files to data folder:
```bash
cp /media/usb/*.xml /path/to/Mkweli/data/
```
3. Restart application or click "Reload Sanctions"

---

## 🧹 Cache Management

MkweliAML caches parsed sanctions data for faster startup.

### Cache Location
```
instance/sanctions_cache.pkl
```

### Force Cache Rebuild
```bash
# Delete cache file
rm instance/sanctions_cache.pkl

# Restart app - cache rebuilds automatically
python app.py
```

### When to Force Rebuild
- After manual database changes
- If entity count seems incorrect
- After major version update

---

## 📊 Verification Checklist

After each update, verify:

- [ ] Dashboard shows updated "Loaded" date
- [ ] Entity count matches expected (typically 15,000-30,000 total)
- [ ] Test search returns results
- [ ] No errors in startup output

---

## 🔍 Troubleshooting Updates

### Files Not Loading

**Symptom:** Entity count stays at 0 or doesn't change

**Solutions:**
1. Verify files are in `data/` folder (not subfolder)
2. Check file names are exact (case-sensitive on Linux)
3. Click "Reload Sanctions" button
4. Check for XML parsing errors in console output

### Partial Data Loading

**Symptom:** Entity count lower than expected

**Solutions:**
1. Some XML files may be corrupted - re-download
2. Check each file parses individually:
```bash
# Test parsing
python -c "from app.sanctions_service import SanctionsService; s = SanctionsService(); print(len(s.sanctions_entities))"
```

### Duplicate Entries After Update

**Not an issue:** The system replaces (not appends) data when reloading.

If you suspect duplicates:
1. Delete cache: `rm instance/sanctions_cache.pkl`
2. Restart app

---

## 📅 Setting Up Update Reminders

### Linux (cron)
Add to crontab (`crontab -e`):
```bash
# Reminder every 14 days at 9 AM
0 9 1,15 * * echo "MkweliAML: Time to update sanctions lists!" | mail -s "Sanctions Update Reminder" admin@example.com
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task → "Sanctions Update Reminder"
3. Trigger: Weekly, every 2 weeks
4. Action: Display a message or send email

### Calendar Reminder
- Set recurring calendar event for every 14 days
- Include download links in event description

---

## 📝 Update Log Template

Keep a log of updates for compliance records:

```
Date: YYYY-MM-DD
Updated by: [Name]
Files updated:
- [ ] un_consolidated.xml (size: XX MB)
- [ ] uk_consolidated.xml (size: XX MB)  
- [ ] ofac_consolidated.xml (size: XX MB)
- [ ] eu_consolidated.xml (size: XX MB)
Previous entity count: XXXXX
New entity count: XXXXX
Verification test: PASS/FAIL
Notes: [Any issues encountered]
```

---

## 🔗 Quick Reference Links

| Source | Direct Download Page |
|--------|---------------------|
| UN | https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list |
| UK | https://www.gov.uk/government/publications/the-uk-sanctions-list |
| OFAC | https://sanctionslist.ofac.treas.gov/Home/SdnList |
| EU | https://www.sanctionsmap.eu |

---

**Remember:** Regular updates ensure your screening catches newly sanctioned entities. Set a reminder!
