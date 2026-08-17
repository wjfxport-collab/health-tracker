# 🏃 HealthPulse — Secure Multi-User Weight & Activity Tracker

A fullstack health tracking platform with **Passkeys & Biometric authentication (Face ID / Touch ID)**, **automated Let's Encrypt SSL management**, **asynchronous Google Gemini Flash Vision scale parsing**, and **per-user data isolation**.

---

## 🌟 Key Features

- **👤 Multi-User Data Isolation**:
  - Secure user accounts with password hashing (PBKDF2-SHA256) & JWT session management.
  - Complete per-user data scoping: your entries, step history, trendlines, and goals remain private to your account.
- **🔑 WebAuthn Passkeys & Biometric Sign-In**:
  - One-touch sign-in using **Apple Face ID**, **Touch ID**, **Windows Hello**, or **Android Fingerprint**.
  - Register and manage multiple biometric devices directly from your account settings.
- **🔒 SSL & Automated Let's Encrypt Management**:
  - Automated 1-command Let's Encrypt certificate generation & auto-renewal cronjob (`./setup_ssl.sh --domain yourdomain.com`).
  - Auto-generated local SSL certificates for secure LAN & localhost HTTPS testing.
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

## 🔒 SSL & Let's Encrypt Automation

### Setup Let's Encrypt (Production Domain)
```bash
./setup_ssl.sh --domain yourdomain.com --email you@example.com
```
* Automatically requests certificate from Let's Encrypt via Certbot.
* Installs certificate files in `./certs/`.
* Configures an automatic 90-day renewal cronjob.

### Local Development / LAN Self-Signed SSL (for Biometric Testing)
```bash
./setup_ssl.sh --self-signed
```

---

## 🔑 Biometric Passkey Setup

1. Sign in or register an account with a username and password.
2. Click **"Settings" / Username** in the top navigation bar.
3. Under **"Biometric Passkeys"**, click **"Enroll Biometrics"** and scan your fingerprint or face.
4. On future sign-ins, simply tap **"Sign in with Touch ID / Face ID / Passkey"** for instant passwordless access!
