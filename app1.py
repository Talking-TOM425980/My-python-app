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
        * { box-sizing: border-box; }
        body { 
            font-family: 'Trebuchet MS', 'Impact', sans-serif; 
            background: linear-gradient(135deg, #0f051d 0%, #2e114d 50%, #03001e 100%); 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            color: #ffffff;
            overflow: hidden;
            position: relative;
        }
        body::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,0,127,0.15) 0%, rgba(0,242,254,0.05) 50%, transparent 70%);
            z-index: 0;
            pointer-events: none;
        }
        .card { 
            position: relative;
            z-index: 1;
            background: rgba(18, 10, 36, 0.85); 
            backdrop-filter: blur(12px);
            padding: 40px 30px; 
            border-radius: 12px; 
            box-shadow: 0 0 25px rgba(255, 0, 127, 0.35), inset 0 0 15px rgba(0, 242, 254, 0.15); 
            border: 2px solid #ff007f;
            width: 340px; 
            text-align: center; 
        }
        h2 { 
            margin: 0;
            font-size: 32px; 
            text-transform: uppercase; 
            letter-spacing: 2px;
            color: #ff007f; 
            text-shadow: 0 0 10px #ff007f, 0 0 20px #ff007f; 
            font-style: italic;
        }
        h3 { 
            margin: 5px 0 20px 0;
            font-size: 18px; 
            color: #00f2fe; 
            letter-spacing: 3px; 
            text-transform: uppercase;
            text-shadow: 0 0 8px #00f2fe;
        }
        input { 
            width: 100%; 
            padding: 12px; 
            margin: 10px 0; 
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid #00f2fe; 
            border-radius: 6px; 
            color: #ffffff;
            font-size: 15px;
            outline: none;
            transition: all 0.3s ease;
        }
        input:focus {
            border-color: #ff007f;
            box-shadow: 0 0 10px #ff007f;
        }
        button { 
            width: 100%; 
            padding: 12px; 
            margin-top: 15px;
            background: linear-gradient(90deg, #ff007f, #7928ca); 
            color: white; 
            border: none; 
            border-radius: 6px; 
            font-size: 16px;
            font-weight: bold; 
            text-transform: uppercase;
            letter-spacing: 1.5px;
            cursor: pointer; 
            box-shadow: 0 0 12px rgba(255, 0, 127, 0.5);
            transition: all 0.3s ease;
        }
        button:hover { 
            background: linear-gradient(90deg, #00f2fe, #4facfe); 
            box-shadow: 0 0 20px #00f2fe;
            color: #000;
        }
        .error-msg {
            background-color: rgba(255, 0, 85, 0.2);
            color: #ff0055;
            border: 1px solid #ff0055;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 14px;
            font-weight: bold;
            box-shadow: 0 0 8px #ff0055;
        }
        p { margin-top: 20px; font-size: 14px; color: #b3b3b3; }
        a { color: #00f2fe; text-decoration: none; font-weight: bold; text-shadow: 0 0 5px #00f2fe; }
        a:hover { color: #ff007f; text-shadow: 0 0 8px #ff007f; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Plant Net</h2>
        <h3>Login</h3>
        {% if error %}
            <div class="error-msg">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Sign In</button>
        </form>
        <p>Don't have an account? <a href="/register">Register</a></p>
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
        * { box-sizing: border-box; }
        body { 
            font-family: 'Trebuchet MS', 'Impact', sans-serif; 
            background: linear-gradient(135deg, #0f051d 0%, #2e114d 50%, #03001e 100%); 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            color: #ffffff;
            overflow: hidden;
            position: relative;
        }
        body::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(0,242,254,0.15) 0%, rgba(255,0,127,0.05) 50%, transparent 70%);
            z-index: 0;
            pointer-events: none;
        }
        .card { 
            position: relative;
            z-index: 1;
            background: rgba(18, 10, 36, 0.85); 
            backdrop-filter: blur(12px);
            padding: 40px 30px; 
            border-radius: 12px; 
            box-shadow: 0 0 25px rgba(0, 242, 254, 0.35), inset 0 0 15px rgba(255, 0, 127, 0.15); 
            border: 2px solid #00f2fe;
            width: 340px; 
            text-align: center; 
        }
        h2 { 
            margin: 0 0 20px 0;
            font-size: 28px; 
            text-transform: uppercase; 
            letter-spacing: 2px;
            color: #00f2fe; 
            text-shadow: 0 0 10px #00f2fe, 0 0 20px #00f2fe; 
            font-style: italic;
        }
        input { 
            width: 100%; 
            padding: 12px; 
            margin: 10px 0; 
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid #ff007f; 
            border-radius: 6px; 
            color: #ffffff;
            font-size: 15px;
            outline: none;
            transition: all 0.3s ease;
        }
        input:focus {
            border-color: #00f2fe;
            box-shadow: 0 0 10px #00f2fe;
        }
        button { 
            width: 100%; 
            padding: 12px; 
            margin-top: 15px;
            background: linear-gradient(90deg, #00f2fe, #4facfe); 
            color: #000; 
            border: none; 
            border-radius: 6px; 
            font-size: 16px;
            font-weight: bold; 
            text-transform: uppercase;
            letter-spacing: 1.5px;
            cursor: pointer; 
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.5);
            transition: all 0.3s ease;
        }
        button:hover { 
            background: linear-gradient(90deg, #ff007f, #7928ca); 
            box-shadow: 0 0 20px #ff007f;
            color: #fff;
        }
        .error-msg {
            background-color: rgba(255, 0, 85, 0.2);
            color: #ff0055;
            border: 1px solid #ff0055;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 14px;
            font-weight: bold;
            box-shadow: 0 0 8px #ff0055;
        }
        p { margin-top: 20px; font-size: 14px; color: #b3b3b3; }
        a { color: #ff007f; text-decoration: none; font-weight: bold; text-shadow: 0 0 5px #ff007f; }
        a:hover { color: #00f2fe; text-shadow: 0 0 8px #00f2fe; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Create Account</h2>
        {% if error %}
            <div class="error-msg">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/register">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Register</button>
        </form>
        <p>Already registered? <a href="/login">Login here</a></p>
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
        * { box-sizing: border-box; }
        body { 
            font-family: 'Trebuchet MS', 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #0b0217 0%, #1d0936 50%, #03001e 100%); 
            min-height: 100vh;
            margin: 0; 
            padding: 20px; 
            color: #ffffff;
        }
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: rgba(18, 10, 36, 0.85); 
            backdrop-filter: blur(10px);
            padding: 20px 25px; 
            border-radius: 12px; 
            border: 1px solid #ff007f;
            box-shadow: 0 0 15px rgba(255, 0, 127, 0.25); 
        }
        .header h2 {
            margin: 0;
            font-size: 26px;
            font-style: italic;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #ff007f;
            text-shadow: 0 0 8px #ff007f;
        }
        .container { 
            background: rgba(18, 10, 36, 0.85); 
            backdrop-filter: blur(10px);
            padding: 30px; 
            border-radius: 12px; 
            margin-top: 25px; 
            border: 1px solid #00f2fe;
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.2); 
        }
        h3, h4 {
            color: #00f2fe;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            text-shadow: 0 0 6px #00f2fe;
            margin-top: 0;
        }
        .status-badge { 
            display: inline-block; 
            padding: 8px 16px; 
            border-radius: 20px; 
            font-weight: bold; 
            text-transform: uppercase; 
            letter-spacing: 1px;
            font-size: 14px;
        }
        .on { 
            background-color: rgba(0, 255, 128, 0.2); 
            color: #00ff80; 
            border: 1px solid #00ff80;
            box-shadow: 0 0 10px #00ff80;
        }
        .off { 
            background-color: rgba(255, 0, 85, 0.2); 
            color: #ff0055; 
            border: 1px solid #ff0055;
            box-shadow: 0 0 10px #ff0055;
        }
        pre { 
            background: #05020a; 
            color: #ff007f; 
            padding: 20px; 
            border-radius: 8px; 
            border: 1px solid #ff007f;
            box-shadow: inset 0 0 15px rgba(255, 0, 127, 0.3);
            font-family: 'Courier New', Courier, monospace; 
            font-size: 16px; 
            white-space: pre-wrap; 
            word-wrap: break-word; 
            text-shadow: 0 0 5px #ff007f;
        }
        .logout-btn { 
            color: #ff0055; 
            text-decoration: none; 
            font-weight: bold; 
            text-transform: uppercase;
            letter-spacing: 1px;
            border: 1px solid #ff0055;
            padding: 6px 12px;
            border-radius: 6px;
            transition: all 0.3s ease;
        }
        .logout-btn:hover {
            background: #ff0055;
            color: #fff;
            box-shadow: 0 0 10px #ff0055;
        }
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
        <div>Welcome, <strong style="color: #00f2fe; text-shadow: 0 0 5px #00f2fe;">{{ username }}</strong> | <a href="/logout" class="logout-btn">Logout</a></div>
    </div>
    
    <div class="container">
        <h3>Live Telemetry</h3>
        <p><strong>System State:</strong> <span id="state" class="status-badge off">Loading...</span></p>
        <h4 style="margin-top: 25px;">LCD Display Feedback:</h4>
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
    return render_template_string(LOGIN_HTML, error=None)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template_string(REGISTER_HTML, error="Missing username or password")

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
            return render_template_string(REGISTER_HTML, error="Username already exists!")
        except Exception as e:
            return render_template_string(REGISTER_HTML, error=f"Database Error: {e}")

    return render_template_string(REGISTER_HTML, error=None)


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

            return render_template_string(LOGIN_HTML, error="Invalid Credentials")
        except Exception as e:
            return render_template_string(LOGIN_HTML, error=f"Database Error: {e}")

    return render_template_string(LOGIN_HTML, error=None)


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
