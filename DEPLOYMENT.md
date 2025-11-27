# MkweliAML - Deployment Guide

This guide covers deploying MkweliAML for production use.

---

## 🚀 Quick Deployment (Development/Testing)

For quick testing or small-scale use:

```bash
# Linux/macOS
bash run_linux.sh

# Windows
run_windows.bat
```

This starts the Flask development server on `http://localhost:5000`.

---

## 🏭 Production Deployment

For production environments, use a proper WSGI server.

### Option 1: Gunicorn (Linux/macOS)

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Option 2: Waitress (Windows/Linux)

```bash
# Install Waitress
pip install waitress

# Run
waitress-serve --port=5000 app:app
```

### Option 3: systemd Service (Linux)

Create `/etc/systemd/system/mkweli.service`:

```ini
[Unit]
Description=MkweliAML Sanctions Screening Service
After=network.target

[Service]
User=mkweli
WorkingDirectory=/opt/mkweli
Environment="PATH=/opt/mkweli/venv/bin"
ExecStart=/opt/mkweli/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mkweli
sudo systemctl start mkweli
```

---

## 🔐 Security Configuration

### 1. Change Default Password

Immediately after deployment:
1. Login with default password `admin123`
2. Go to Settings
3. Change to a strong password (12+ characters, mixed case, numbers, symbols)

### 2. Enable HTTPS (Recommended)

Use a reverse proxy like nginx:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Set Production Secret Key

Set environment variable before starting:

```bash
export SECRET_KEY="your-very-long-random-secret-key-here"
python app.py
```

Or in systemd service file:
```ini
Environment="SECRET_KEY=your-very-long-random-secret-key-here"
```

---

## 📥 Initial Sanctions Data Setup

1. Download XML files from official sources:
   - [UN Consolidated List](https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list) → `un_consolidated.xml`
   - [UK Sanctions List](https://www.gov.uk/government/publications/the-uk-sanctions-list) → `uk_consolidated.xml`
   - [OFAC SDN List](https://sanctionslist.ofac.treas.gov/Home/SdnList) → `ofac_consolidated.xml`
   - [EU Sanctions Map](https://www.sanctionsmap.eu) → `eu_consolidated.xml`

2. Place renamed files in `data/` folder

3. Start the application - data loads automatically

4. Or click "Reload Sanctions" on Dashboard to manually trigger reload

---

## 🖥️ Air-Gapped / Offline Deployment

MkweliAML is designed for 100% offline operation after initial setup.

### Transfer to Offline System

1. On a connected machine, prepare the package:
```bash
# Clone and setup
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli

# Create venv and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download and add sanctions XML files to data/

# Package everything
cd ..
zip -r mkweli-offline.zip Mkweli/
```

2. Transfer `mkweli-offline.zip` to offline system (USB, etc.)

3. On offline system:
```bash
unzip mkweli-offline.zip
cd Mkweli
source venv/bin/activate
python app.py
```

### Updating Offline Systems

See [UPDATE.md](UPDATE.md) for procedures to update sanctions data on air-gapped systems.

---

## 📊 Database Management

### Backup

```bash
# Copy the database file
cp instance/mkweli.db instance/mkweli_backup_$(date +%Y%m%d).db
```

### Reset Database

```bash
# Remove existing database (WARNING: deletes all data)
rm instance/mkweli.db

# Restart app - fresh database created automatically
python app.py
```

---

## 🔍 Monitoring

### Log Files

Application logs are printed to stdout. For production, redirect:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app >> /var/log/mkweli/app.log 2>&1
```

### Health Check

The application exposes `/sanctions-stats` endpoint for health monitoring:

```bash
curl http://localhost:5000/sanctions-stats
```

---

## 📁 File Permissions (Linux)

```bash
# Set proper ownership
chown -R mkweli:mkweli /opt/mkweli

# Set permissions
chmod 755 /opt/mkweli
chmod 644 /opt/mkweli/*.py
chmod 600 /opt/mkweli/instance/*.db
chmod 700 /opt/mkweli/data
```

---

## 🔄 Maintenance Schedule

| Task | Frequency |
|------|-----------|
| Update sanctions lists | Every 14 days |
| Backup database | Weekly |
| Check logs for errors | Daily |
| Update Python packages | Monthly |
| Security audit | Quarterly |

---

## ❓ Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Kill the process or use different port
python app.py --port 5001
```

### Database Locked
```bash
# Usually caused by multiple instances
# Stop all instances and restart single instance
pkill -f "python app.py"
python app.py
```

### XML Parsing Errors
- Verify XML files are not corrupted
- Check file encoding is UTF-8
- Ensure files are renamed correctly

---

For update procedures, see [UPDATE.md](UPDATE.md).
