import subprocess
import sys
import os
import time
import sqlite3
import io

# Ensure UTF-8 output (Windows fix)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Base paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
DB_PATH = os.path.join(BASE_DIR, "database", "sentri.db")
LOG_FILE = os.path.join(BASE_DIR, "dashboard", "startup_log.txt")

# Ordered scripts and whether to skip them (True = skip)
scripts = {
    "collect_device_logs.py": False,
    "capture_network_traffic.py": False,
    "real_time_detection.py": False,
    "soar_rules.py": False,
    "log_analysis.py": False,
    "visualization.py": False
}

# Ensure log file directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Ensure script_logs table
def ensure_logs_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS script_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_name TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] Failed to ensure script_logs table: {e}")

def log_to_file(msg):
    """Append to startup log file."""
    entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
        print(msg)
    except Exception as e:
        print(f"[LOG ERROR] {e}")

def log_to_db(script_name, status, message=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO script_logs (script_name, status, message) VALUES (?, ?, ?)",
            (script_name, status, message)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log_to_file(f"[DB ERROR] Failed to log {script_name}: {e}")

def run_script_with_timeout(script_name, timeout=60):
    if scripts[script_name]:
        log_to_file(f"⏭️ Skipped {script_name}")
        log_to_db(script_name, "skipped", "Marked as skipped.")
        return

    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        log_to_file(f"❌ Script not found: {script_path}")
        log_to_db(script_name, "error", "Script not found")
        return

    log_to_file(f"🚀 Running {script_name} (timeout {timeout}s)...")
    try:
        start = time.time()
        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        while proc.poll() is None:
            if time.time() - start > timeout:
                proc.terminate()
                log_to_file(f"⏱️ Timeout reached for {script_name}. Terminated.")
                log_to_db(script_name, "timeout")
                return
            time.sleep(1)

        stdout, stderr = proc.communicate()
        if stdout.strip():
            log_to_file(f"[OUTPUT] {stdout.strip()}")
        if stderr.strip():
            log_to_file(f"[ERROR] {stderr.strip()}")

        log_to_file(f"✅ Finished {script_name}")
        log_to_db(script_name, "success", stdout.strip())
    except Exception as e:
        log_to_file(f"❌ Error in {script_name}: {e}")
        log_to_db(script_name, "error", str(e))

if __name__ == "__main__":
    ensure_logs_table()
    log_to_file("🚀 Launching SentriSIEM full pipeline (with time limits)...")
    start_time = time.time()

    for script in scripts:
        run_script_with_timeout(script, timeout=60)

    duration = round(time.time() - start_time, 2)
    log_to_file(f"✅ Pipeline complete in {duration}s.\n")