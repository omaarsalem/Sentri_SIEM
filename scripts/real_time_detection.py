import os
import time
import sqlite3
import random
from collections import defaultdict
from datetime import datetime

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(BASE_DIR, "dashboard", "database", "sentri.db")
LOG_FILE = os.path.join(LOG_DIR, "real_time_detection.log")

# Ensure folders
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Ensure log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("Real-time detection started.\n")

def log_message(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    entry = f"[{timestamp}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")
    print(entry)

# Frequency tracking
frequency_tracker = defaultdict(int)
FREQUENCY_THRESHOLD = 10
COLLECTION_TIME = 60  # seconds

def generate_dynamic_logs():
    sample_logs = [
        {"EventID": "4625", "Source": "Security", "Severity": "High", "Message": "Failed login attempt"},
        {"EventID": "4672", "Source": "Security", "Severity": "Medium", "Message": "Privileged access granted"},
        {"EventID": "4688", "Source": "Process", "Severity": "High", "Message": "Suspicious process started"},
        {"EventID": "5145", "Source": "FileAudit", "Severity": "Low", "Message": "Unauthorized file access attempt"},
        {"EventID": "7036", "Source": "Service", "Severity": "Info", "Message": "Service state changed"}
    ]
    return [random.choice(sample_logs)]

def process_log_entry(log):
    try:
        event_id = log.get("EventID", "Unknown")
        source = log.get("Source", "Unknown")
        severity = log.get("Severity", "Info")
        message = log.get("Message", "No message")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"→ Inserting: {timestamp}, {event_id}, {severity}, {source}, {message}")

        with sqlite3.connect(DB_PATH) as conn:
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
            cursor.execute("""
                INSERT INTO logs (timestamp, event_id, severity, source, message)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, event_id, severity, source, message))
            conn.commit()

        frequency_tracker[event_id] += 1
        if frequency_tracker[event_id] > FREQUENCY_THRESHOLD:
            log_message(f"[ALERT] High frequency detected: Event ID {event_id}")

    except Exception as e:
        log_message(f"[ERROR] Failed to process log: {e}")

def monitor_logs():
    log_message("🔍 Starting real-time detection scan")
    start = time.time()
    while time.time() - start < COLLECTION_TIME:
        logs = generate_dynamic_logs()
        for entry in logs:
            process_log_entry(entry)
        time.sleep(5)
    log_message("✅ Real-time detection finished.")

# Entry point
if __name__ == "__main__":
    monitor_logs()
