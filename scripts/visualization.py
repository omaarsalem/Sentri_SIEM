import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Base path and output directory
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "dashboard", "database", "sentri.db")
OUT = os.path.join(BASE, "dashboard", "static", "visualizations")
os.makedirs(OUT, exist_ok=True)

def failed_logins_chart():
    """Generate bar chart of failed login events (Event ID 4625)."""
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT timestamp FROM logs WHERE event_id = 4625", conn)
    conn.close()

    if df.empty:
        print("[INFO] No failed login logs found.")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.strftime('%Y-%m-%d %H:00')
    counts = df.groupby("hour").size()

    plt.figure(figsize=(10, 5))
    counts.plot(kind="bar", color="red")
    plt.title("Failed Logins (Event ID 4625)")
    plt.xlabel("Hour")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    output_path = os.path.join(OUT, "failed_logins_heatmap.png")
    plt.savefig(output_path)
    plt.close()
    print(f"[SAVED] {output_path}")

def severity_pie_chart():
    """Generate pie chart of log severity distribution."""
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT severity FROM logs", conn)
    conn.close()

    if df.empty:
        print("[INFO] No severity data found.")
        return

    counts = df["severity"].value_counts()

    plt.figure(figsize=(6, 6))
    counts.plot(kind="pie", autopct='%1.1f%%', colors=['red', 'orange', 'green', 'blue', 'grey'])
    plt.title("Log Severity Distribution")
    plt.ylabel("")
    plt.tight_layout()
    output_path = os.path.join(OUT, "severity_pie_chart.png")
    plt.savefig(output_path)
    plt.close()
    print(f"[SAVED] {output_path}")

def top_anomalies_by_severity_chart():
    """Generate bar chart of top anomalies by severity."""
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT severity FROM anomalies", conn)
    conn.close()

    if df.empty:
        print("[INFO] No anomaly data found.")
        return

    counts = df["severity"].value_counts()

    plt.figure(figsize=(8, 4))
    counts.plot(kind="bar", color='purple')
    plt.title("Top Anomalies by Severity")
    plt.xlabel("Severity Level")
    plt.ylabel("Count")
    plt.tight_layout()
    output_path = os.path.join(OUT, "anomaly_severity_chart.png")
    plt.savefig(output_path)
    plt.close()
    print(f"[SAVED] {output_path}")

def export_anomalies_csv():
    """Export all anomalies to CSV."""
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM anomalies", conn)
    conn.close()

    if df.empty:
        print("[INFO] No anomalies to export.")
        return

    csv_path = os.path.join(OUT, "anomalies_export.csv")
    df.to_csv(csv_path, index=False)
    print(f"[EXPORTED] {csv_path}")

if __name__ == "__main__":
    print("[INFO] Generating visualizations and exporting anomalies...")
    failed_logins_chart()
    severity_pie_chart()
    top_anomalies_by_severity_chart()
    export_anomalies_csv()
    print("[INFO] All tasks completed.")
