import os
import sqlite3
import pandas as pd
from datetime import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB = os.path.join(BASE, "dashboard", "database", "sentri.db")
THRESHOLD = 1000  # Total packet size in 1 min (adjust as needed)

def detect_spike():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT timestamp, packet_length FROM network_traffic", conn)
    conn.close()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["minute"] = df["timestamp"].dt.strftime('%Y-%m-%d %H:%M')
    grouped = df.groupby("minute")["packet_length"].sum()

    for minute, total in grouped.items():
        if total > THRESHOLD:
            print(f"[ALERT] ⚠️ Packet burst at {minute} → {total} bytes")

if __name__ == "__main__":
    print("[INFO] Checking for unusual packet bursts...")
    detect_spike()