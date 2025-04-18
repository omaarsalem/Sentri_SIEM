import os
import json
import sqlite3
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "dashboard", "database", "sentri.db")

LOG_PATHS = [
    os.path.join(BASE_DIR, "logs", "sentrisem_logs.json"),
    os.path.join(BASE_DIR, "collected_logs", "exported_logs.txt")
]

conn = sqlite3.connect(DB_PATH)
conn.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    source TEXT,
    event_id TEXT,
    severity TEXT,
    message TEXT
)
""")
conn.commit()

def process_entry(entry):
    try:
        timestamp = entry.get("Timestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        conn.execute("""
            INSERT INTO logs (timestamp, event_id, severity, source, message)
            VALUES (?, ?, ?, ?, ?)
        """, (
            timestamp,
            entry.get("EventID", "Unknown"),
            entry.get("Severity", "Info"),
            entry.get("Source", "Unknown"),
            entry.get("Message", "No message")
        ))
        conn.commit()
        print(f"[+] Processed: {entry}")
    except Exception as e:
        print(f"[!] Failed: {e}")

def monitor_logs():
    for path in LOG_PATHS:
        if not os.path.exists(path): continue
        try:
            with open(path, "r") as f:
                content = f.read()
                if path.endswith(".json"):
                    entries = json.loads(content)
                else:
                    entries = [{"EventID": "1001", "Severity": "Info", "Source": "Winlog", "Message": line.strip(), "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for line in content.splitlines() if line.strip()]
                for entry in entries:
                    process_entry(entry)
        except Exception as e:
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    print("⚡ Running real-time log detection for 60 seconds...")
    start = time.time()
    while time.time() - start < 60:
        monitor_logs()
        time.sleep(5)
    print("✅ Detection done.")