import sqlite3
import os
from datetime import datetime

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard", "database", "sentri.db")

def insert_alert(source, alert_type, description, severity):
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        source TEXT,
        alert_type TEXT,
        description TEXT,
        severity TEXT
    )
    """)
    conn.execute(
        "INSERT INTO alerts (timestamp, source, alert_type, description, severity) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), source, alert_type, description, severity)
    )
    conn.commit()
    conn.close()
    print(f"🚨 Alert: {alert_type} ({severity}) logged.")

def run_playbooks():
    conn = sqlite3.connect(DB)
    logs = conn.execute("SELECT event_id, source, message FROM logs ORDER BY timestamp DESC LIMIT 50").fetchall()
    conn.close()

    for log in logs:
        event_id = int(log[0])
        if event_id == 4625:
            insert_alert(log[1], "Brute Force Attempt", log[2], "High")
        elif event_id == 4688:
            insert_alert(log[1], "Suspicious Process", log[2], "Medium")

if __name__ == "__main__":
    print("🧠 Running SOAR playbooks...")
    run_playbooks()
    print("✅ SOAR processing complete.")