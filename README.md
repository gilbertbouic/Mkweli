# MkweliAML - Free AML Screening Tool

Open-source Know-Your-Customer (KYC) Anti-Money-Laundering (AML) tool 
 **embedded sanctions data** that works immediately after installation.

**Key Features:**
- ✅ **Pre-loaded sanctions data** (UN, UK, OFAC, EU) - works out of the box
- ✅ **Free OS platform** (Ubuntu)
- ✅ **Automatic 14-day update reminders** for sanctions data
- ✅ **Offline-capable** - no internet required for screening
- ✅ **Fuzzy name matching** (70% threshold) + risk tier scoring
- ✅ **Professional reports** with SHA256 integrity verification
- ✅ **Detailed audit logs** with IP, timestamp, actions


🚀 Getting Started with Mkweli
Follow these steps to install and run Mkweli on your system.

Step 1: Download and Extract
Download the Mkweli.zip file.

Extract it to:

Windows: C:\Mkweli

Ubuntu: /home/usr/Mkweli

Step 2: Windows-Specific Setup
(Skip if you're using Ubuntu)

Open PowerShell as Administrator and run:

powershell
wsl --install
Install the latest version of Ubuntu from the Microsoft Store.

Once Ubuntu is installed, open it to set up your WSL environment.

Step 3: Open Terminal in the Mkweli Folder
Navigate to the extracted Mkweli folder in File Explorer.

Right-click inside the folder and select “Open in Terminal” (Windows) or open a terminal in that location (Ubuntu).

(Windows WSL users): In the terminal, type wsl to switch to the Ubuntu environment.

Step 4: Install Dependencies
Run the following commands in your terminal:

sudo apt update && sudo apt upgrade -y

sudo apt install -y build-essential git curl wget

sudo apt install -y python3 python3-pip python3-venv python3-dev

Step 5: Set Up Python Virtual Environment

pip3 install -r requirements.txt --break-system-packages

python3 -m venv venv

source venv/bin/activate

Step 6: Run the Application

python3 app.py

Once running, you’ll see a confirmation that the app has started.

Step 7: Access Mkweli in Your Browser
Open your web browser and go to:
http://127.0.0.1:5000

Default login:
Password: admin123

Step 8: Initial Setup
Click on “Setup” in the app.

Add your details.

Change your password immediately for security.

You’re ready to start screening!

Keep your terminal open while using the app.

Ctrl+C to close


Enjoy using Mkweli! 🎉

-**Troubleshooting**
Ignore Terminal warning : "WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead."

Every 14 days renew sanctions data. 
