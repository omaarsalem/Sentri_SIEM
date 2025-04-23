import subprocess
import sys
import os
import time

# Base project path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
LOG_FILE = os.path.join(BASE_DIR, "dashboard", "startup_log.txt")

# Scripts to run in sequence
scripts = [
    "collect_device_logs.py",
    "capture_network_traffic.py",
    "real_time_detection.py",
    "soar_rules.py",
    "log_analysis.py",
    "visualization.py"
]

def log_to_file(msg):
    """Append output to startup log file."""
    with open(LOG_FILE, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

def run_script_with_timeout(script_name, timeout=60):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        log_to_file(f"❌ Script not found: {script_path}")
        return

    log_to_file(f"🚀 Running {script_name} (timeout {timeout}s)...")
    try:
        proc = subprocess.Popen([sys.executable, script_path])
        start = time.time()
        while proc.poll() is None:
            if time.time() - start > timeout:
                proc.terminate()
                log_to_file(f"⏱️ Timeout reached for {script_name}. Terminated.")
                return
            time.sleep(1)
        log_to_file(f"✅ Finished {script_name}")
    except Exception as e:
        log_to_file(f"❌ Error running {script_name}: {e}")

if __name__ == "__main__":
    log_to_file("🚀 Launching SentriSIEM full pipeline (with time limits)...")
    for script in scripts:
        run_script_with_timeout(script, timeout=60)
    log_to_file("✅ Pipeline complete.\n")