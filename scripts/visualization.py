import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "dashboard", "database", "sentri.db")
OUT = os.path.join(BASE, "dashboard", "static", "visualizations")
os.makedirs(OUT, exist_ok=True)

def failed_logins_chart():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT timestamp FROM logs WHERE event_id = 4625", conn)
    conn.close()
    if df.empty: return
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.strftime('%Y-%m-%d %H:00')
    counts = df.groupby("hour").size()

    plt.figure(figsize=(10, 5))
    counts.plot(kind="bar", color="red")
    plt.title("Failed Logins (Event ID 4625)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "failed_logins_heatmap.png"))
    plt.close()

def severity_pie_chart():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT severity FROM logs", conn)
    conn.close()
    if df.empty: return
    counts = df["severity"].value_counts()

    plt.figure(figsize=(6, 6))
    counts.plot(kind="pie", autopct='%1.1f%%', colors=['red', 'orange', 'green'])
    plt.title("Log Severity Distribution")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "severity_pie_chart.png"))
    plt.close()

if __name__ == "__main__":
    print("📊 Creating charts...")
    failed_logins_chart()
    severity_pie_chart()
    print("✅ Visualizations saved.")