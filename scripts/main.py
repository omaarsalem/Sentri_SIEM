import subprocess
import sys
import os
import time

# === Directories ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

# === Scripts in order ===
scripts = [
    "collect_device_logs.py",
    "capture_network_traffic.py",
    "real_time_detection.py",
    "soar_rules.py",
    "log_analysis.py",
    "visualization.py"
]

def run_script(script_name, timeout=60):
    path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(path):
        print(f"❌ Script not found: {path}")
        return
    print(f"🚀 Running {script_name} (timeout {timeout}s)...")
    process = subprocess.Popen([sys.executable, path])
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout reached for {script_name}. Terminating...")
        process.terminate()

if __name__ == "__main__":
    print("🚀 Launching SentriSIEM full pipeline (with time limits)...")
    start = time.time()
    for script in scripts:
        run_script(script, timeout=60)
    print(f"✅ Pipeline complete in {round(time.time() - start, 1)} seconds.")