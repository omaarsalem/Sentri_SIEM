import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB = os.path.join(BASE, "dashboard", "database", "sentri.db")
OUT = os.path.join(BASE, "dashboard", "static", "visualizations")
os.makedirs(OUT, exist_ok=True)

def generate_top_talkers_chart():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT source_ip, COUNT(*) as count FROM network_traffic GROUP BY source_ip ORDER BY count DESC LIMIT 10", conn)
    conn.close()

    if df.empty:
        print("[INFO] No data for top talkers.")
        return

    df.plot(kind="bar", x="source_ip", y="count", legend=False, color="#ff4d4d")
    plt.title("Top Talkers (By IP)")
    plt.xlabel("Source IP")
    plt.ylabel("Packets")
    plt.tight_layout()
    path = os.path.join(OUT, "top_talkers.png")
    plt.savefig(path)
    plt.close()
    print(f"[SAVED] {path}")

def generate_protocol_pie_chart():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT protocol, COUNT(*) as count FROM network_traffic GROUP BY protocol", conn)
    conn.close()

    if df.empty:
        print("[INFO] No data for protocol distribution.")
        return

    df.set_index("protocol", inplace=True)
    df.plot(kind="pie", y="count", autopct='%1.1f%%', legend=False)
    plt.title("Protocol Distribution")
    plt.ylabel("")
    plt.tight_layout()
    path = os.path.join(OUT, "protocol_distribution.png")
    plt.savefig(path)
    plt.close()
    print(f"[SAVED] {path}")

def generate_bandwidth_chart():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT timestamp, packet_length FROM network_traffic", conn)
    conn.close()

    if df.empty:
        print("[INFO] No bandwidth data.")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["minute"] = df["timestamp"].dt.strftime('%Y-%m-%d %H:%M')
    grouped = df.groupby("minute")["packet_length"].sum()

    grouped.plot(kind="line", marker="o", color="cyan")
    plt.title("Bandwidth Usage Over Time")
    plt.xlabel("Minute")
    plt.ylabel("Total Bytes")
    plt.xticks(rotation=45)
    plt.tight_layout()
    path = os.path.join(OUT, "bandwidth_over_time.png")
    plt.savefig(path)
    plt.close()
    print(f"[SAVED] {path}")

if __name__ == "__main__":
    print("[INFO] Generating network visualizations...")
    generate_top_talkers_chart()
    generate_protocol_pie_chart()
    generate_bandwidth_chart()
    print("[INFO] Done.")