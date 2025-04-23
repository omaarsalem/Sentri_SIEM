import sqlite3
import os

# 🔧 Absolute path to ensure correctness
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "dashboard", "database", "sentri.db")

def reset_alerts_table():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)  # Ensure folders exist
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS alerts")
            cursor.execute("""
                CREATE TABLE alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    source TEXT,
                    alert_type TEXT,
                    description TEXT,
                    severity TEXT
                )
            """)
            conn.commit()
        print("✅ Alerts table has been reset successfully.")
    except Exception as e:
        print(f"❌ Failed to reset alerts table: {e}")

if __name__ == "__main__":
    reset_alerts_table()