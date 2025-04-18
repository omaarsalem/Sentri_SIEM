import sqlite3
import os
from datetime import datetime

# ✅ Path to the shared SQLite DB
DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "sentri.db")

def insert_alert(source, alert_type, description, severity):
    """Insert an alert into the alerts table."""
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
    print(f"🚨 Alert logged: {alert_type} | Severity: {severity} | Source: {source}")

def run_playbooks():
    """Basic SOAR playbooks on latest log entries."""
    conn = sqlite3.connect(DB)
    logs = conn.execute(
        "SELECT event_id, source, message FROM logs ORDER BY timestamp DESC LIMIT 50"
    ).fetchall()
    conn.close()

    for log in logs:
        try:
            event_id = int(log[0])
            source = log[1]
            message = log[2]

            if event_id == 4625:
                insert_alert(source, "Brute Force Attempt", message, "High")
            elif event_id == 4688:
                insert_alert(source, "Suspicious Process Execution", message, "Medium")
            elif event_id == 1102:
                insert_alert(source, "Audit Log Cleared", message, "High")
            elif event_id == 4672:
                insert_alert(source, "Privileged Access Detected", message, "Medium")
        except Exception as e:
            print(f"[ERROR] Failed to process log entry: {e}")

if __name__ == "__main__":
    print("🧠 Running SOAR playbooks...")
    run_playbooks()
    print("✅ SOAR processing complete.")