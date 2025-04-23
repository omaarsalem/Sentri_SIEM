import sqlite3
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# Path to the shared SQLite DB
DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard", "database", "sentri.db")

# Email Settings
EMAIL_USER = "info@sentrisiem.org"
EMAIL_PASS = "Sentri@Siem@135"
SMTP_SERVER = "smtp.hostinger.com"
SMTP_PORT = 465

def send_email_alert(subject, body, severity):
    try:
        msg = MIMEMultipart()
        msg['From'] = formataddr(("SentriSIEM Alerts", EMAIL_USER))
        msg['To'] = EMAIL_USER
        msg['Subject'] = f"[{severity.upper()}] {subject}"

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            if not EMAIL_PASS:
                raise ValueError("EMAIL_PASS environment variable is not set.")
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            print(f"[EMAIL] Sent: {subject}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send: {e}")

def ensure_alerts_table():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source TEXT,
            alert_type TEXT,
            description TEXT,
            severity TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_alert(source, alert_type, description, severity):
    try:
        conn = sqlite3.connect(DB)
        conn.execute("""
            INSERT INTO alerts (timestamp, source, alert_type, description, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            source,
            alert_type,
            description,
            severity
        ))
        conn.commit()
        conn.close()
        print(f"[ALERT] {alert_type} | Severity: {severity} | Source: {source}")

        # Send email for high/critical severity alerts
        if severity.lower() in ["high", "critical"]:
            send_email_alert(alert_type, f"{description}\nSource: {source}", severity)

    except Exception as e:
        print(f"[SOAR ERROR] Failed processing alert: {e}")

def run_playbooks():
    conn = sqlite3.connect(DB)
    logs = conn.execute("SELECT event_id, source, message FROM logs ORDER BY timestamp DESC LIMIT 50").fetchall()
    conn.close()

    for log in logs:
        try:
            event_id = int(log[0])
            source = log[1]
            message = log[2]

            if event_id == 4625:
                insert_alert(source, "Brute Force Attempt", message, "High")
            elif event_id == 4688:
                insert_alert(source, "Suspicious Process Execution", message, "Medium")
            elif event_id == 1102:
                insert_alert(source, "Audit Log Cleared", message, "High")
            elif event_id == 4672:
                insert_alert(source, "Privileged Access Detected", message, "Medium")
        except Exception as e:
            print(f"[SOAR ERROR] Failed processing log: {e}")

if __name__ == "__main__":
    print("[INFO] Running SOAR playbooks...")
    ensure_alerts_table()
    run_playbooks()
    print("[INFO] SOAR processing complete.")
