# Mkweli AML - Sanctions Screening Tool

A simple tool to screen names against international sanctions lists (UN, UK, OFAC, EU).

**Works out of the box** - all sanctions data is pre-loaded and ready to use.

---

## What is Mkweli AML?

Mkweli AML helps you check if a person or company appears on international sanctions lists. This is required for Know-Your-Customer (KYC) and Anti-Money-Laundering (AML) compliance.

**Features:**
- ✅ Pre-loaded sanctions data (UN, UK, OFAC, EU)
- ✅ Works offline after installation
- ✅ Professional PDF reports
- ✅ Simple web interface

---

## Quick Start (5 Minutes)

### What You Need

- A computer with **Windows 10/11** or **Ubuntu 20.04+**
- **Docker Desktop** installed (free download below)
- **8 GB RAM** (minimum)
- **5 GB disk space**

---

## Step 1: Install Docker

### Windows

1. Go to https://www.docker.com/products/docker-desktop/
2. Click **"Download for Windows"**
3. Run the installer and follow the prompts
4. **Restart your computer** when asked
5. Open Docker Desktop and wait for it to start (green icon in taskbar)

### Ubuntu

Open a terminal and run these commands:

```bash
# Update system
sudo apt update

# Install Docker
sudo apt install docker.io docker-compose -y

# Allow your user to run Docker
sudo usermod -aG docker $USER

# Log out and log back in for changes to take effect
```

---

## Step 2: Download Mkweli

### Windows (PowerShell)

1. Press `Windows + X` and click **"Windows PowerShell"**
2. Run these commands:

```powershell
# Download Mkweli
git clone https://github.com/gilbertbouic/Mkweli.git

# Go to the folder
cd Mkweli

# Create settings file
copy .env.example .env
```

### Ubuntu (Terminal)

Open a terminal and run:

```bash
# Download Mkweli
git clone https://github.com/gilbertbouic/Mkweli.git

# Go to the folder
cd Mkweli

# Create settings file
cp .env.example .env
```

---

## Step 3: Start the Application

Run this command (same for Windows and Ubuntu):

```bash
docker-compose up -d
```

**Wait 1-2 minutes** for the first startup. The application is loading sanctions data.

---

## Step 4: Open the Application

1. Open your web browser
2. Go to: **http://localhost:8000**
3. Enter password: `admin123`
4. **Important:** Change the password immediately (see First-Time Setup)

---

## First-Time Setup

### Change Your Password

1. Log in with password `admin123`
2. Click the **gear icon** (⚙️) in the top menu
3. Click **"Change Password"**
4. Enter your current password (`admin123`)
5. Enter a new strong password (at least 12 characters)
6. Click **"Change Password"**

### Generate a Secret Key (Recommended)

For better security, generate a unique secret key:

**Windows (PowerShell):**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

**Ubuntu:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it in your `.env` file, replacing `your-secure-secret-key-here-change-me`.

Then restart the application:
```bash
docker-compose restart
```

---

## Using Mkweli

### Screen a Single Name

1. Go to **Dashboard**
2. Click **"Quick Check"**
3. Enter a name to screen
4. Click **"Check"**

### Screen Multiple Names (Batch)

1. Go to **Dashboard**
2. Click **"Upload List"**
3. Upload a CSV or Excel file with names
4. Download the screening report

---

## Updating Sanctions Data

The application shows an alert when sanctions data is older than 14 days.

### How to Update

1. Download new XML files from official sources (verify these are the current official URLs):
   - **UN:** https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list
   - **UK:** https://www.gov.uk/government/publications/the-uk-sanctions-list
   - **OFAC:** https://sanctionslist.ofac.treas.gov/Home/SdnList
   - **EU:** https://www.sanctionsmap.eu

2. Rename the files to match these exact names:
   - `un_consolidated.xml`
   - `uk_consolidated.xml`
   - `ofac_consolidated.xml`
   - `eu_consolidated.xml`

3. Replace the files in the `data/` folder

4. Restart the application:
   ```bash
   docker-compose restart
   ```

---

## Common Commands

### Start the Application
```bash
docker-compose up -d
```

### Stop the Application
```bash
docker-compose down
```

### Restart the Application
```bash
docker-compose restart
```

### Check if Application is Running
```bash
docker-compose ps
```

### View Logs (if something goes wrong)
```bash
docker-compose logs
```

---

## Troubleshooting

### "Cannot connect to localhost:8000"

**Solution:** Wait 1-2 minutes. The application takes time to load on first start.

Check status with:
```bash
docker-compose ps
```

Wait until STATUS shows `healthy`.

---

### "Port 8000 is already in use"

**Solution:** Change the port number.

1. Open the `.env` file in a text editor
2. Change `PORT=8000` to `PORT=8080`
3. Restart: `docker-compose up -d`
4. Access at: http://localhost:8080

---

### "Docker is not running"

**Windows:** Open Docker Desktop from the Start menu and wait for it to start.

**Ubuntu:** Run `sudo systemctl start docker`

---

### "Permission denied" (Ubuntu)

Run:
```bash
sudo usermod -aG docker $USER
```
Then log out and log back in.

---

### "Out of memory"

The application needs at least 2 GB of RAM. If you have memory issues:

1. Close other applications
2. Restart Docker Desktop (Windows) or the Docker service (Ubuntu)

---

### Application is Slow on First Run

This is normal. The first startup loads ~160 MB of sanctions data and takes 1-2 minutes. Subsequent starts are much faster.

---

## File Structure

```
Mkweli/
├── data/                    # Sanctions data (XML files)
│   ├── eu_consolidated.xml
│   ├── ofac_consolidated.xml
│   ├── uk_consolidated.xml
│   └── un_consolidated.xml
├── .env                     # Your settings (create from .env.example)
├── .env.example             # Settings template
├── docker-compose.yml       # Docker configuration
└── README.md                # This file
```

**Note:** The `data/` folder is the only folder you need to edit (to update sanctions data).

---

## Support

- **Email:** gilbert@Mkweli.tech
- **Issues:** https://github.com/gilbertbouic/Mkweli/issues

When reporting issues, please include:
1. Your operating system (Windows or Ubuntu)
2. The output of `docker-compose logs`
3. What you were trying to do when the error occurred

---

## License

See [LICENSE](LICENSE) file for details. 
