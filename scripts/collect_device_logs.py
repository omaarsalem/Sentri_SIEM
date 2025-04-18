import os
import time
import sqlite3
import csv
from datetime import datetime

# ✅ Define dynamic paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(BASE_DIR, "database", "sentri.db")
CSV_FILE = os.path.join(LOG_DIR, "device_logs.csv")

# ✅ Ensure required directories
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ✅ Ensure SQLite table exists
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            device_id TEXT,
            log_message TEXT
        )
    """)
    conn.commit()
    conn.close()
except Exception as e:
    print(f"[ERROR] Failed to ensure device_logs table: {e}")

# ✅ Ensure CSV header
if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
    with open(CSV_FILE, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "device_id", "log_message"])

def write_to_csv(log):
    try:
        with open(CSV_FILE, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([log["timestamp"], log["device_id"], log["log_message"]])
    except Exception as e:
        print(f"[ERROR] CSV write failed: {e}")

def write_to_sqlite(log):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO device_logs (timestamp, device_id, log_message)
            VALUES (?, ?, ?)
        """, (log["timestamp"], log["device_id"], log["log_message"]))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"[ERROR] SQLite insert failed: {e}")

def collect_logs():
    log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device_id": "DEVICE-001",
        "log_message": "Simulated log entry from device."
    }
    write_to_csv(log)
    write_to_sqlite(log)
    print(f"[INFO] Log written: {log}")

if __name__ == "__main__":
    print("🟢 Collecting device logs for 60 seconds...")
    start = time.time()
    while time.time() - start < 60:
        collect_logs()
        time.sleep(5)
    print("✅ Device log collection complete.")