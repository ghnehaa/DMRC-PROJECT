Here is a comprehensive, professional, and well-structured `README.md` file designed specifically for your **Delhi Metro Line 7 SCADA Simulation System**. It incorporates the inputs, outputs, system logic, and installation steps we went through so anyone can easily clone, install, and test your repository.

---

# Delhi Metro Line 7 (Pink Line) - ATS/CBI/ATP Operation Simulator

A web-based SCADA (Supervisory Control and Data Acquisition) Train Simulation System built using Django and modern web technologies. This application replicates live railway signaling, interlocking, and telemetry logic for the **Delhi Metro Line 7 (Pink Line)**, modeling core rail automation subsystems: **Automated Train Supervision (ATS)**, **Computer-Based Interlocking (CBI)**, and **Automatic Train Protection (ATP)**.

---

## 🚇 Subsystem Framework

* **ATS (Automated Train Supervision):** Provides the operator control interface (OCC Dashboard), schedules tracking states, monitors active alarms, and handles command logs.
* **CBI (Computer-Based Interlocking):** Manages wayside safety logic, ensuring points/crossovers and signals align safely to prevent route conflicts or collisions.
* **ATP (Automatic Train Protection):** Operates on-board the train, continuously calculating emergency braking curve profiles against track occupancies ahead.

---

## 🏗️ Architecture & File Structure

The project is structured around Django's Model-View-Template (MVT) architecture pattern:

```text
trainee-sim-neha/
│
└── dmrc project/                  # Main Django Root Directory
    ├── manage.py                  # Django CLI administrative entry point
    │
    ├── dmrc_project/              # Global Core Configurations
    │   ├── settings.py            # System configuration, database configurations, and middleware
    │   └── urls.py                # Main network routing configurations
    │
    └── dashboard/                 # Main Core Simulation Application
        ├── models.py              # Infrastructure database schemas (stations, track layouts)
        ├── views.py               # Main simulation loop execution & physics calculation engine
        ├── urls.py                # Dashboard page API endpoint mapping
        └── templates/
            └── dashboard/
                └── layout.html    # Frontend SCADA UI (SVG Graphics engine & async polling loop)

```

---

## ⚙️ Core Logic, Inputs & Outputs

### 1. Backend Processing Engine (`dashboard/views.py` & `models.py`)

* **Logic:** Tracks physical assets via the Django ORM database layer. Calculates real-time train kinematics using discrete motion equations:

$$v = u + at$$


$$s = ut + \frac{1}{2}at^2$$



If an upcoming tracking circuit block evaluates as occupied (`is_occupied: true`), an ATP overriding Emergency Braking Distance (EBD) decelerating velocity profile is initiated.
* **Input:** Automated client asynchronously polled HTTP requests (`/simulation/tick/`).
* **Output:** Generates structured telemetry JSON streams detailing train coordinate matrices, signal configurations, and track block conditions.

### 2. Frontend Visualization Dashboard (`dashboard/templates/dashboard/layout.html`)

* **Logic:** Renders a static layout representing stations, turnouts, and wayside markers using dynamic vector graphics (SVG). Runs a JavaScript async `fetch()` polling interval loop executing every **100ms** to handle data binding updates.
* **Input:** Receives structured real-time JSON payloads from the server endpoint.
* **Output:** Smoothly translates the train SVG element across track paths via 2D matrix configurations, alters track color variables (Green = Clear, Red = Occupied), and streams active operational alerts into log lists.

---

## 🚀 Local Installation & Setup Guide

Ensure you have **Python 3.x** installed on your operating system, then open a terminal window and execute these configuration commands:

### Step 1: Clone the Project

```bash
git clone https://github.com/kinshookchaturvedi-cell/trainee-sim-neha.git
cd trainee-sim-neha

```

### Step 2: Initialize an Isolated Virtual Environment

```bash
# Create the environment
python3 -m venv venv

# Activate on macOS/Linux:
source venv/bin/activate

# Activate on Windows (Command Prompt):
venv\Scripts\activate

```

### Step 3: Navigate and Install Dependencies

```bash
cd "dmrc project"
pip install django

```

### Step 4: Run Database Migrations

Initialize the baseline tracking layout configuration constraints by updating your local database architecture:

```bash
python manage.py migrate

```

### Step 5: Start the Development Server

```bash
python manage.py runserver

```

### Step 6: Test the App

Open your web browser and navigate to the local environment link provided in your terminal output:
👉 **[http://127.0.0.1:8000/](https://www.google.com/search?q=http://127.0.0.1:8000/)**

---

## 📊 Data Exchange Payload Example

The `/simulation/tick/` endpoint populates the interactive layout using the following schema structure:

```json
{
  "train": {
    "x": 768,
    "y": 135,
    "speed": 15.2,
    "acc": 0.25,
    "state": "RUNNING",
    "dwell_timer": 0
  },
  "track_circuits": [
    { "tc_id": "AX16", "line": "up", "is_occupied": true }
  ],
  "signals": [
    { "signal_id": "SIG-UP-13", "aspect": "GREEN" }
  ],
  "event_logs": [
    { "timestamp": "12:04:11", "type": "INFO", "message": "Train TR-0011 accelerating out of Station S13." }
  ]
}

```
