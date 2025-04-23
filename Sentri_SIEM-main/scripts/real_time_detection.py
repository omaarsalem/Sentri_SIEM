import sqlite3
import json
import time
import os
import chardet
import re
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

log_files = [
    os.path.join(BASE_DIR, "logs", "sentrisem_logs.json"),
    os.path.join(BASE_DIR, "collected_logs", "exported_logs.txt")
]

# Use the shared database path (adjusted correctly for both local and Render)
db_path = os.getenv("SENTRI_DB_PATH", os.path.join(BASE_DIR, "database", "sentri.db"))

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
except sqlite3.OperationalError as e:
    print(f"❌ Database connection error: {e}")
    exit(1)

# Ensure logs table exists
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

# Frequency Alert Tracking
frequency_tracker = defaultdict(int)
FREQUENCY_THRESHOLD = 10
COLLECTION_TIME = 60  # seconds

def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        result = chardet.detect(f.read(10000))
    return result['encoding']

def read_logs_from_json(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return []

    try:
        encoding = detect_encoding(file_path)
        with open(file_path, "r", encoding=encoding, errors="ignore") as log_file:
            raw_content = log_file.read().strip()
            if not raw_content:
                print(f"⚠️ Empty JSON log: {file_path}")
                return []
            return json.loads(raw_content)
    except Exception as e:
        print(f"❌ JSON parse error in {file_path}: {e}")
        return []

def parse_exported_logs(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return []

    logs = []
    try:
        encoding = detect_encoding(file_path)
        with open(file_path, "r", encoding=encoding, errors="ignore") as log_file:
            for line in log_file:
                line = line.strip()
                if not line or "Index" in line or "Time" in line:
                    continue
                match = re.match(r'(\d+)\s+(\w+\s+\d+\s+\d+:\d+)\s+(\w+)\s+([\w-]+)\s+(\d+)\s+(.+)', line)
                if match:
                    logs.append({
                        "EventID": match.group(5),
                        "Timestamp": match.group(2),
                        "Severity": match.group(3),
                        "Source": match.group(4),
                        "Message": match.group(6),
                    })
        return logs
    except Exception as e:
        print(f"❌ Error parsing exported logs: {e}")
        return []

def process_log_entry(log_entry):
    try:
        event_id = log_entry.get("EventID", "Unknown")
        source = log_entry.get("Source", "Unknown")
        severity = log_entry.get("Severity", "Info")
        message = log_entry.get("Message", "No message")
        timestamp = log_entry.get("Timestamp", time.strftime('%Y-%m-%d %H:%M:%S'))

        cursor.execute("""
            INSERT INTO logs (timestamp, event_id, severity, source, message)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, event_id, severity, source, message))
        conn.commit()

        frequency_tracker[event_id] += 1
        if frequency_tracker[event_id] > FREQUENCY_THRESHOLD:
            print(f"⚠️ ALERT: High frequency detected for EventID {event_id}")
    except Exception as e:
        print(f"❌ Error inserting log: {e}")

def monitor_logs():
    start = time.time()
    while time.time() - start < COLLECTION_TIME:
        for log_file in log_files:
            print(f"🔍 Scanning: {log_file}")
            logs = parse_exported_logs(log_file) if "exported_logs.txt" in log_file else read_logs_from_json(log_file)
            if logs:
                for entry in logs:
                    process_log_entry(entry)
            else:
                print(f"⚠️ No usable logs in {log_file}")
        time.sleep(5)
    print("✅ Real-time detection finished.")

if __name__ == "__main__":
    monitor_logs()
