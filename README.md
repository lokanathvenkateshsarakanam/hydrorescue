# HydroRescue™ | Verified 24/7 Emergency Plumbing Network

An on-demand emergency plumbing dispatch platform engineered to solve the systemic market failures of night and weekend home plumbing crises.

---

## 📌 Problem Statement Addressed

> *"Homeowners facing plumbing emergencies at night or weekends cannot find verified, trustworthy plumbers instantly. Local search results show unverified listings with no ratings or background checks. Emergency charges are inflated 2-3x. Service quality is unpredictable. No on-demand platform provides verified emergency plumbers with transparent pricing and instant availability."*

---

## 💡 How HydroRescue Solves the 5 Core Failures

| Failure in Market | Conventional Reality | HydroRescue Solution |
| :--- | :--- | :--- |
| **1. 2:00 AM Availability** | Search engines & directories sell leads to 5 contractors whose phones are on silent. | **Live Telemetry & On-Duty Radar**: Plumbers explicitly check in "On-Call". Instant dispatch matching with sub-20m arrival times. |
| **2. Unverified Trades & Handymen** | Lead-gen directories list unverified handymen with fake reviews and no liability coverage. | **Credential Audit Vault**: Mandatory State Master Plumber license verification, $2M liability insurance check, and criminal background vetting. |
| **3. 2x–3x Distress Price Gouging** | Plumbers exploit flooded basements with surprise $1,500–$2,500 emergency fees. | **Algorithmic Anti-Gouging Cap**: Emergency rates are strictly capped at 1.4x daytime standard. Upfront price book benchmarks. |
| **4. Inescapable Water Damage** | Homeowners panic while water pumps 10 gallons/minute into their living room. | **Integrated 60-Second Shutoff Guide**: Immediate visual first-aid to locate & close main valves before plumber arrives. |
| **5. Unpredictable Service Quality** | No recourse after cash payment is handed over; plumbers ghost on callbacks. | **Escrow Protection & 90-Day Warranty**: Funds held in secure escrow until customer verifies repair, activating an automated 90-day warranty certificate. |

---

## 🛠️ System Architecture & Features

### 1. Homeowner SOS Portal (`/`)
* **Instant Emergency Dispatch Form**: Select emergency category (Burst Pipe, Sewer Backup, Water Heater Rupture, Broken Main Valve).
* **Transparent Pricing Matrix**: Live comparison of HydroRescue price cap vs. predatory broker rates.
* **Interactive Plumber Radar & Live Map**: Leaflet.js map tracking nearby on-duty service trucks with ETA tags.
* **Live Dispatch Progress Bar**: Real-time status updates (*Dispatched → En Route → On-Site → Completed*).
* **License & Insurance Auditor**: Full public inspection modal of plumber state registration numbers and commercial insurance policies.
* **Audio Alerts**: Real-time Web Audio API synthesizer for emergency notifications and confirmation chimes.

### 2. Plumber On-Duty Mobile Terminal (`/plumber`)
* **On-Call Toggle**: Plumbers switch between *On-Call* and *Standby* with guaranteed escrow payouts.
* **Emergency Dispatch Receiver**: View incoming dispatch, customer water-shutoff status, and location.
* **Workflow Progression Controller**: Plumber advances dispatch state (*Accepted → En Route → Arrived → In Repair → Complete*).
* **Pre-Approved Itemized Work Order**: Enter labor hours and parts costs with automated anti-gouging formula calculations.
* **Truck Inventory Checklist**: Verifies high-priority emergency equipment (ProPress, 100ft snake, pipe stock).

### 3. Platform Admin & Verification Center (`/admin`)
* **Trade Registry & Compliance Audits**: Verify or suspend plumbers based on state license databases.
* **Anti-Gouging Guardrails**: Real-time regulatory limits, surge caps, and platform savings metrics.

### 4. Interactive Main Water Shut-Off Guide (`/shutoff-guide`)
* Step-by-step visual emergency triage (Basement, Utility Room, Curb Meter Pit).
* Ball valve (quarter-turn) vs. Gate valve (wheel) identification and turning instructions.
* Depressurization procedures to stop residual leaks.

---

## 🚀 Quickstart & Running the Project

### Requirements
* **Python 3.8+** (Uses Flask and SQLite standard library)

### Step 1: Navigate to the Directory
```powershell
cd C:\Users\kalla\.gemini\antigravity\scratch\hydrorescue
```

### Step 2: Initialize Database (Pre-seeded with verified Master Plumbers)
```powershell
python database.py
```

### Step 3: Launch the Server
```powershell
python app.py
```

### Step 4: Open in Your Browser
The server listens simultaneously on both **Port 8000** and **Port 8080**:
* **Homeowner Emergency SOS:** [http://localhost:8000/](http://localhost:8000/) or [http://localhost:8080/](http://localhost:8080/)
* **Plumber On-Duty Terminal:** [http://localhost:8000/plumber](http://localhost:8000/plumber) or [http://localhost:8080/plumber](http://localhost:8080/plumber)
* **Admin Verification & Radar:** [http://localhost:8000/admin](http://localhost:8000/admin) or [http://localhost:8080/admin](http://localhost:8080/admin)
* **Emergency Shutoff Guide:** [http://localhost:8000/shutoff-guide](http://localhost:8000/shutoff-guide) or [http://localhost:8080/shutoff-guide](http://localhost:8080/shutoff-guide)

---

## 📁 Project File Structure

```text
hydrorescue/
├── app.py                      # Flask backend API & page routing
├── database.py                 # SQLite schema, initial seeding, and models
├── hydrorescue.db              # SQLite relational database
├── templates/
│   ├── layout.html             # Base responsive layout with Tailwind & Leaflet
│   ├── index.html              # Homeowner SOS portal & interactive radar
│   ├── plumber_portal.html     # Plumber terminal with on-duty controls & invoicing
│   ├── admin_portal.html       # Admin compliance registry & anti-gouging monitor
│   └── shutoff_guide.html      # Interactive emergency water shutoff guide
├── static/
│   ├── css/
│   │   └── custom.css          # Radar pulse animations and dark map styling
│   └── js/
│       └── app.js              # State machine, map telemetry, audio synthesis
└── README.md                   # Full documentation & project overview
```

---

## 🛡️ Key REST API Endpoints

* `GET /api/categories`: Returns emergency categories with guaranteed price caps and market benchmarks.
* `GET /api/plumbers`: Returns verified plumbers with license numbers, insurance, and on-call status.
* `POST /api/dispatches/create`: Dispatches nearest verified plumber with upfront escrow deposit hold.
* `GET /api/dispatches/active`: Retrieves current active dispatch status and live telemetry.
* `POST /api/dispatches/<id>/status`: Plumber status progression updates.
* `POST /api/dispatches/<id>/shutoff-confirm`: Customer marks main water line as shut off.
* `POST /api/dispatches/<id>/complete-repair`: Plumber submits final itemized invoice.
* `POST /api/dispatches/<id>/release-escrow`: Releases escrow payment and issues 90-day warranty certificate.
* `POST /api/plumber/toggle-duty`: Toggles plumber on-call availability.
* `POST /api/plumber/verify`: Admin verification toggle for trade licenses and insurance policies.
