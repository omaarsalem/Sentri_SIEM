import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# ✅ Base path and output directory
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "database", "sentri.db")
OUT = os.path.join(BASE, "dashboard", "static", "visualizations")
os.makedirs(OUT, exist_ok=True)

def failed_logins_chart():
    """Generate bar chart of failed login events (Event ID 4625)."""
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT timestamp FROM logs WHERE event_id = 4625", conn)
    conn.close()

    if df.empty:
        print("⚠️ No failed login logs found.")
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
    print(f"✅ Saved: {output_path}")

def severity_pie_chart():
    """Generate pie chart of log severity distribution."""
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT severity FROM logs", conn)
    conn.close()

    if df.empty:
        print("⚠️ No severity logs found.")
        return

    counts = df["severity"].value_counts()

    plt.figure(figsize=(6, 6))
    counts.plot(kind="pie", autopct='%1.1f%%', colors=['red', 'orange', 'green'])
    plt.title("Log Severity Distribution")
    plt.ylabel("")  # Removes y-axis label
    plt.tight_layout()
    output_path = os.path.join(OUT, "severity_pie_chart.png")
    plt.savefig(output_path)
    plt.close()
    print(f"✅ Saved: {output_path}")

if __name__ == "__main__":
    print("📊 Generating visualizations...")
    failed_logins_chart()
    severity_pie_chart()
    print("✅ All visualizations completed.")