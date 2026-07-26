# **DMRC Signaling & Control Simulator — Complete System Installation & Environment Setup Guide**

> **Official Installation & Deployment Manual** for running the Delhi Metro Rail Corporation (DMRC) Signaling & Train Control Simulator on any operating system (Windows, macOS, Linux, WSL, Docker, or Cloud VPS).

---

## **Table of Contents**

1. [System & Software Prerequisites](#1-system--software-prerequisites)
2. [Quick Start (Automated One-Click Setup)](#2-quick-start-automated-one-click-setup)
3. [Step-by-Step Manual Installation](#3-step-by-step-manual-installation)
   - [Step 1: Clone / Obtain Codebase](#step-1-clone--obtain-codebase)
   - [Step 2: Create Python Virtual Environment](#step-2-create-python-virtual-environment)
   - [Step 3: Activate Virtual Environment](#step-3-activate-virtual-environment)
   - [Step 4: Install Dependencies](#step-4-install-dependencies)
   - [Step 5: Apply Database Migrations](#step-5-apply-database-migrations)
   - [Step 6: (Optional) Create Administrative Account](#step-6-optional-create-administrative-account)
   - [Step 7: Launch Development Server](#step-7-launch-development-server)
   - [Step 8: Access Web Interface](#step-8-access-web-interface)
4. [Environment & Configuration Settings](#4-environment--configuration-settings)
5. [Network & Multi-Device Access (LAN / OCC Deployment)](#5-network--multi-device-access-lan--occ-deployment)
6. [Troubleshooting & Common Failure Resolution](#6-troubleshooting--common-failure-resolution)
7. [Verification & Verification Checklist](#7-verification--verification-checklist)

---

## **1. System & Software Prerequisites**

Before installing the DMRC Simulator, ensure your system satisfies the following software and hardware requirements:

### **Hardware Requirements**
- **Processor**: Dual-Core 1.5 GHz or higher (Intel/AMD x86_64, Apple Silicon M1/M2/M3, or ARM64)
- **RAM**: Minimum 2 GB (4 GB recommended)
- **Storage**: At least 100 MB available disk space

### **Supported Operating Systems**
- **Windows**: Windows 10, Windows 11, Windows Server 2016+
- **macOS**: macOS 10.15 (Catalina) or later (Intel & Apple Silicon)
- **Linux**: Ubuntu 20.04+, Debian 10+, Fedora 32+, RHEL/CentOS 8+, Arch Linux
- **Subsystems**: Windows Subsystem for Linux (WSL1 / WSL2)

### **Software Prerequisites**
1. **Python 3.8 or Higher** (Python 3.8, 3.9, 3.10, 3.11, 3.12+ supported)
   - Check version: `python --version` or `python3 --version`
   - *Windows Note*: Ensure "Add Python to PATH" checkbox is ticked during Python installation.
2. **pip** (Python package installer)
   - Check version: `pip --version` or `python -m pip --version`
3. **SQLite3** (Included standard with Python installation)
4. **Modern Web Browser**
   - Google Chrome, Microsoft Edge, Mozilla Firefox, or Apple Safari with JavaScript enabled and HTML5 SVG support.

---

## **2. Quick Start (Automated One-Click Setup)**

For maximum ease of use, pre-configured automated setup scripts are included in the repository.

### **On Windows (Command Prompt / PowerShell)**
Double-click `setup.bat` or run in terminal:
```cmd
setup.bat
```
*What this script does automatically:*
1. Verifies Python installation.
2. Creates an isolated `.venv` virtual environment.
3. Upgrades `pip` and installs required packages from `requirements.txt`.
4. Runs database migrations (`python manage.py migrate`).
5. Opens your default browser to `http://127.0.0.1:8000/login/`.
6. Starts the Django development web server.

### **On Linux / macOS / WSL**
Open terminal, give execute permission, and run `setup.sh`:
```bash
chmod +x setup.sh
./setup.sh
```
*What this script does automatically:*
1. Detects `python3` / `pip3`.
2. Sets up `.venv` environment.
3. Installs `requirements.txt`.
4. Initializes database schema via Django ORM.
5. Launches the HTTP server and opens the browser.

---

## **3. Step-by-Step Manual Installation**

If you prefer installing manually or are setting up a custom server environment, follow these steps:

### **Step 1: Clone / Obtain Codebase**
Navigate to your desired project workspace:
```bash
git clone https://github.com/YourUsername/DMRC-PROJECT.git
cd DMRC-PROJECT/"dmrc project"
```

### **Step 2: Create Python Virtual Environment**
Creating a virtual environment ensures Python dependencies do not conflict with system packages:
```bash
# Windows
python -m venv .venv

# Linux / macOS
python3 -m venv .venv
```

### **Step 3: Activate Virtual Environment**
Activate the environment for your shell:

- **Windows Command Prompt (cmd.exe)**:
  ```cmd
  .venv\Scripts\activate
  ```
- **Windows PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(If PowerShell blocks script execution, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)*

- **Linux / macOS (Bash / Zsh)**:
  ```bash
  source .venv/bin/activate
  ```

Once activated, your terminal prompt will show `(.venv)`.

### **Step 4: Install Dependencies**
Install Django and required dependencies via `requirements.txt`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

To verify installation:
```bash
python -m django --version
```

### **Step 5: Apply Database Migrations**
Initialize the SQLite database schema (`db.sqlite3`):
```bash
python manage.py makemigrations
python manage.py migrate
```

### **Step 6: (Optional) Create Administrative Account**
To access Django's built-in Admin Panel (`/admin/`), create a superuser account:
```bash
python manage.py createsuperuser
```
Follow prompts to set username, email, and password.

### **Step 7: Launch Development Server**
Start Django's built-in web server:
```bash
python manage.py runserver
```
By default, the server binds to `127.0.0.1:8000`.

### **Step 8: Access Web Interface**
Open your web browser and navigate to:
- **Login Portal**: [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
- **Layout Configurator**: [http://127.0.0.1:8000/input/](http://127.0.0.1:8000/input/)
- **Django Admin Panel**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## **4. Environment & Configuration Settings**

Configuration is controlled via `dmrcproject/settings.py`:

| Setting | Default Value | Purpose |
|---|---|---|
| `SECRET_KEY` | `django-insecure-...` | Django cryptographic signing key. Change in production. |
| `DEBUG` | `True` | Displays error tracebacks in browser during development. |
| `ALLOWED_HOSTS` | `[]` (or `['*']`) | Allowed hostnames/IP addresses when binding to network interfaces. |
| `DATABASES` | `sqlite3` (`db.sqlite3`) | Relational database file path. |
| `SESSION_ENGINE` | `django.contrib.sessions` | Server-side session state engine for live simulation ticks. |

### **Customizing HTTP Port**
If port 8000 is occupied by another application, specify an alternate port:
```bash
python manage.py runserver 8080
```

---

## **5. Network & Multi-Device Access (LAN / OCC Deployment)**

To view the simulation from other computers or tablets on the same Local Area Network (LAN):

1. Edit `dmrcproject/settings.py` and allow network access:
   ```python
   ALLOWED_HOSTS = ['*']
   ```
2. Start Django server bound to all network interfaces:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
3. Find host IP address:
   - Windows: `ipconfig` (Look for IPv4 Address, e.g. `192.168.1.15`)
   - Linux / macOS: `ifconfig` or `ip a`
4. Access simulator on client device browser:
   `http://<HOST_IP_ADDRESS>:8000/login/`

---

## **6. Troubleshooting & Common Failure Resolution**

### **Issue 1: `python` or `pip` command not recognized (Windows)**
- **Cause**: Python is installed but not added to system Environment Variables (`PATH`).
- **Solution**: Re-run Python installer, choose "Modify", check **"Add Python to environment variables"**, and click Install. Or invoke python via launcher: `py -3 manage.py runserver`.

### **Issue 2: `ImportError: Couldn't import Django`**
- **Cause**: Virtual environment is not activated or `requirements.txt` was not installed in active environment.
- **Solution**: Ensure `(.venv)` is visible in prompt, then run `pip install -r requirements.txt`.

### **Issue 3: `Port 8000 is already in use`**
- **Cause**: Another process (e.g. previous server run, Node.js app) is using port 8000.
- **Solution**: Kill running process or run on new port: `python manage.py runserver 8050`.

### **Issue 4: SQLite Database Locked / Migration Errors**
- **Cause**: Corrupted database file or simultaneous write locks.
- **Solution**: Delete `db.sqlite3`, then re-run `python manage.py migrate`.

---

## **7. Verification & Smoke Test Checklist**

After installation, perform the following smoke tests to verify complete system functionality:

- [x] **Authentication Test**: Navigate to `/login/`, sign up a test user (e.g., `operator1`), and verify successful redirect to `/input/`.
- [x] **Layout Generation Test**: Enter `5` Stations, `2` Crossovers, `1` Depot, submit form, and confirm redirect to `/layout/`.
- [x] **SVG Schematic Rendering**: Verify SVG track network renders with UP line, DOWN line, station boxes (`ST-01` to `ST-05`), crossover diamonds, and 3-aspect signal LEDs.
- [x] **Live Tick Simulation Loop**: Click **Start / Resume**, verify train marker moves smoothly across track circuits, signals update aspect (GREEN -> RED -> VIOLET -> GREEN), HUD telemetry displays speed and acceleration, and Event Log records live events.
- [x] **CSV Export Verification**: Click **Export Log (CSV)** and **Export Layout (CSV)**; verify CSV files download with valid headers and row data.
