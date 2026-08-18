# 🏃 HealthPulse — Secure Multi-User Weight & Activity Tracker

A fullstack health tracking platform built with **SQLAlchemy 2.0 ORM**, **Pydantic v2 DTOs**, **Passkeys & Biometric authentication (Face ID / Touch ID)**, **Fernet AES Secrets Vault encryption at rest**, **automated Let's Encrypt SSL management**, **asynchronous Google Gemini Flash Vision scale parsing**, and **per-user data isolation**.

---

## 🌟 Key Features

- **👤 Multi-User Data Isolation**:
  - Secure user accounts with password hashing (PBKDF2-SHA256) & JWT session management.
  - Complete per-user data scoping: your entries, step history, trendlines, and goals remain private to your account.
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
- **📈 Interactive React Dashboard**:
  - Weight progression trendlines & goal markers.
  - 7-day and 30-day moving step averages.
  - Daily streak counters and goal progress bars.

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

HealthPulse includes a full 3-tier regression testing suite covering backend Python APIs, frontend React components, and live JSON REST API endpoints:

```bash
# Run ALL regression test suites
./test.sh --all

# Run Python backend regression tests (Pytest - 25 tests)
./test.sh --backend

# Run React frontend component tests (Vitest - 12 tests)
./test.sh --frontend

# Run live JSON REST API regression test runner (13 tests)
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
