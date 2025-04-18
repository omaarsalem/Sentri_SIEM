from flask import Flask, render_template, request, redirect, url_for, flash, Response, session, jsonify
import sqlite3
import os
import bcrypt
from functools import wraps
import csv
from flask_wtf.csrf import CSRFProtect
import subprocess

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")
csrf = CSRFProtect(app)

# Make sure the path works both locally and on Render
DATABASE = os.getenv("SENTRI_DB_PATH", "dashboard/database/sentri.db")

# -------------------- Utilities --------------------

def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        app.logger.error(f"Database connection error: {e}")
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
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_id INTEGER,
                    severity TEXT,
                    message TEXT,
                    source_ip TEXT,
                    process_name TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_id INTEGER,
                    severity TEXT,
                    message TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source TEXT,
                    alert_type TEXT,
                    description TEXT,
                    severity TEXT
                )
            """)
            conn.commit()
            conn.close()
            print("✅ Tables ensured.")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")

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
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for('dashboard'))
    alerts = conn.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 100").fetchall()
    conn.close()
    return render_template("alerts.html", alerts=alerts)

@app.route('/reports', methods=['GET'])
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

    query = "SELECT timestamp, event_id, severity, message FROM logs WHERE 1=1"
    params = []
    if keyword:
        query += " AND LOWER(message) LIKE ?"
        params.append(f"%{keyword}%")
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if date_from:
        query += " AND timestamp >= ?"
        params.append(date_from)
    if date_to:
        query += " AND timestamp <= ?"
        params.append(date_to)
    query += " ORDER BY timestamp DESC LIMIT 50"

    logs = conn.execute(query, params).fetchall()
    anomalies = conn.execute("SELECT timestamp, event_id, severity, message FROM anomalies ORDER BY timestamp DESC").fetchall()
    conn.close()
    return render_template("reports.html", logs=logs, anomalies=anomalies)

@app.route('/logs')
@login_required
def get_logs():
    page = int(request.args.get("page", 1))
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    logs = conn.execute(
        "SELECT timestamp, event_id, severity, message FROM logs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
        (per_page, offset)
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in logs])

@app.route('/frequency-analysis')
@login_required
def frequency_analysis():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    event_freq = conn.execute("SELECT event_id, COUNT(*) AS count FROM logs GROUP BY event_id ORDER BY count DESC LIMIT 10").fetchall()

    ip_freq, process_freq = [], []
    log_columns = conn.execute("PRAGMA table_info(logs)").fetchall()
    column_names = [col["name"] for col in log_columns]

    if "source_ip" in column_names:
        ip_freq = conn.execute("SELECT source_ip, COUNT(*) AS count FROM logs GROUP BY source_ip ORDER BY count DESC LIMIT 10").fetchall()
    if "process_name" in column_names:
        process_freq = conn.execute("SELECT process_name, COUNT(*) AS count FROM logs GROUP BY process_name ORDER BY count DESC LIMIT 10").fetchall()

    conn.close()
    return jsonify({
        "event_frequency": [dict(row) for row in event_freq],
        "ip_frequency": [dict(row) for row in ip_freq],
        "process_frequency": [dict(row) for row in process_freq]
    })

@app.route('/settings')
@requires_admin
def settings():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for('dashboard'))

    users = conn.execute("SELECT id, username, role FROM users").fetchall()
    conn.close()
    return render_template("settings.html", users=users)

@app.route('/export/anomalies/csv')
@login_required
def export_anomalies_csv():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for('reports'))

    anomalies = conn.execute("SELECT timestamp, event_id, severity, message FROM anomalies").fetchall()
    conn.close()

    def generate():
        rows = [[a["timestamp"], a["event_id"], a["severity"], a["message"]] for a in anomalies]
        header = ['Timestamp', 'Event ID', 'Severity', 'Message']
        yield "\n".join([",".join(header)] + [",".join(map(str, r)) for r in rows])

    return Response(generate(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=anomalies.csv"})

@app.route('/export/logs/csv')
@login_required
def export_logs_csv():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed", "danger")
        return redirect(url_for('reports'))

    logs = conn.execute("SELECT timestamp, event_id, severity, message FROM logs ORDER BY timestamp DESC LIMIT 50").fetchall()
    conn.close()

    def generate():
        rows = [[l["timestamp"], l["event_id"], l["severity"], l["message"]] for l in logs]
        header = ['Timestamp', 'Event ID', 'Severity', 'Message']
        yield "\n".join([",".join(header)] + [",".join(map(str, r)) for r in rows])

    return Response(generate(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=logs.csv"})

@csrf.exempt
@app.route('/add-user', methods=['POST'])
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
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode()

        conn = get_db_connection()
        if not conn:
            flash("Database connection failed", "danger")
            return redirect(url_for('login'))

        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and bcrypt.checkpw(password, user["password"].encode()):
            session['username'] = user['username']
            session['role'] = user['role']
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("index"))

# -------------------- Entry --------------------

if __name__ == '__main__':
    ensure_tables_exist()

    # ✅ Start main.py in background
    try:
        subprocess.Popen(["python", "scripts/main.py"])
        print("🚀 Background log collection started via main.py")
    except Exception as e:
        print(f"❌ Failed to launch main.py: {e}")

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
