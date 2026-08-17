# 🏃 HealthPulse — Fullstack Weight & Steps Tracker

A fullstack health tracking dashboard featuring **AI-powered scale photo parsing** (via Google Gemini 2.5 Flash Vision or Local Mac Gemma 4 12B Vision), automatic EXIF capture timestamp extraction, and interactive progress metrics.

---

## 🌟 Key Features

- **🧠 Multi-Engine Scale Photo OCR**:
  - 🌐 **Google Gemini 2.5 Flash Vision (Cloud)**: Reads 7-segment digital displays, aqua/blue screens, and glare-covered glass with human-grade accuracy.
  - 💻 **Local Mac Gemma 4 12B Vision (LAN Server `192.168.4.27`)**: 100% private local LLM vision inference running directly on your Mac.
  - ⚡ **Local Tesseract OCR (Offline)**: On-device image thresholding fallback.
- **🕒 Automatic EXIF Timestamp Extraction**: Reads photo capture date & time (`DateTimeOriginal`) directly from photo metadata.
- **📈 Interactive React Dashboard**:
  - Weight progression trendlines & goal markers.
  - 7-day and 30-day moving step averages.
  - Daily streak counters and goal progress bars.
- **📱 Remote & Mobile Friendly**: Accessible from desktop browsers and mobile devices over your local Wi-Fi.

---

## 🚀 Quick Start (Zero Config)

### Prerequisites
- **Python 3.9+**
- **Node.js 18+ & npm**

### 1. Clone & Run
```bash
# Clone the repository
git clone https://github.com/wjfxport-collab/health-tracker.git
cd health-tracker

# Run the app (auto-installs Python .venv and npm packages on first launch)
./run.sh
```

### 2. Open in Browser
- **Frontend Dashboard**: `http://localhost:5173`
- **Backend API**: `http://localhost:5000`

---

## 🛠️ Manual Installation (Optional)

If you prefer to install dependencies manually:

```bash
# 1. Setup Python Virtual Environment
python3 -m venv .venv
./.venv/bin/pip install -r backend/requirements.txt

# 2. Setup Node.js Frontend Dependencies
cd frontend
npm install
cd ..

# 3. Launch Servers
./run.sh
```

---

## ⚙️ AI Engine Configuration

Open **"Goals"** in the top navigation bar:
- **Google Gemini Vision**: Enter your Gemini API key (get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey)).
- **Local Mac Gemma 12B**: Set your server address (`http://192.168.4.27:11434` or custom port) and click **"Test Connection to Mac"**.
