import os
import sqlite3
import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard", "database", "sentri.db")
CONTAMINATION = 0.05

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

def load_logs():
    try:
        return pd.read_sql_query("SELECT id, timestamp, event_id, severity, message FROM logs", conn)
    except Exception as e:
        print(f"[LOAD ERROR] {e}")
        return pd.DataFrame()

def generate_message(event_id):
    return {
        4625: "❌ Brute-force login attempt.",
        4672: "⚠️ Privileged access used.",
        4688: "🛑 Suspicious process started."
    }.get(event_id, f"Anomaly detected - Event ID: {event_id}")

def run_anomaly_detection():
    df = load_logs()
    if df.empty: return
    try:
        model = IsolationForest(contamination=CONTAMINATION)
        df["anomaly"] = model.fit_predict(df[["event_id"]])
        anomalies = df[df["anomaly"] == -1]
        for _, row in anomalies.iterrows():
            conn.execute(
                "INSERT INTO anomalies (timestamp, event_id, severity, message) VALUES (?, ?, ?, ?)",
                (row["timestamp"], row["event_id"], row["severity"], generate_message(row["event_id"]))
            )
        conn.commit()
        print(f"✅ {len(anomalies)} anomalies saved.")
    except Exception as e:
        print(f"[ANALYSIS ERROR] {e}")

if __name__ == "__main__":
    print("🔎 Starting anomaly analysis...")
    run_anomaly_detection()
    print("✅ Done.")