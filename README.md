# HealthPulse — Weight & Steps Tracker

A fullstack application for tracking daily weight and step counts, visualizing progress over time, and monitoring goal streaks.

## Architecture

* **Backend**: Python 3.12 + Flask REST API with SQLite database (`tracker.db`) in a dedicated `.venv`.
* **Frontend**: React 18 + Vite with Lucide icons, responsive SVG trend charts, and modal loggers.
* **Communication**: Decoupled REST API with CORS and Vite proxy (`/api`).

## Project Layout

```
health-tracker/
├── .venv/                      # Python virtual environment
├── backend/
│   ├── app.py                  # Flask REST API server (port 5000)
│   ├── database.py             # SQLite connection, models & queries
│   ├── seed.py                 # Initial 14-day sample dataset generator
│   └── requirements.txt        # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MetricCards.jsx # Top metric cards (Weight, Steps, 7-day avg, Streak)
│   │   │   ├── Charts.jsx      # Interactive weight curve & step bar visualizers
│   │   │   ├── EntryForm.jsx   # Modal for adding/editing daily weight & steps
│   │   │   ├── HistoryTable.jsx# Searchable, filterable entry logs
│   │   │   └── GoalSettings.jsx# Target weight & step goal configuration
│   │   ├── App.jsx             # Main dashboard
│   │   ├── index.css           # Styling & design system
│   │   └── main.jsx            # Entry point
│   ├── package.json
│   └── vite.config.js
├── run.sh                      # Launch both backend and frontend together
└── README.md
```

## Quick Start

### 1. Launch the Application
Run the helper script from the project root:
```bash
./run.sh
```

Or run each service separately:

#### Start Flask Backend:
```bash
./.venv/bin/python backend/app.py
```
Backend runs on `http://127.0.0.1:5000`

#### Start React Frontend:
```bash
cd frontend
npm run dev
```
Frontend runs on `http://localhost:5173`

## API Endpoints

* `GET /api/entries`: List all weight & step entries (newest first).
* `POST /api/entries`: Create or upsert entry (`{ "date": "YYYY-MM-DD", "weight": 178.5, "steps": 10500, "notes": "..." }`).
* `PUT /api/entries/<id>`: Update an entry.
* `DELETE /api/entries/<id>`: Delete an entry.
* `GET /api/stats`: Compute 7-day average, streak, weight progress %, best days.
* `GET /api/goals` & `POST /api/goals`: Retrieve and update target step/weight goals.
