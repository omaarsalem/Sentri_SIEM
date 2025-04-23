import os
import sqlite3
from datetime import datetime
from scapy.all import sniff
from scapy.layers.inet import IP

# Path Setup
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "dashboard", "database", "sentri.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Ensure DB table exists
def setup_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
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

def save_packet(packet):
    try:
        if not packet.haslayer(IP):
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        src = packet[IP].src
        dst = packet[IP].dst
        proto = packet.proto if hasattr(packet, "proto") else "Unknown"
        length = len(packet)

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO network_traffic (timestamp, source_ip, destination_ip, protocol, packet_length)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, src, dst, proto, length))
            conn.commit()
        print(f"[CAPTURED] {timestamp} | {src} → {dst} | {proto} | {length} bytes")

    except Exception as e:
        print(f"[ERROR] Failed to save packet: {e}")

def main():
    setup_db()
    print("🔍 Starting real network traffic capture... (Press Ctrl+C to stop)")
    try:
        sniff(prn=save_packet, filter="ip", store=False, timeout=60)
        print("✅ Capture complete.")
    except KeyboardInterrupt:
        print("⛔ Capture stopped manually.")

if __name__ == "__main__":
    main()