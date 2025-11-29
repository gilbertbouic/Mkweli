# MkweliAML - Portable AML Screening Tool

Open-source Know-Your-Customer (KYC) & Anti-Money-Laundering (AML) financial sanctions screening tool with **embedded sanctions data** that works immediately after installation.

**Key Features:**
- ✅ **Pre-loaded sanctions data** (UN, UK, OFAC, EU) - works out of the box
- ✅ **Cross-platform** (Ubuntu, Windows, macOS)
- ✅ **Docker support** for easy production deployment
- ✅ **Automatic 14-day update reminders** for sanctions data
- ✅ **Offline-capable** - no internet required for screening
- ✅ **Fuzzy name matching** (70% threshold) + risk tier scoring
- ✅ **Professional reports** with SHA256 integrity verification
- ✅ **Detailed audit logs** with IP, timestamp, actions
- ✅ **Health monitoring** endpoint for production systems

---

## 📋 Table of Contents

- [Quick Start with Docker (5 minutes)](#-quick-start-with-docker-5-minutes)
- [Detailed Setup - Linux/Ubuntu](#-detailed-setup---linuxubuntu)
- [Detailed Setup - Windows](#-detailed-setup---windows)
- [Docker Commands Reference](#-docker-commands-reference)
- [Database Initialization & Admin Password](#-database-initialization--admin-password)
- [Updating Sanctions Data](#-updating-sanctions-data)
- [Health Monitoring](#-health-monitoring)
- [Troubleshooting](#-troubleshooting)
- [File Structure & Architecture](#-file-structure--architecture)
- [Security Best Practices](#-security-best-practices)
- [Support & Updates](#-support--updates)

---

## 🐳 Quick Start with Docker (5 minutes)

The fastest way to run Mkweli AML is using Docker. This works on both Windows and Linux.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac)
- [Docker Engine](https://docs.docker.com/engine/install/) (Linux)

### Step 1: Clone and Configure

```bash
# Clone repository
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli

# Create environment file from template
cp .env.example .env
```

### Step 2: Generate Secret Key

**Linux/Mac:**
```bash
# Generate secure secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and replace 'your-secure-secret-key-here-change-me' in .env
```

**Windows (PowerShell):**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and edit .env file
```

### Step 3: Start Application

```bash
# Build and start container
docker-compose up -d

# Wait for container to be healthy (30-60 seconds for first run)
docker-compose ps
```

### Step 4: Access Application

- **URL:** http://localhost:8000
- **Default Password:** `admin123`
- **⚠️ Change the password immediately** in Setup → Change Password

### Expected Output

```
$ docker-compose up -d
Creating network "mkweli_default" with the default driver
Creating volume "mkweli_mkweli-db" with local driver
Creating mkweli-aml ... done

$ docker-compose ps
NAME          STATUS    PORTS
mkweli-aml    healthy   0.0.0.0:8000->8000/tcp
```

---

## 🐧 Detailed Setup - Linux/Ubuntu

### Option A: Using Docker (Recommended)

See [Quick Start with Docker](#-quick-start-with-docker-5-minutes) above.

### Option B: Production Script (Without Docker)

```bash
# 1. Clone repository
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli

# 2. Make script executable and run
chmod +x run_production_linux.sh
./run_production_linux.sh
```

The script will:
- Create virtual environment automatically
- Install all dependencies
- Generate secure SECRET_KEY
- Start Gunicorn production server on port 8000

**Access:** http://localhost:8000

### Option C: Manual Development Setup

```bash
# 1. Clone repository
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start development server
python3 app.py
```

**Access:** http://localhost:5000

---

## 🪟 Detailed Setup - Windows

### Option A: Using Docker Desktop (Recommended)

1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Open PowerShell or Command Prompt
3. Follow [Quick Start with Docker](#-quick-start-with-docker-5-minutes) steps

### Option B: Production Script (Without Docker)

```cmd
# 1. Clone repository
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli

# 2. Run production script
run_production_windows.bat
```

The script will:
- Create virtual environment automatically
- Install all dependencies including Waitress WSGI server
- Generate secure SECRET_KEY
- Start production server on port 8000

**Access:** http://localhost:8000

### Option C: Manual Development Setup

```cmd
# 1. Clone repository
git clone https://github.com/gilbertbouic/Mkweli.git
cd Mkweli

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start development server
python app.py
```

**Access:** http://localhost:5000

---

## 🐳 Docker Commands Reference

### Basic Operations

```bash
# Start application (in background)
docker-compose up -d

# Stop application
docker-compose down

# Restart application
docker-compose restart

# View status
docker-compose ps
```

### Logs & Monitoring

```bash
# View live logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View specific time range
docker-compose logs --since="2024-01-01T00:00:00"
```

### Maintenance

```bash
# Rebuild container (after code changes)
docker-compose up -d --build

# Remove container and volumes (⚠️ deletes database)
docker-compose down -v

# Update to latest version
git pull
docker-compose up -d --build
```

### Resource Management

```bash
# View container resource usage
docker stats mkweli-aml

# Enter container shell (for debugging)
docker exec -it mkweli-aml /bin/bash
```

### Configuration

Edit `.env` file to change settings:

```bash
# Port (default: 8000)
PORT=8000

# Workers (default: 4, recommended: 2-4 × CPU cores)
WORKERS=4

# Secret key (MUST change for production)
SECRET_KEY=your-secure-random-key-here
```

---

## 🔑 Database Initialization & Admin Password

### First Run

The database is automatically initialized when the application starts:
- SQLite database created in `instance/` directory
- Default admin user created (password: `admin123`)
- Sanctions data parsed from `data/` folder (30-60 seconds on first run)

### Changing Admin Password

**⚠️ IMPORTANT: Change the default password immediately!**

1. Log in with password `admin123`
2. Go to **Setup** (gear icon in navigation)
3. Click **Change Password**
4. Enter current password and new password
5. Click **Change Password**

### Database Backup

**Docker:**
```bash
# Backup database
docker cp mkweli-aml:/app/instance/mkweli.db ./backup-mkweli.db

# Restore database
docker cp ./backup-mkweli.db mkweli-aml:/app/instance/mkweli.db
docker-compose restart
```

**Non-Docker:**
```bash
# Backup
cp instance/mkweli.db backup-mkweli.db

# Restore
cp backup-mkweli.db instance/mkweli.db
```

---

## 🔄 Updating Sanctions Data

The app shows an alert on the Dashboard when data is older than 14 days.

### Manual Update

1. Download latest XML files from official sources (links below)
2. Rename files to match these exact names:
   - `un_consolidated.xml`
   - `uk_consolidated.xml`
   - `ofac_consolidated.xml`
   - `eu_consolidated.xml`
3. Replace files in `data/` folder
4. Go to **Dashboard** → Click **Reload Lists**

### Official Sanctions List Sources

| Source | Download URL |
|--------|--------------|
| **UN** | https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list |
| **UK** | https://www.gov.uk/government/publications/the-uk-sanctions-list |
| **OFAC** | https://sanctionslist.ofac.treas.gov/Home/SdnList |
| **EU** | https://www.sanctionsmap.eu |

### Using Git Pull (Paid Service)

Contact repository owner for paid sanctions update service:

```bash
git pull origin main
# Sanctions files update automatically in data/ folder
```

---

## 🏥 Health Monitoring

### Health Check Endpoint

The application provides a health check endpoint for monitoring:

```bash
# Check health status
curl http://localhost:8000/health
```

**Healthy Response:**
```json
{
    "status": "healthy",
    "database": "healthy",
    "sanctions_data": "loaded",
    "timestamp": "2024-01-15T10:30:00.000000"
}
```

**Degraded Response (HTTP 503):**
```json
{
    "status": "degraded",
    "database": "unhealthy: connection failed",
    "sanctions_data": "not loaded",
    "timestamp": "2024-01-15T10:30:00.000000"
}
```

### Docker Health Checks

Docker automatically monitors container health every 30 seconds:

```bash
# View container health
docker inspect --format='{{.State.Health.Status}}' mkweli-aml

# View health check history
docker inspect --format='{{json .State.Health}}' mkweli-aml | jq
```

---

## 🔧 Troubleshooting

### Port Already in Use

**Docker:**
```bash
# Change port in .env file
PORT=8080

# Restart container
docker-compose up -d
```

**Non-Docker:**
```bash
# Linux
PORT=8080 ./run_production_linux.sh

# Windows
set PORT=8080
run_production_windows.bat
```

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Common fix: rebuild container
docker-compose down
docker-compose up -d --build
```

### Database Locked

```bash
# Docker
docker-compose down
docker volume rm mkweli_mkweli-db
docker-compose up -d

# Non-Docker
rm -rf instance/
python3 app.py  # Will recreate database
```

### Sanctions Data Not Loading

```bash
# Check if data files exist
ls -lh data/

# Expected output:
# -rw-r--r-- 1 user user  23M data/eu_consolidated.xml
# -rw-r--r-- 1 user user 100M data/ofac_consolidated.xml
# -rw-r--r-- 1 user user  19M data/uk_consolidated.xml
# -rw-r--r-- 1 user user  19M data/un_consolidated.xml

# If missing, ensure all 4 XML files are in data/ folder
```

### Slow Screening on First Run

First time parsing ~160MB of sanctions data takes 30-60 seconds. Subsequent searches are instant (cached).

### Permission Denied (Linux)

```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x run_production_linux.sh
```

### Memory Issues

If the application crashes with memory errors:

```bash
# Increase Docker memory limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

---

## 📁 File Structure & Architecture

```
Mkweli/
├── data/                          # Sanctions data (160MB)
│   ├── eu_consolidated.xml        # ✅ Pre-loaded
│   ├── ofac_consolidated.xml      # ✅ Pre-loaded
│   ├── uk_consolidated.xml        # ✅ Pre-loaded
│   └── un_consolidated.xml        # ✅ Pre-loaded
│
├── app/                           # Application modules
│   ├── enhanced_matcher.py        # 4-layer fuzzy matching
│   ├── sanctions_service.py       # Data loading & caching
│   └── ...
│
├── templates/                     # HTML templates
├── static/                        # CSS/JS assets
├── instance/                      # Database (auto-created)
│
├── app.py                         # Main Flask application
├── config.py                      # Configuration classes
├── requirements.txt               # Development dependencies
├── requirements-prod.txt          # Production dependencies
│
├── Dockerfile                     # Docker container definition
├── docker-compose.yml             # Docker orchestration
├── .dockerignore                  # Docker build exclusions
├── .env.example                   # Environment template
│
├── run_production_linux.sh        # Linux production script
├── run_production_windows.bat     # Windows production script
├── run_linux.sh                   # Linux development script
├── run_windows.bat                # Windows development script
│
└── README.md                      # This file
```

---

## 🔒 Security Best Practices

### Production Deployment

1. **Change default password immediately** after first login
2. **Generate secure SECRET_KEY** - never use the default
3. **Use HTTPS** in production (behind reverse proxy like nginx)
4. **Restrict network access** - don't expose directly to internet
5. **Regular backups** of database
6. **Keep sanctions data updated** every 14 days

### Environment Variables

Never commit secrets to version control:

```bash
# Good: Use environment variables
SECRET_KEY=your-secure-key-here

# Bad: Don't hardcode in code
app.config['SECRET_KEY'] = 'hardcoded-secret'  # NEVER DO THIS
```

### Docker Security

The Docker container:
- Runs as non-root user (`mkweli`)
- Has read-only access to sanctions data
- Uses resource limits (CPU/memory)
- Includes health checks

---

## 📞 Support & Updates

### Contact

- **Email:** gilbert@Mkweli.tech
- **Repository:** https://github.com/gilbertbouic/Mkweli
- **Issues:** https://github.com/gilbertbouic/Mkweli/issues

### Updating Mkweli

```bash
# Pull latest code
git pull origin main

# Docker: Rebuild container
docker-compose up -d --build

# Non-Docker: Reinstall dependencies
pip install -r requirements.txt
```

### Reporting Issues

When reporting issues, please include:
1. Operating system (Windows/Linux/Mac)
2. Deployment method (Docker/Script/Manual)
3. Error logs (`docker-compose logs` or console output)
4. Steps to reproduce the issue

---

## 📄 License

See [LICENSE](LICENSE) file for details. 
