import os
import sqlite3
import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import datetime

# ✅ Dynamic path to production database
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "database", "sentri.db")
CONTAMINATION = 0.05

# ✅ Ensure anomalies table exists
try:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_id INTEGER,
            severity TEXT,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()
except Exception as e:
    print(f"[ERROR] Failed to ensure anomalies table: {e}")

def generate_message(event_id):
    return {
        4625: "❌ Brute-force login attempt.",
        4672: "⚠️ Privileged access used.",
        4688: "🛑 Suspicious process started.",
        4768: "🔐 Kerberos authentication anomaly.",
        5145: "📁 Unauthorized file access attempt.",
        4697: "🕵️ Suspicious service installation.",
        7036: "🔁 Unexpected service state change."
    }.get(event_id, f"Anomaly detected - Event ID: {event_id}")

def load_logs():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query("SELECT id, timestamp, event_id, severity, message FROM logs", conn)
    except Exception as e:
        print(f"[LOAD ERROR] {e}")
        return pd.DataFrame()

def run_anomaly_detection():
    df = load_logs()
    if df.empty:
        print("⚠️ No logs available.")
        return

    try:
        model = IsolationForest(contamination=CONTAMINATION, random_state=42)
        df["anomaly"] = model.fit_predict(df[["event_id"]])
        anomalies = df[df["anomaly"] == -1]

        if anomalies.empty:
            print("✅ No new anomalies found.")
            return

        with sqlite3.connect(DB_PATH) as conn:
            for _, row in anomalies.iterrows():
                conn.execute(
                    "INSERT INTO anomalies (timestamp, event_id, severity, message) VALUES (?, ?, ?, ?)",
                    (
                        row["timestamp"],
                        row["event_id"],
                        row["severity"],
                        generate_message(row["event_id"])
                    )
                )
            conn.commit()
        print(f"✅ {len(anomalies)} anomalies saved to database.")
    except Exception as e:
        print(f"[ANALYSIS ERROR] {e}")

# 🔍 Run if executed directly
if __name__ == "__main__":
    print("🔎 Starting anomaly analysis...")
    run_anomaly_detection()
    print("✅ Done.")