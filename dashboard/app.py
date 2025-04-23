from flask import Flask, render_template, request, redirect, url_for, flash, Response, session, jsonify
import sqlite3, os, bcrypt, csv, subprocess
from datetime import datetime
from functools import wraps
from flask_wtf.csrf import CSRFProtect
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")
csrf = CSRFProtect(app)

DATABASE = os.getenv("SENTRI_DB_PATH", "dashboard/database/sentri.db")
print(f"📂 Using database: {DATABASE}")
# -------------------- Utilities --------------------

def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") != "Admin":
            flash("Access denied: Admins only.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash("Please login first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def ensure_tables_exist():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_id TEXT,
                    severity TEXT,
                    message TEXT,
                    source_ip TEXT,
                    process_name TEXT,
                    source TEXT
                );
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_id TEXT,
                    severity TEXT,
                    message TEXT
                );
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    source TEXT,
                    alert_type TEXT,
                    description TEXT,
                    severity TEXT
                );
                CREATE TABLE IF NOT EXISTS network_traffic (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    source_ip TEXT,
                    destination_ip TEXT,
                    protocol TEXT,
                    packet_length INTEGER
                );
                CREATE TABLE IF NOT EXISTS device_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    device_id TEXT,
                    log_message TEXT
                );
                CREATE TABLE IF NOT EXISTS script_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("✅ Tables ensured.")
        except Exception as e:
            print(f"❌ Table creation error: {e}")
        finally:
            conn.close()

# -------------------- Routes --------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/alerts')
@login_required
def alerts():
    severity = request.args.get("severity", "")
    date_from = request.args.get("from", "")
    date_to = request.args.get("to", "")
    
    query = "SELECT timestamp, source, alert_type, description, severity FROM alerts WHERE 1=1"
    params = []

    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if date_from:
        query += " AND DATE(timestamp) >= ?"
        params.append(date_from)
    if date_to:
        query += " AND DATE(timestamp) <= ?"
        params.append(date_to)

    query += " ORDER BY timestamp DESC"

    conn = get_db_connection()
    alerts = []
    if conn:
        try:
            alerts = conn.execute(query, params).fetchall()
        except Exception as e:
            flash("Failed to load alerts", "danger")
            print(f"[ERROR] Alerts fetch: {e}")
        finally:
            conn.close()

    return render_template("alerts.html", alerts=alerts)

@app.route('/export/alerts/csv')
@login_required
def export_alerts_csv():
    severity = request.args.get("severity", "")
    date_from = request.args.get("from", "")
    date_to = request.args.get("to", "")

    query = "SELECT timestamp, source, alert_type, description, severity FROM alerts WHERE 1=1"
    params = []

    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if date_from:
        query += " AND DATE(timestamp) >= ?"
        params.append(date_from)
    if date_to:
        query += " AND DATE(timestamp) <= ?"
        params.append(date_to)

    conn = get_db_connection()
    alerts = []
    if conn:
        try:
            alerts = conn.execute(query, params).fetchall()
        except Exception as e:
            return Response(f"Error: {e}", status=500)
        finally:
            conn.close()

    def generate_csv():
        yield "Timestamp,Source,Alert Type,Description,Severity\n"
        for a in alerts:
            line = f"{a['timestamp']},{a['source']},{a['alert_type']},{a['description']},{a['severity']}\n"
            yield line

    return Response(generate_csv(), mimetype="text/csv", headers={
        "Content-Disposition": "attachment; filename=sentrisiem_alerts.csv"
    })

@app.route("/reports")
@login_required
def reports():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("dashboard"))

    keyword = request.args.get('keyword', '').lower()
    severity = request.args.get('severity', '')
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')

    logs, anomalies, network_logs = [], [], []

    query = "SELECT timestamp, event_id, severity, message, source FROM logs WHERE 1=1"
    params = []

    if keyword:
        query += " AND LOWER(message) LIKE ?"
        params.append(f"%{keyword}%")
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if date_from:
        query += " AND DATE(timestamp) >= ?"
        params.append(date_from)
    if date_to:
        query += " AND DATE(timestamp) <= ?"
        params.append(date_to)

    query += " ORDER BY timestamp DESC LIMIT 100"

    try:
        logs = conn.execute(query, params).fetchall()
        anomalies = conn.execute("""
            SELECT timestamp, event_id, severity, message 
            FROM anomalies 
            ORDER BY timestamp DESC LIMIT 100
        """).fetchall()

        network_logs = conn.execute("""
            SELECT timestamp, source_ip, destination_ip, protocol, packet_length
            FROM network_traffic
            ORDER BY timestamp DESC LIMIT 100
        """).fetchall()

    except Exception as e:
        flash("Error loading reports", "danger")
        print(f"[ERROR] Failed fetching reports: {e}")
    finally:
        conn.close()

    return render_template("reports.html", logs=logs, anomalies=anomalies, network_logs=network_logs)

@app.route('/logs')
@login_required
def get_logs():
    page = int(request.args.get("page", 1))
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        logs = conn.execute(
            "SELECT timestamp, event_id, severity, message FROM logs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        ).fetchall()
        return jsonify([dict(row) for row in logs])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/settings')
@requires_admin
def settings():
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role FROM users").fetchall() if conn else []
    if conn: conn.close()
    return render_template("settings.html", users=users)

@csrf.exempt
@app.route('/add-user', methods=["POST"])
@requires_admin
def add_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "").strip()

    if not username or not password or not role:
        flash("All fields are required.", "danger")
        return redirect(url_for("settings"))

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for("settings"))

    try:
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed, role))
        conn.commit()
        flash("User added!", "success")
    except sqlite3.IntegrityError:
        flash("Username already exists.", "danger")
    finally:
        conn.close()
    return redirect(url_for("settings"))

@csrf.exempt
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if password is None:
            flash("Password is required.", "danger")
            return redirect(url_for("login"))
        password = password.encode()

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return redirect(url_for("login"))

        try:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user and bcrypt.checkpw(password, user["password"].encode()):
                session["username"] = user["username"]
                session["role"] = user["role"]
                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid credentials", "danger")
        finally:
            conn.close()
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("index"))

# -------------------- Background Scripts + Startup --------------------

if __name__ == "__main__":
    ensure_tables_exist()
    try:
        subprocess.Popen(["python", "scripts/main.py"])
        print("🚀 Background log collection started via main.py")
    except Exception as e:
        print(f"❌ Failed to start main.py: {e}")

    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
