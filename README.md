# 🏃 HealthPulse — Extensible Multi-User Health & Activity Platform

A fullstack modular health & equipment tracking platform built with **SQLAlchemy 2.0 ORM**, **Pydantic v2 DTOs**, **Metric Component DevKit & Plugin Engine**, **Passkeys & Biometric authentication (Face ID / Touch ID)**, **Fernet AES Secrets Vault encryption at rest**, **automated Let's Encrypt SSL management**, and **asynchronous Google Gemini Flash Vision scale parsing**.

---

## 🌟 Key Features

- **🧩 Metric DevKit & Dynamic Component Model**:
  - All tracking modules (including **Weight Tracker**, **Daily Steps**, and the new **Camera & Lens Gear Log**) are packaged as self-contained plugin components with a declarative `manifest.json`.
  - Add new metric boxes with auto-generated validated GUI forms and database storage without touching core application code.
- **📷 Camera & Lens Gear Session Addin**:
  - Log camera bodies, lenses, shoot timestamps, focal length, aperture, ISO, shutter speeds, and session notes.
  - Generates equipment analytics (total sessions, top camera body used, top lens used).
- **👤 Multi-User Data Isolation**:
  - Secure user accounts with password hashing (PBKDF2-SHA256) & JWT session management.
  - Complete per-user data scoping: your entries, step history, trendlines, and equipment logs remain private to your account.
- **🔑 WebAuthn Passkeys & Biometric Sign-In**:
  - One-touch sign-in using **Apple Face ID**, **Touch ID**, **Windows Hello**, or **Android Fingerprint**.
  - Register and manage multiple biometric devices directly from your account settings.
- **🔒 Authenticated Secrets Vault & Pydantic Configuration**:
  - **Fernet AES-128-CBC encryption at rest**: API keys stored in SQLite are encrypted ciphertext.
  - **Pydantic-Settings (12-Factor App)**: Automatically loads validated configurations from `.env` or system environment.
- **🧠 Async Google Gemini Flash Vision Scale Parsing**:
  - **Instant Async Upload**: Scale photos upload instantly without blocking the UI.
  - **Google Gemini Flash Engine**: High-accuracy parsing on 7-segment digital displays, aqua/blue LCDs, and glass glare reflections.
  - **Camera EXIF Timestamp Extraction**: Reads photo capture date & time (`DateTimeOriginal`) to accurately log past weigh-ins.
- **⚠️ Main Dashboard Status & Error Warning Banner**:
  - If a scale photo was blurry or unreadable, a persistent alert banner appears on the main dashboard indicating that your **most recent valid weight is retained**, with a 1-click button to re-upload.

---

## 🛠️ Component DevKit CLI (`./devkit.sh`)

Create, validate, and install new metric components into HealthPulse with a single command:

```bash
# List all installed tracking components
./devkit.sh list

# Scaffold a new component (e.g. Blood Pressure or Water Intake)
./devkit.sh create --id "blood_pressure" --name "Blood Pressure" --category "cardio" --icon "HeartPulse" --color "#ef4444"

# Validate a component manifest against the specification
./devkit.sh validate plugins/camera_log/

# Install a component package
./devkit.sh install plugins/camera_log/
```

---

## 🚀 Quick Start (Zero Config)

### Prerequisites
- **Python 3.9+**
- **Node.js 18+ & npm**

### 1. Clone & Launch
```bash
# Clone the repository
git clone https://github.com/wjfxport-collab/health-tracker.git
cd health-tracker

# Launch the app (auto-installs Python .venv and npm packages on first run)
./run.sh
```

### 2. Access HealthPulse
- **Web Dashboard**: `http://localhost:5173`
- **Backend API**: `http://localhost:5000` (or `https://localhost:5000` with SSL)

---

## 🧪 Unified Regression Testing Suite

HealthPulse includes a full 3-tier regression testing suite:

```bash
# Run ALL regression test suites (61 tests total - 100% Pass Rate)
./test.sh --all

# Run Python backend regression tests (Pytest - 31 tests)
./test.sh --backend

# Run React frontend component tests (Vitest - 16 tests)
./test.sh --frontend

# Run live JSON REST API regression test runner (14 tests)
./test.sh --api
```

---

## 🔒 SSL & Let's Encrypt Automation

### Setup Let's Encrypt (Production Domain)
```bash
./setup_ssl.sh --domain yourdomain.com --email you@example.com
```

### Local Development / LAN Self-Signed SSL (for Biometric Testing)
```bash
./setup_ssl.sh --self-signed
```
