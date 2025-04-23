import os
import sqlite3
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import numpy as np
from scipy.sparse import csr_matrix
# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "dashboard", "database", "sentri.db")
CONTAMINATION = 0.2

# Ensure anomalies table exists
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS anomalies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        event_id TEXT,
        severity TEXT,
        message TEXT
    )
""")
conn.commit()
cursor.close()

# Severity mapping
SEVERITY_MAP = {
    "Info": 0,
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4
}

def generate_message(event_id):
    return {
        "4625": "Brute-force login attempt.",
        "4672": "Privileged access used.",
        "4688": "Suspicious process started.",
        "4768": "Kerberos authentication anomaly.",
        "5145": "Unauthorized file access attempt.",
        "4697": "Suspicious service installation.",
        "7036": "Unexpected service state change.",
        "1102": "Audit log cleared."
    }.get(str(event_id), f"Anomaly detected - Event ID: {event_id}")

def load_logs():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query("SELECT timestamp, event_id, severity, message FROM logs", conn)
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to load logs: {e}")
        return pd.DataFrame()

def run_anomaly_detection():
    df = load_logs()
    if df.empty:
        print("[INFO] No logs available in logs table.")
        return

    print(f"[INFO] Analyzing {len(df)} log entries...")

    try:
        # Clean and encode
        df["event_id"] = pd.to_numeric(df["event_id"], errors="coerce")
        df["severity_num"] = df["severity"].map(SEVERITY_MAP).fillna(0)
        df.dropna(subset=["event_id"], inplace=True)

        if len(df) < 20:
            print("[INFO] Not enough varied logs to perform anomaly detection (need >20 valid rows).")
            return

        # TF-IDF on message
        tfidf = TfidfVectorizer(max_features=25)
        tfidf_matrix = tfidf.fit_transform(df["message"])

        # Combine all features
        features = np.column_stack((
            df["event_id"].to_numpy(),
            df["severity_num"].to_numpy(),
            tfidf_matrix.toarray() # type: ignore
        ))
        features = StandardScaler().fit_transform(features)

        # Anomaly detection
        model = IsolationForest(contamination=CONTAMINATION, random_state=42)
        df["anomaly"] = model.fit_predict(features)
        anomalies = df[df["anomaly"] == -1]

        if anomalies.empty:
            print("[INFO] No anomalies detected.")
            return

        print("\n[DETECTED] Anomalies preview:")
        print(anomalies[["timestamp", "event_id", "severity", "message"]])

        # Insert into anomalies table
        with sqlite3.connect(DB_PATH) as conn:
            for _, row in anomalies.iterrows():
                conn.execute(
                    """
                    INSERT INTO anomalies (timestamp, event_id, severity, message)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        row["timestamp"],
                        str(int(row["event_id"])),
                        row["severity"],
                        generate_message(row["event_id"])
                    )
                )
            conn.commit()
        print(f"[INFO] {len(anomalies)} anomalies saved to database.")

    except Exception as e:
        print(f"[ANALYSIS ERROR] {e}")

if __name__ == "__main__":
    print("[INFO] Starting anomaly analysis...")
    run_anomaly_detection()
    print("[INFO] Done.")