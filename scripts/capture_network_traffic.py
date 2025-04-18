import os
import time
import sqlite3
import csv
from datetime import datetime

# ✅ Resolve paths correctly
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "database", "sentri.db")
LOG_DIR = os.path.join(BASE_DIR, "logs")
CSV_FILE = os.path.join(LOG_DIR, "network_traffic.csv")

# ✅ Ensure directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# ✅ Ensure database table
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS network_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source_ip TEXT,
            destination_ip TEXT,
            protocol TEXT,
            packet_length INTEGER
        )
    """)
    conn.commit()
    conn.close()
except Exception as e:
    print(f"[ERROR] Failed to create table: {e}")

def log_traffic():
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source_ip": "192.168.1.1",
        "destination_ip": "192.168.1.100",
        "protocol": "TCP",
        "packet_length": 512
    }

    # ✅ Write to CSV
    try:
        write_header = not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(entry.keys())
            writer.writerow(entry.values())
    except Exception as e:
        print(f"[ERROR] Failed to write to CSV: {e}")

    # ✅ Write to SQLite
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO network_traffic (timestamp, source_ip, destination_ip, protocol, packet_length)
            VALUES (?, ?, ?, ?, ?)
        """, tuple(entry.values()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] SQLite insert failed: {e}")

    print(f"[INFO] Captured Traffic: {entry}")

# ✅ Timed run
if __name__ == "__main__":
    print("🟢 Capturing network traffic for 60 seconds...")
    start = time.time()
    while time.time() - start < 60:
        log_traffic()
        time.sleep(5)
    print("✅ Network traffic capture complete.")