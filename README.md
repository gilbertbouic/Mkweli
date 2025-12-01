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

## Choose Your Installation Method

| I am a... | Recommended Method |
|-----------|-------------------|
| **Windows User** (non-technical) | [One-Click Installer](#-windows-users-one-click-install) |
| **Developer / Power User** | [Docker Setup](#-developers-docker-setup) |
| **Ubuntu/Linux User** | [Docker Setup](#-developers-docker-setup) |

---

## 🖥️ Windows Users: One-Click Install

**No terminal required!** Get up and running in 3 easy steps.

### System Requirements

| Requirement | Minimum |
|------------|---------|
| Windows | 10 or 11 (64-bit) |
| RAM | 4 GB |
| Disk Space | 5 GB free |

### Step 1: Download the Installer

👉 **[Download Mkweli AML Installer](https://github.com/gilbertbouic/Mkweli/releases)** (MkweliAML-Setup-x.x.x.exe)

### Step 2: Run the Installer

1. **Double-click** the downloaded file
2. Click **Yes** if Windows asks for permission
3. Follow the wizard: **Next → Accept → Install**
4. If Docker is not installed, the installer will guide you to download it

### Step 3: Launch & Use

1. **Double-click** the **Mkweli AML** shortcut on your desktop
2. Select **"1. Start Application"** from the menu
3. Your browser opens automatically - login with password: `admin123`
4. **Change your password immediately** (⚙️ → Change Password)

**That's it! You're ready to screen names.** 🎉

> 📖 For detailed instructions, see [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md)

---

## 👨‍💻 Developers: Docker Setup

For developers, power users, and Linux/Ubuntu users.

### What You Need

- **Windows 10/11** or **Ubuntu 20.04+**
- **Docker Desktop** installed ([download here](https://www.docker.com/products/docker-desktop/))
- **8 GB RAM** (minimum)
- **5 GB disk space**

### Install Docker

**Windows:**
1. Download [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Run the installer and restart when prompted
3. Open Docker Desktop and wait for it to start

**Ubuntu:**
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
# Log out and back in
```

### Download & Run Mkweli

```bash
# Clone the repository
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli

# Create configuration file
cp .env.example .env  # Linux/Mac
# OR
copy .env.example .env  # Windows

# Start the application
docker-compose up -d
```

**Wait 1-2 minutes** for the first startup, then open: **http://localhost:8000**

Default password: `admin123` (change immediately!)

---

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
