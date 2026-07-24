# **Delhi Metro Rail Corporation (DMRC) — Signaling & Control Simulator**

> **A web-based, real-time metro railway control and simulation platform built using Python (Django), SQLite, HTML5, CSS3, and Vanilla JavaScript.**

---

## **Table of Contents**

1. [Project Overview](#1-project-overview)
2. [Objectives & Problem Statement](#2-objectives--problem-statement)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture & Block Diagram](#4-system-architecture--block-diagram)
5. [Module & File Structure](#5-module--file-structure)
6. [Backend — Object-Oriented Design (OOP Classes)](#6-backend--object-oriented-design-oop-classes)
7. [Database Design (Models)](#7-database-design-models)
8. [URL Routing & API Endpoints](#8-url-routing--api-endpoints)
9. [Simulation Engine — Physics & Kinematics](#9-simulation-engine--physics--kinematics)
10. [Interlocking & Safety Logic](#10-interlocking--safety-logic)
11. [Frontend — Control Centre Dashboard](#11-frontend--control-centre-dashboard)
12. [Features Implemented (What Is Done)](#12-features-implemented-what-is-done)
13. [Setup & Execution Guide](#13-setup--execution-guide)
14. [Operation Workflow](#14-operation-workflow)
15. [Future Scope](#15-future-scope)

---

## **1. Project Overview**

The **DMRC Signaling & Control Simulator** is an interactive, web-based simulation platform designed to model and demonstrate real-world **Delhi Metro Rail Corporation (DMRC)** train control and signaling systems. It simulates the core subsystems of a modern Communications-Based Train Control (CBTC) environment including:

- **ATS** — Automatic Train Supervision
- **CBI** — Computer-Based Interlocking
- **ATP** — Automatic Train Protection
- **ATO** — Automatic Train Operation

The project was developed as a **Summer Training Project** to study metro train control systems, signal engineering, and railway operations through a practical, hands-on software simulation approach. It is based on international standards such as **IEEE 1474 (CBTC moving-block framework)** and DMRC operational procedures.

The simulator allows a user (acting as a Train Controller / OCC Operator) to:
1. Configure a custom metro line layout (number of stations, crossovers, depot links).
2. Visualize the live track network as an **SVG-based schematic diagram** on an Operations Control Centre (OCC)-style dashboard.
3. Observe a train running autonomously with realistic physics (acceleration, cruising, braking, dwelling at stations, crossover navigation).
4. Monitor real-time telemetry: speed, acceleration, active block (track circuit), signal aspects, and dwell timers.
5. Export event logs and layout data to CSV files.

---

## **2. Objectives & Problem Statement**

### **Problem Statement**

Modern metro rail systems are controlled by highly complex, safety-critical systems that are difficult to study without access to actual OCC simulators. Traditional textbook learning cannot provide the dynamic, real-time understanding needed for signaling engineers and operational staff.

### **Objectives**

- Build a web-based, interactive simulator that replicates the core logic of a metro train control system.
- Implement Object-Oriented Programming (OOP) to model real-world railway elements: track circuits, point switches, signal posts, and trains.
- Simulate train kinematics (acceleration profiles, deceleration braking curves, dwell timers).
- Implement computerized interlocking logic: automatic block occupation, signal cascade (RED to VIOLET to GREEN), and point locking.
- Provide a real-time OCC-style dashboard with a live SVG track schematic and telemetry HUD.
- Allow dynamic layout generation (user-defined number of stations, crossovers, depots) stored in a database.
- Enable CSV export of telemetry and event logs for post-simulation analysis.

---

## **3. Technology Stack**

| Layer | Technology | Purpose |
|---|---|---|
| **Backend Language** | Python 3.x | Core simulation logic, OOP classes, physics engine |
| **Web Framework** | Django (MVC) | Request handling, routing, session management, ORM |
| **Database** | SQLite3 via Django ORM | Persistent storage of layouts, stations, crossovers, depots |
| **Frontend Structure** | HTML5 | Semantic page structure, SVG rendering canvas |
| **Frontend Styling** | Vanilla CSS3 | Dark-mode OCC dashboard, glassmorphism HUD cards, glow effects |
| **Frontend Logic** | Vanilla JavaScript ES6+ | AJAX polling loop, live SVG updates, HUD telemetry rendering |
| **Data Exchange** | JSON AJAX REST API | Backend to Frontend real-time communication |
| **Fonts** | Google Fonts — Outfit, Share Tech Mono | Premium UI typography |
| **SVG Graphics** | Inline SVG server-rendered + JS-updated | Live track schematic, train marker, signal lights |
| **Session Storage** | Django Server-Side Sessions | Persisting simulation state between AJAX ticks |
| **CSV Export** | Python csv module + Django HttpResponse | Log and layout data download |

---

## **4. System Architecture & Block Diagram**

```
+-----------------------------------------------------------------------------+
|                    USER (OCC Operator / Train Controller)                    |
|                         Web Browser (Chrome / Edge)                          |
+----------------------------------+------------------------------------------+
                                   |  HTTP / AJAX JSON
                                   v
+-----------------------------------------------------------------------------+
|                       DJANGO WEB FRAMEWORK (Backend)                         |
|                                                                              |
|  +-----------------+    +---------------------------+   +----------------+  |
|  |  URL Router     |    |   Django Views (MVC)      |   |  Django ORM    |  |
|  |  (urls.py)      +--->|   (views.py)              +-->|  (SQLite3 DB)  |  |
|  +-----------------+    +-------------+-------------+   +----------------+  |
|                                       |                                      |
|         +-----------------------------+----------------------------+         |
|         v                             v                            v         |
|  +-------------+          +---------------------+    +------------------+   |
|  | MetroNetwork|          |  TrainSimEngine      |    |  Django Session  |   |
|  | (OOP Class) |          |  (Simulation Tick)   |    |  (State Store)   |   |
|  |             |          |                      |    +------------------+   |
|  | TrackCircuit|          |  Train (Kinematics)  |                          |
|  | PointSwitch |          |  evaluate_interlock  |                          |
|  | SignalPost  |          |  build_journey_path  |                          |
|  +-------------+          +---------------------+                           |
+-----------------------------------------------------------------------------+
                                   |  JSON Response
                                   v
+-----------------------------------------------------------------------------+
|                       FRONTEND DASHBOARD (Browser)                           |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |            SVG Track Schematic (Live Updated via JavaScript)           |  |
|  |  UP Track Line | DOWN Track Line | Station Boxes | Crossover Diamonds  |  |
|  |  Depot Links | Signal LEDs (Red/Violet/Green) | Animated Train Marker  |  |
|  +------------------------------------------------------------------------+  |
|  +------------------------------------------------------------------------+  |
|  |                       HUD Telemetry Panel                              |  |
|  |   [Speed km/h]  [Acceleration m/s2]  [Active Block]  [Dwell]  [Signal]|  |
|  +------------------------------------------------------------------------+  |
|  +------------------------------------------------------------------------+  |
|  |               Event Log Panel (Real-Time Activity Feed)                |  |
|  +------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------+
```

### **Data Flow — Simulation Tick Cycle**

```
Browser JavaScript AJAX fetch (every ~33 ms)
        |
        v
  POST /simulation/tick/
        |
        v
  simulation_tick() Django View
        |
        +-- Load Layout from SQLite DB via MetroNetwork class
        +-- Load sim_state from Django Session
        +-- Reconstruct TrainSimEngine object from saved state
        +-- Compute delta-time (dt = now - last_tick_time)
        +-- engine.tick(dt)
        |       +-- Update Train kinematics: speed, acc, position
        |       +-- Detect station stop -> DWELL state trigger
        |       +-- evaluate_interlocking()
        |               +-- Set TrackCircuit occupancy flags
        |               +-- Lock / Unlock PointSwitches
        |               +-- Cascade Signal Aspects: RED / VIOLET / GREEN
        |       +-- Log all state change events
        +-- Save updated sim_state back to Django Session
        +-- Return full JSON Response
                |
                v
        Browser JavaScript updates SVG elements and HUD cards live
```

---

## **5. Module & File Structure**

```
DMRC-PROJECT/
|
+-- README.md                         <- This documentation file
|
+-- dmrc project/                     <- Django Project Root
    |
    +-- manage.py                     <- Django management CLI entry point
    +-- db.sqlite3                    <- SQLite3 database (auto-generated after migrate)
    |
    +-- dmrcproject/                  <- Django Project Configuration Package
    |   +-- __init__.py
    |   +-- settings.py               <- Django settings: DB config, installed apps, sessions
    |   +-- urls.py                   <- Root URL dispatcher (includes dashboard.urls)
    |   +-- wsgi.py                   <- WSGI entry point for production deployment
    |
    +-- dashboard/                    <- Main Django Application Package
        |
        +-- __init__.py
        +-- apps.py                   <- App configuration (DashboardConfig)
        +-- admin.py                  <- Django Admin model registration
        +-- tests.py                  <- Unit test placeholder
        |
        +-- models.py                 <- Database models: Layout, Station, Crossover, Depot
        +-- urls.py                   <- App-level URL patterns and AJAX API endpoints
        +-- views.py                  <- ALL backend logic in one file:
        |                                  OOP Classes: TrackCircuit, PointSwitch,
        |                                    SignalPost, MetroNetwork
        |                                  Django Views: login_view, logout_view,
        |                                    input_view, layout_view, export_csv
        |                                  Simulation Engine: Train, TrainSimEngine,
        |                                    build_journey_path, simulation_tick
        |
        +-- migrations/               <- Django auto-generated DB migration files
        |   +-- 0001_initial.py       <- Initial schema creation migration
        |
        +-- templates/
            +-- dashboard/
                +-- login.html        <- OCC login portal (authentication page)
                +-- input.html        <- Layout configuration form (dynamic fields)
                +-- layout.html       <- Main simulation dashboard: SVG + HUD + Event Log
```

---

## **6. Backend — Object-Oriented Design (OOP Classes)**

The entire backend is contained in `views.py` and implements a clean OOP architecture that mirrors real-world railway signaling elements.

---

### **Class: TrackCircuit**

Represents an **isolated electrical track segment (Block)** that detects train occupancy.

| Attribute | Type | Description |
|---|---|---|
| tc_id | str | Unique identifier, e.g., TC-UP-02, TC-XOV-1 |
| line | str | Track direction: up, down, or crossover |
| start_x | int | Left boundary coordinate in SVG pixels |
| end_x | int | Right boundary coordinate in SVG pixels |
| is_occupied | bool | False = Clear (Pick-up), True = Occupied (Drop) |

In real DMRC systems, track circuits operate on the pick-up / drop relay principle. When a train short-circuits the rails, the relay drops to the occupied state, which triggers interlocking responses.

---

### **Class: PointSwitch**

Represents a **physical crossover track switch** that guides trains between the UP and DOWN lines.

| Attribute | Type | Description |
|---|---|---|
| point_id | str | Unique ID such as P-01 |
| tc_id | str | The track circuit this switch occupies |
| from_station | int | Reference station number |
| to_station | int | Secondary station number |
| position_type | str | before or after the reference station |
| x_left, x_right | int | Geometric SVG boundary coordinates |
| y_up, y_down | int | Y-coordinates for UP and DOWN lines |
| current_state | str | NORMAL (straight) or REVERSE (diverging) |
| is_locked | bool | True when train is in the crossover — cannot switch |

---

### **Class: SignalPost**

Represents a **physical wayside 3-aspect signal** (Green, Violet, Red) that protects block entry.

| Attribute | Type | Description |
|---|---|---|
| signal_id | str | e.g., S-UP-02, S-DN-03, S-CO-1 |
| line | str | up or down |
| x, y | int | SVG layout coordinates |
| protects_tc_id | str | The track circuit this signal controls entry to |
| signal_type | str | station or crossover |
| aspect | str | Current aspect: GREEN, VIOLET, or RED |

Signal aspects follow the **3-aspect cascade rule**: The signal at the rear of the train shows RED, the one behind it shows VIOLET (caution / approach), and all others show GREEN (proceed).

---

### **Class: MetroNetwork**

The **master container class** that reads database models, builds the complete track topology, and instantiates all OOP objects.

**Key method: _build_network()**
1. Creates Station geometry objects from DB records with SVG coordinates.
2. Instantiates TrackCircuit blocks — LEAD (before first station), platform-to-platform sections, and TRAIL (after last station).
3. Instantiates PointSwitch objects for each crossover with correct geometric positions.
4. Instantiates SignalPost objects for each station platform (UP and DOWN lines) and each crossover.

**Key method: get_serialized_data()**
Returns all network elements as JSON-serializable Python dictionaries for frontend rendering and simulation state management.

---

### **Class: Train**

Models the **physical train movement parameters and kinematic state machine**.

| Attribute | Description |
|---|---|
| seg_index | Current journey path segment index |
| seg_progress | Distance traveled within the current segment in meters or pixels |
| speed | Current speed in m/s |
| acc | Current acceleration in m/s squared |
| state | Train state: ACCELERATING, CRUISING, BRAKING, or DWELLING |
| dwell_timer | Platform dwell countdown in seconds |
| x, y | Current SVG canvas coordinates |
| current_tc | Currently occupied track circuit ID |
| chainage | Linear distance from Station 1 in meters |
| direction | UP or DOWN |
| mode | Operation mode: ATO (Automatic Train Operation) |

**calculate_acceleration()** implements a speed-dependent acceleration profile:
- Speed below 30 km/h: 1.3 m/s squared
- Speed between 30 and 45 km/h: 1.2 m/s squared
- Speed above 45 km/h: 1.0 m/s squared

---

### **Class: TrainSimEngine**

The **central Python simulation engine** that drives all physics, occupancy detection, interlocking, and signal cascade logic on every tick.

| Method | Description |
|---|---|
| tick(dt) | Advances all simulation physics by delta-time dt seconds |
| evaluate_interlocking(train_x, train_line) | Runs occupancy, point locking, and signal cascade |
| log_event(message, type) | Appends timestamped events to activity log (max 50) |
| to_dict() | Serializes engine state to Python dict for session storage |
| from_dict(data, ...) | Class method to reconstruct engine from saved session dict |

---

## **7. Database Design (Models)**

**File:** dashboard/models.py

The SQLite3 database schema is managed entirely by the Django ORM. It contains four tables:

### **Layout**
Stores a user-created metro line configuration session.

| Field | Type | Description |
|---|---|---|
| id | AutoField PK | Auto-generated layout ID |
| user | ForeignKey to User | The Django user who created this layout |
| num_stations | IntegerField | Total number of stations on the line |
| num_crossovers | IntegerField | Number of crossover switches defined |
| created_at | DateTimeField | Auto-timestamp of creation |

### **Station**
Represents a single station platform within a layout.

| Field | Type | Description |
|---|---|---|
| layout | ForeignKey to Layout | Parent layout (CASCADE delete) |
| number | IntegerField | Station serial number: 1, 2, 3, ... |

### **Crossover**
Represents a crossover track switch placement.

| Field | Type | Description |
|---|---|---|
| layout | ForeignKey to Layout | Parent layout |
| from_station | IntegerField | Starting station reference number |
| to_station | IntegerField | Ending station reference number |
| position | CharField | before or after the reference station |

### **Depot**
Represents a maintenance depot link from the mainline track.

| Field | Type | Description |
|---|---|---|
| layout | ForeignKey to Layout | Parent layout |
| near_station | IntegerField | Station nearest to the depot entry point |
| track | CharField | up or down line connection |
| position | CharField | before or after the reference station |

---

## **8. URL Routing & API Endpoints**

**File:** dashboard/urls.py

| URL Pattern | View Function | Method | Description |
|---|---|---|---|
| /login/ | login_view | GET, POST | Authentication page — OCC operator login portal |
| /logout/ | logout_view | GET | Logout and redirect to login |
| /input/ | input_view | GET, POST | Layout configuration form — POST saves to DB |
| /layout/ | layout_view | GET | Main simulation dashboard — renders SVG and HUD |
| /layout/select/int:layout_id/ | select_layout | GET | Load a previously saved layout into session |
| /export/ | export_csv | GET | Download current layout data as a CSV file |
| /simulation/tick/ | simulation_tick | POST | AJAX API — executes one simulation tick and returns JSON |

---

## **9. Simulation Engine — Physics & Kinematics**

### **Journey Path Construction**

The function `build_journey_path()` constructs a **closed-loop path** of 4 segments that the train continuously traverses:

1. **UP line** — Left to right from first crossover to last crossover
2. **Terminal crossover** — UP line transitions to DOWN line at the far end
3. **DOWN line** — Right to left from last crossover back to first crossover
4. **Origin crossover** — DOWN line transitions back to UP line

Each segment stores: x1, y1 (start), x2, y2 (end), track type, and pre-calculated length.

### **Train State Machine**

```
        +---------------------------------------------+
        |                                             |
        v                                             |
  [ACCELERATING] ---- reaches speed limit -------> [CRUISING]
        ^                                             |
        |                                             |
   dwell ends                            brake zone ahead detected
        |                                             |
  [DWELLING] <----- arrives at station <----- [BRAKING]
                                                      |
                                          speed reaches 0 at platform
```

### **Kinematic Equations Applied**

| Phase | Formula |
|---|---|
| Velocity update | v = v0 + a times dt |
| Braking distance required | s = v squared divided by (2 times a) |
| Position update | seg_progress += speed times dt |
| Crossover speed limit | 25 km/h |
| Mainline maximum speed | 60 km/h |
| Platform dwell duration | 3.0 seconds |

### **SVG Coordinate System**

- SVG canvas: 1200 x 400 pixels
- 1 SVG pixel is approximately 1 metre for chainage measurement
- UP track line: Y = 120 px
- DOWN track line: Y = 260 px
- Left margin: 100 px — Right margin: 100 px
- Crossover width: 50 px — Crossover setback from platform: 60 px

---

## **10. Interlocking & Safety Logic**

The `evaluate_interlocking()` method runs on every simulation tick and enforces three layered safety checks:

### **Layer 1 — Block Occupancy Detection**

- All track circuits are reset to `is_occupied = False` at the start of each tick.
- The train's current X-coordinate is tested against every track circuit's boundary range on the active track line.
- The matching block is flagged as `is_occupied = True`.
- `train.current_tc` is updated to that circuit's ID for HUD display.

### **Layer 2 — Point Switch Locking (Track Locking)**

- If the currently occupied track circuit ID matches a crossover's `tc_id`, that PointSwitch's `is_locked` flag is set to `True`.
- A locked point **cannot be changed** while a train is physically occupying the crossover.
- Lock and unlock state changes are recorded as WARNING events in the event log.

### **Layer 3 — Three-Aspect Signal Cascade**

All signals are initialized to GREEN at the beginning of each tick. The cascade rule is then applied based on train direction:

**For UP line travel:**
- Signals sorted West to East by X-coordinate.
- Signal immediately behind the train: **RED** — block occupied, stop.
- Signal one step further behind: **VIOLET** — caution, prepare to stop.
- All other signals: **GREEN** — line clear, proceed.
- If the next signal ahead is a crossover type signal: **VIOLET** — caution before turnout.

**For DOWN line travel:**
- Same cascade logic but signals sorted East to West (matching direction of travel).

**For Crossover traversal:**
- The crossover entry signal matching the active turnout segment: **RED**.
- The approach signal immediately behind it: **VIOLET**.

---

## **11. Frontend — Control Centre Dashboard**

### **login.html — Authentication Portal**

- OCC-styled dark-theme login form.
- Accepts Django superuser credentials.
- Uses Django messages framework to display authentication error feedback.

### **input.html — Layout Configuration Panel**

- Dynamic HTML form where the operator specifies:
  - Number of stations (minimum 2 required)
  - Number of crossovers — each with from-station, to-station, and position
  - Number of depot links — each with station number, track (up or down), and position
- Client-side JavaScript dynamically generates form field rows based on count input values.
- On POST submission the backend validates all inputs, automatically injects a terminal crossover if none exists near the last station, saves the layout to the SQLite database, and redirects to the simulation dashboard.

### **layout.html — Live Simulation Dashboard**

**HUD Telemetry Panel (5 real-time cards):**

| Card Label | Data Mapped |
|---|---|
| Train Speed | train.speed multiplied by 3.6 in km/h |
| Acceleration | train.acc in m/s squared |
| Active Block | train.current_tc (track circuit ID) |
| Station Dwell | train.dwell_timer in seconds |
| Signal Ahead | Aspect of the next wayside signal |

**SVG Track Schematic Elements (all live-updated by JavaScript):**

- **UP Track Line** — Glowing blue horizontal line
- **DOWN Track Line** — Glowing blue horizontal line
- **Station Boxes** — Rectangular boxes for both UP (PF-01) and DOWN (PF-02) platforms
- **Crossover Diamonds** — Diamond-shaped indicators showing NORMAL or REVERSE state
- **Depot Branches** — Diagonal branch lines representing depot connections
- **Wayside Signals** — Colored LED circles: Green, Violet, or Red with glow filter
- **Train Marker** — Animated rectangle that moves along the SVG path in real time

**Event Log Panel:**
- Scrollable, color-coded activity feed showing the last 50 events.
- INFO events displayed in grey-white; WARNING events displayed in yellow.

**Operator Controls:**
- **Pause / Resume** button to toggle the AJAX simulation ticker on and off.
- **Configure Layout** link to return to the input form.
- **Export CSV** link to download layout data as a comma-separated file.
- **Logout** link to end the authenticated session.

**AJAX Polling Architecture:**
- JavaScript uses `fetch()` to call `/simulation/tick/` every approximately 33 milliseconds, equivalent to 30 frames per second.
- The JSON response is parsed and all SVG elements and HUD card values are updated in-place without any page reload, creating a smooth real-time animation.

---

## **12. Features Implemented (What Is Done)**

| # | Feature | Status |
|---|---|---|
| 1 | User Authentication — Django Login and Logout | Done |
| 2 | Dynamic Layout Configuration Form with JS-generated fields | Done |
| 3 | SQLite Database Schema — Layout, Station, Crossover, Depot | Done |
| 4 | MetroNetwork OOP Class — Full Track Topology Builder | Done |
| 5 | TrackCircuit OOP Class with Occupancy Detection | Done |
| 6 | PointSwitch OOP Class with Normal/Reverse States and Locking | Done |
| 7 | SignalPost OOP Class — 3-Aspect Green / Violet / Red | Done |
| 8 | Train OOP Class — Full Kinematic State Machine | Done |
| 9 | TrainSimEngine — Physics and Interlocking Loop | Done |
| 10 | build_journey_path — Closed-loop 4-segment path construction | Done |
| 11 | Speed-dependent Acceleration Profile (3 zones) | Done |
| 12 | Braking Curve Calculation at Station Approach | Done |
| 13 | Crossover Speed Restriction (25 km/h caution) | Done |
| 14 | Platform Dwell Timer (3-second automated stop) | Done |
| 15 | 3-Aspect Signal Cascade Logic for UP / DOWN / Crossover | Done |
| 16 | Point Switch Locking During Train Occupation | Done |
| 17 | Real-Time Event Logging (last 50 timestamped entries) | Done |
| 18 | Django Session-Based Simulation State Persistence | Done |
| 19 | AJAX JSON REST API endpoint at /simulation/tick/ | Done |
| 20 | Live SVG Track Schematic — server-initialized, JS-updated | Done |
| 21 | HUD Telemetry Dashboard with 5 real-time data cards | Done |
| 22 | Animated Train Marker on SVG Canvas | Done |
| 23 | Depot Link Visualization on SVG Schematic | Done |
| 24 | Auto Terminal Crossover Injection if missing | Done |
| 25 | CSV Export of Layout and Event Log Data | Done |
| 26 | OCC Dark-Mode Premium Dashboard UI with Glassmorphism | Done |
| 27 | Train Telemetry: mode, direction, chainage, TC ID | Done |
| 28 | Pause and Resume Simulation Control Button | Done |
| 29 | Multiple Layout Save and Load via select_layout endpoint | Done |
| 30 | Responsive SVG Viewport with viewBox scaling | Done |

---

## **13. Setup & Execution Guide**

### **Prerequisites**
- Python 3.x installed on your system.
- pip Python package manager available.

### **Step 1 — Install Django**

Open a terminal or PowerShell window and run:

```
pip install django
```

### **Step 2 — Navigate to the Project Directory**

```
cd "c:\Users\SMB\Desktop\dmrc project\DMRC-PROJECT\dmrc project"
```

### **Step 3 — Apply Database Migrations**

This creates all required SQLite3 tables from the Django models:

```
python manage.py makemigrations
python manage.py migrate
```

### **Step 4 — Create a Superuser Account**

```
python manage.py createsuperuser
```

Follow the interactive prompts to enter a username, email address, and password. These credentials are used to log in to the simulator dashboard.

### **Step 5 — Start the Development Server**

```
python manage.py runserver
```

You will see output confirming the server is running on port 8000.

### **Step 6 — Open the Simulator in Your Browser**

Navigate to:

```
http://127.0.0.1:8000/login/
```

---

## **14. Operation Workflow**

```
Step 1 — Login
        Enter your Django superuser credentials at the OCC portal.

            |
            v

Step 2 — Configure Layout
        Set the number of stations (minimum 2).
        Add crossover entries: from-station, to-station, and position.
        Add depot links if needed: station, track (up/down), position.
        Click GENERATE LAYOUT to save and proceed.

            |
            v

Step 3 — Simulation Dashboard
        The SVG track schematic loads automatically.
        The train begins moving on the UP track.
        The HUD displays real-time speed, acceleration, active block, dwell timer.
        Signals cascade automatically as the train moves through each block.
        Watch crossovers lock and unlock as the train traverses them.
        Monitor the event log panel for all state change notifications.
        Use the Pause button to freeze the simulation at any moment.
        Use the Resume button to continue.

            |
            v

Step 4 — Export Data
        Click Export CSV to download the current layout configuration
        and event data as a CSV file for offline analysis.

            |
            v

Step 5 — Reconfigure
        Click Configure Layout to return to the input form
        and create a new layout configuration.
```

---

## **15. Future Scope**

The following features are planned for future development iterations:

### **Simulation Enhancements**

- **Multiple Trains** — Support for 2 to 5 trains running simultaneously with automatic headway management and rear-end collision avoidance logic.
- **Moving Block CBTC** — Replace fixed block signaling with a continuous moving block authority system based on real-time train position reporting, as per IEEE 1474.
- **Platform Screen Doors (PSD)** — Synchronize PSD opening and closing with train door alignment detection and dwell timer expiry.
- **Failure Injection Panel** — Simulate track circuit failures (shunted or open circuit), signal lamp failures, and point machine failures to test operator response procedures.

### **Advanced Safety Features**

- **Emergency Stop Pushbutton (ESP)** — Allow operators or passengers to trigger an emergency train halt from platform or control room.
- **Signal Post Key (SPK)** — Implement manual key-operated route cancellation for degraded mode operations.
- **Emergency Key Transmitter (EKT)** — Simulate train-to-trackside emergency communication protocols.
- **ATP Emergency Brake Trigger** — Automatically apply emergency brakes when a train exceeds the permitted speed in an occupied or restricted block.
- **Restricted Manual Mode (RM)** — Low-speed manual driving mode for depot entry, shunting, and degraded operations at 25 km/h maximum.

### **Operational Features**

- **Headway Calculator** — Real-time display of minimum safe headway based on current train separations and speed profiles.
- **Schedule and Timetable Module** — Define a departure timetable for each station and measure schedule adherence with delay reporting.
- **Skip-Stop Planning** — Allow the OCC operator to designate express services that bypass selected intermediate stations.
- **Train Hold Instructions** — Issue platform hold commands to delay a train's departure and adjust headway spacing.

### **Analytics and Reporting**

- **Real-Time Dashboard Analytics** — Average speed metrics, dwell time compliance rates, and headway trend charts.
- **Full Event Log Export** — Complete timestamped CSV or JSON export of all simulation events across a full run.
- **Journey Chart** — Graphical speed-distance (V-D) and speed-time (V-T) profile visualization rendered using canvas charts.
- **Energy Consumption Simulation** — Estimate electrical energy usage based on traction and braking force profiles.

### **Technical Improvements**

- **WebSockets via Django Channels** — Replace the current AJAX polling loop with a push-based WebSocket connection for lower latency, reduced HTTP overhead, and smoother animation.
- **Multi-User OCC** — Implement role-based access control with separate roles for Train Controller, Station Master, and Maintenance Engineer, sharing a synchronized simulation state.
- **Mobile-Responsive Dashboard** — Adapt the layout for tablet-based field monitoring by DMRC staff.
- **Dockerized Deployment** — Package the application as a Docker container for one-command deployment on any server or cloud platform.
- **PostgreSQL Migration** — Upgrade the database backend from SQLite3 to PostgreSQL for production-scale deployments with concurrent users.
- **Automated Unit Tests** — Implement complete test coverage for all OOP classes, physics calculations, interlocking logic, and API endpoint responses.
- **Extended Django Admin Panel** — Add custom admin views showing layout statistics, simulation history, and user activity analytics.

---

## **License**

This project was developed as an academic **Summer Training Project** for demonstration and educational purposes, based on publicly available DMRC operational knowledge and IEEE CBTC standards framework.

---

*DMRC Signaling and Control Simulator — Built with Python, Django, and Vanilla Web Technologies.*
