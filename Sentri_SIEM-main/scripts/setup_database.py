import os
import sqlite3

# ✅ Unified Database Path
BASE_DIR = r"C:\Users\omaar\Desktop\SentriSIEM\database"
DB_FILE = os.path.join(BASE_DIR, "sentri.db")

# Ensure database directory exists
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

def setup_database():
    """
    Creates the SentriSIEM database and necessary tables.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # ✅ Users table (for authentication)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

        # ✅ Logs table (used throughout)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                source_ip TEXT,
                process_name TEXT
            )
        """)

        # ✅ Anomalies table (for detection reporting)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_id INTEGER,
                severity TEXT,
                message TEXT
            )
        """)

        # ✅ Device logs table (for collect_device_logs.py)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                device_id TEXT,
                log_message TEXT
            )
        """)

        # ✅ Alerts (optional for future use)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL
            )
        """)

        conn.commit()
        print(f"✅ Database setup completed at {DB_FILE}")

    except Exception as e:
        print(f"❌ Error setting up the database: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Setting up the database...")
    setup_database()