import os
import sqlite3
import csv

# Base directory
BASE_DIR = r"C:\Users\omaar\Desktop\SentriSIEM"
DB_FILE = os.path.join(BASE_DIR, "sentri.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "anomaly_data.csv")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def prepare_data():
    """
    Extract logs from the database and export to CSV for anomaly detection.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT timestamp, event_id, severity, message FROM logs")
        logs = cursor.fetchall()

        with open(OUTPUT_FILE, "w", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "event_id", "severity", "message"])  # Header
            for row in logs:
                writer.writerow(row)

        print(f"✅ Anomaly data exported to {OUTPUT_FILE}")
        conn.close()

    except Exception as e:
        print(f"❌ Error preparing anomaly data: {e}")

if __name__ == "__main__":
    prepare_data()