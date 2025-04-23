import os
import requests
import sqlite3
from datetime import datetime

API_ENDPOINT = "https://sentrisiem-q0j6.onrender.com/api/logs"  # Replace with your actual dashboard URL
API_KEY = os.getenv("SENTRI_API_KEY", "default_api_key")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "dashboard", "database", "sentri.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    event_id TEXT,
    severity TEXT,
    source TEXT,
    message TEXT
)
""")
conn.commit()
def get_latest_logs(limit=10):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, event_id, severity, message, source FROM logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[ERROR] Fetching logs failed: {e}")
        return []

def push_log(log):
    payload = {
        "timestamp": log[0],
        "event_id": log[1],
        "severity": log[2],
        "message": log[3],
        "source": log[4]
    }
    try:
        response = requests.post(API_ENDPOINT, json=payload, headers={"X-API-KEY": API_KEY})
        if response.status_code == 200:
            print(f"[PUSHED] {log}")
        else:
            print(f"[FAILED] {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERROR] API push failed: {e}")

if __name__ == "__main__":
    print("🚀 Pushing latest logs to Render...")
    logs = get_latest_logs()
    for log in logs:
        push_log(log)
