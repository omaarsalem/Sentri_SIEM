# 🔒 SentriSIEM – Lightweight Security Information & Event Management System

SentriSIEM is a streamlined, open-source SIEM platform designed for small environments and academic use. It provides real-time log collection, alert generation, visual reporting, and anomaly detection — all deployable via Render and accessible through a custom domain.

---

## 🚀 Features

- 🔐 Secure user login with role-based access (Admin, Viewer)
- 📊 Real-time dashboard with:
  - Total logs
  - Active devices
  - Alert summaries
  - Frequency analysis (top IPs, events, processes)
- 📁 Export logs & anomalies to CSV
- 📈 Graphical visualizations (bar charts, pie charts)
- 🛠️ Built-in anomaly detection using Isolation Forest
- 🌐 Accessible via [https://sentrisiem.org](https://sentrisiem.org)

---

## 🧱 Architecture Overview

- **Frontend:** Flask (Jinja2 templates, HTML, CSS, Plotly)
- **Backend:** Python (Flask)
- **Database:** SQLite (`sentri.db`)
- **Log Sources:** Simulated or real (device logs, network logs, Windows exports)
- **Deployment:** Render + Cloudflare DNS
- **Security:** CSRF protection, session management, bcrypt password hashing

---

## 📂 Project Structure

```plaintext
SentriSIEM/
│
├── dashboard/
│   ├── app.py                # Flask app
│   ├── templates/            # HTML templates
│   └── static/               # CSS & chart assets
│
├── database/
│   ├── sentri.db             # SQLite database
│   └── create_admin.py       # Admin setup script
│
├── scripts/
│   ├── collect_device_logs.py
│   ├── capture_network_traffic.py
│   ├── real_time_detection.py
│   ├── log_analysis.py
│   ├── visualization.py
│   └── main.py               # Master runner
│
├── logs/                     # Simulated raw log output
├── collected_logs/          # Windows-exported logs (optional)
├── requirements.txt
└── README.md
