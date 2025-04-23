import os
import csv

# === Base Paths ===
BASE_DIR = r"C:\Users\omaar\Desktop\SentriSIEM"
LOG_DIR = os.path.join(BASE_DIR, "logs")
RAW_LOG_FILE = os.path.join(LOG_DIR, "firewall.log")
PARSED_CSV_FILE = os.path.join(LOG_DIR, "parsed_firewall_logs.csv")

# === Ensure directories and files exist ===
os.makedirs(LOG_DIR, exist_ok=True)

if not os.path.exists(RAW_LOG_FILE):
    print(f"⚠️ No firewall logs found. Creating empty log: {RAW_LOG_FILE}")
    open(RAW_LOG_FILE, "w").close()

def parse_firewall_logs():
    """
    Parses simulated firewall logs and saves parsed output to CSV format.
    Expected format: 'DATE - ACTION - SRC - DST - PROTOCOL'
    """
    if os.stat(RAW_LOG_FILE).st_size == 0:
        print("⚠️ Warning: Firewall log file is empty!")
        return

    try:
        with open(RAW_LOG_FILE, "r", encoding="utf-8") as infile, open(PARSED_CSV_FILE, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(["date", "action", "source", "destination", "protocol"])

            print("📄 Reading firewall logs...")
            for line in infile:
                print(f"🔍 Raw: {line.strip()}")
                parts = line.strip().split(" - ")
                if len(parts) == 5:
                    writer.writerow(parts)
                    print(f"✅ Parsed: {parts}")
                else:
                    print(f"❌ Skipping malformed line: {line.strip()}")

        print(f"📦 Parsed CSV saved to: {PARSED_CSV_FILE}")

    except Exception as e:
        print(f"❌ Error while parsing logs: {e}")

if __name__ == "__main__":
    print("🚀 Starting firewall log parser...")
    parse_firewall_logs()