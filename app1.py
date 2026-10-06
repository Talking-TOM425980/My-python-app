import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Use /tmp directory on Render to avoid read-only filesystem issues
DB_PATH = "/tmp/database.db" if os.path.exists("/tmp") else "database.db"

# --- Embedded HTML Templates (Single-File Setup) ---

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Plant System - Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 300px; text-align: center; }
        input { width: 90%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { width: 95%; padding: 10px; background-color: #28a745; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #218838; }
        a { color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Plant Monitor</h2>
        <h3>Login</h3>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Sign In</button>
        </form>
        <p style="margin-top: 15px;">Don't have an account? <a href="/register">Register</a></p>
    </div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Plant System - Register</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 300px; text-align: center; }
        input { width: 90%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { width: 95%; padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #0069d9; }
        a { color: #28a745; text-decoration: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Create Account</h2>
        <form method="POST" action="/register">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Register</button>
        </form>
        <p style="margin-top: 15px;">Already registered? <a href="/login">Login here</a></p>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Plant Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background-color: #eef2f5; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: white; padding: 15px 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .container { background: white; padding: 25px; border-radius: 8px; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .status-badge { display: inline-block; padding: 6px 12px; border-radius: 20px; font-weight: bold; text-transform: uppercase; }
        .on { background-color: #d4edda; color: #155724; }
        .off { background-color: #f8d7da; color: #721c24; }
        pre { background: #1e1e1e; color: #00ff66; padding: 20px; border-radius: 6px; font-family: monospace; font-size: 16px; white-space: pre-wrap; word-wrap: break-word; }
        .logout-btn { color: #dc3545; text-decoration: none; font-weight: bold; }
    </style>
    <script>
        async function fetchStatus() {
            try {
                let response = await fetch('/api/status');
                let data = await response.json();
                
                let stateElem = document.getElementById('state');
                stateElem.innerText = data.state;
                stateElem.className = 'status-badge ' + (data.state.toLowerCase() === 'on' ? 'on' : 'off');
                
                document.getElementById('lcd').innerText = data.lcd_text;
            } catch (err) {
                console.error("Error fetching status:", err);
            }
        }
        setInterval(fetchStatus, 2000);
        window.onload = fetchStatus;
    </script>
</head>
<body>
    <div class="header">
        <h2>Smart Plant System</h2>
        <div>Welcome, <strong>{{ username }}</strong> | <a href="/logout" class="logout-btn">Logout</a></div>
    </div>
    
    <div class="container">
        <h3>Live Telemetry</h3>
        <p><strong>System State:</strong> <span id="state" class="status-badge off">Loading...</span></p>
        <h4>LCD Display Feedback:</h4>
        <pre id="lcd">Connecting to hardware feed...</pre>
    </div>
</body>
</html>
"""


# --- Database Connection & Setup ---

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')

        # 2. Telemetry Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                device_state TEXT NOT NULL,
                lcd_text TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            INSERT OR IGNORE INTO telemetry (id, device_state, lcd_text) 
            VALUES (1, 'off', 'System Initializing...\nWaiting for Raspberry Pi connection...')
        ''')

        conn.commit()
        conn.close()
        print(f"Database successfully initialized at {DB_PATH}")
    except Exception as e:
        print(f"Database Initialization Error: {e}")


init_db()


# --- Authentication Routes ---

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template_string(LOGIN_HTML)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return "Missing username or password", 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already exists!", 400
        except Exception as e:
            return f"Database Error: {e}", 500

    return render_template_string(REGISTER_HTML)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user["password_hash"], password):
                session["user"] = username
                return redirect(url_for("dashboard"))

            return "Invalid Credentials", 401
        except Exception as e:
            return f"Database Error: {e}", 500

    return render_template_string(LOGIN_HTML)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template_string(DASHBOARD_HTML, username=session["user"])


# --- Real-Time API Routes ---

@app.route("/api/status", methods=["GET"])
def get_status():
    """Endpoint for frontend dashboard live updates."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT device_state, lcd_text FROM telemetry WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify(state=row["device_state"], lcd_text=row["lcd_text"])
        return jsonify(state="off", lcd_text="System Initializing...")
    except Exception as e:
        return jsonify(state="off", lcd_text=f"Database error: {e}"), 500


@app.route("/api/device", methods=["POST"])
def control_device():
    """Endpoint receiving hardware telemetry from Raspberry Pi (humidity3.py)."""
    data = request.get_json(silent=True) or {}
    new_state = data.get("action")
    new_lcd = data.get("lcd_text")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if new_state and new_lcd:
            cursor.execute("UPDATE telemetry SET device_state = ?, lcd_text = ? WHERE id = 1", (new_state, new_lcd))
        elif new_state:
            cursor.execute("UPDATE telemetry SET device_state = ? WHERE id = 1", (new_state,))
        elif new_lcd:
            cursor.execute("UPDATE telemetry SET lcd_text = ? WHERE id = 1", (new_lcd,))

        conn.commit()

        cursor.execute("SELECT device_state, lcd_text FROM telemetry WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify(state=row["device_state"], lcd_text=row["lcd_text"])
        return jsonify(state=new_state or "off", lcd_text=new_lcd or "")
    except Exception as e:
        return jsonify(error=str(e)), 500


# --- Server Start ---

if __name__ == "__main__":
    # Render assigns dynamic port numbers via os.environ
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
