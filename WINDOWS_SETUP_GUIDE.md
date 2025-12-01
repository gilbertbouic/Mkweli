# Mkweli AML - Windows Setup Guide

Welcome to Mkweli AML! This guide will help you install and run the application on Windows in just a few minutes.

---

## 📋 What You Need

Before you start, make sure you have:

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| **Windows Version** | Windows 10 (64-bit) | Windows 11 |
| **RAM** | 4 GB | 8 GB or more |
| **Disk Space** | 5 GB free | 10 GB free |
| **Internet** | Required for setup | Not needed after setup |

---

## 🚀 Quick Install (Recommended)

### Step 1: Download the Installer

1. Go to [Mkweli Releases](https://github.com/gilbertbouic/Mkweli/releases)
2. Download **`MkweliAML-Setup-x.x.x.exe`** (the latest version)
3. Save it to your Downloads folder

### Step 2: Run the Installer

1. **Double-click** the downloaded file
2. If Windows asks "Do you want to allow this app to make changes?", click **Yes**
3. Follow the on-screen instructions:
   - Click **Next** to continue
   - Read and accept the license agreement
   - Choose where to install (default is fine)
   - Click **Install**

### Step 3: Docker Desktop

The installer will check if Docker Desktop is installed:

**If Docker is NOT installed:**
1. The installer will show a message
2. Click **Download Docker Desktop**
3. Install Docker Desktop (follow its prompts)
4. **Restart your computer**
5. Run the Mkweli installer again

**If Docker IS installed:**
- The installer will continue automatically

### Step 4: Launch the Application

After installation:
1. A **Mkweli AML** shortcut appears on your desktop
2. **Double-click** the shortcut
3. A menu appears - select **"Start Application"**
4. Wait about 30 seconds (longer on first run)
5. Your browser opens automatically to the dashboard

### Step 5: First Login

1. Enter the default password: **`admin123`**
2. **IMPORTANT:** Change your password immediately:
   - Click the ⚙️ (gear) icon
   - Select **Change Password**
   - Create a strong new password (12+ characters)

🎉 **Congratulations! You're ready to use Mkweli AML!**

---

## 🖥️ Using the Launcher

The desktop shortcut opens a simple menu:

| Option | What It Does |
|--------|--------------|
| **1. Start Application** | Starts Mkweli (opens browser automatically) |
| **2. Stop Application** | Stops Mkweli |
| **3. Restart Application** | Restarts Mkweli |
| **4. Open Dashboard** | Opens the web interface in your browser |
| **5. View Logs** | Shows recent activity (for troubleshooting) |
| **6. Check Status** | Shows if everything is running correctly |

---

## 🔧 Manual Installation (Alternative)

If you prefer not to use the installer, you can set up manually:

### 1. Install Docker Desktop

1. Visit [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. Download Docker Desktop for Windows
3. Run the installer
4. **Restart your computer**
5. Open Docker Desktop and wait for it to start (green icon in taskbar)

### 2. Download Mkweli

1. Visit [github.com/gilbertbouic/Mkweli](https://github.com/gilbertbouic/Mkweli)
2. Click the green **Code** button
3. Click **Download ZIP**
4. Extract the ZIP to a folder (e.g., `C:\Mkweli`)

### 3. Start the Application

1. Open the folder where you extracted Mkweli
2. Double-click **`MkweliLauncher.vbs`**
3. Select **"Start Application"** from the menu
4. Wait for the browser to open

---

## ❓ Troubleshooting

### "Docker Desktop is not running"

**Solution:**
1. Look for Docker Desktop in your Start Menu
2. Click to open it
3. Wait for the whale icon in your taskbar to stop animating
4. Try starting Mkweli again

### "The application won't start"

**Solution:**
1. Make sure Docker Desktop is running (check taskbar)
2. Wait 2-3 minutes (first start takes longer)
3. Try selecting **"Restart Application"** from the launcher

### "I can't access localhost:8000"

**Solution:**
1. Make sure the application is running (check with launcher)
2. Try typing `http://127.0.0.1:8000` instead
3. Check if another program is using port 8000

### "Docker installation failed"

**Solutions:**
- Make sure you have Windows 10/11 64-bit
- Enable virtualization in your BIOS (search online for your computer model)
- Make sure Windows is up to date
- Try restarting your computer and installing again

### "My computer is slow when running Mkweli"

**Solutions:**
- Close other applications
- Make sure you have at least 8 GB RAM
- Reduce the number of Docker containers running

---

## 📁 File Locations

After installation, you'll find:

| Location | What's There |
|----------|--------------|
| `C:\Program Files\Mkweli AML\` | Application files |
| `C:\Program Files\Mkweli AML\data\` | Sanctions data (XML files) |
| `Desktop\Mkweli AML` | Shortcut to launcher |
| Start Menu | Mkweli AML shortcuts |

---

## 🔄 Updating Sanctions Data

The application will remind you when sanctions data is older than 14 days.

### How to Update

1. Download new XML files from official sources:
   - [UN Sanctions List](https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list)
   - [UK Sanctions List](https://www.gov.uk/government/publications/the-uk-sanctions-list)
   - [OFAC Sanctions List](https://sanctionslist.ofac.treas.gov/Home/SdnList)
   - [EU Sanctions List](https://www.sanctionsmap.eu)

2. Rename files to match:
   - `un_consolidated.xml`
   - `uk_consolidated.xml`
   - `ofac_consolidated.xml`
   - `eu_consolidated.xml`

3. Replace files in: `C:\Program Files\Mkweli AML\data\`

4. Restart the application using the launcher

---

## 🛟 Getting Help

- **Email:** gilbert@mkweli.tech
- **GitHub Issues:** [github.com/gilbertbouic/Mkweli/issues](https://github.com/gilbertbouic/Mkweli/issues)

When asking for help, please include:
- Your Windows version
- The error message (if any)
- What you were trying to do

---

## 🔐 Security Tips

1. **Change the default password immediately**
2. **Don't share your password** with others
3. **Keep Docker Desktop updated** for security patches
4. **Update sanctions data regularly** (at least monthly)

---

*Mkweli AML - Free and Open Source Sanctions Screening*
