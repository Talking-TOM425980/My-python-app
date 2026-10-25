import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Use /tmp directory on Render to avoid read-only filesystem issues
DB_PATH = "/tmp/database.db" if os.path.exists("/tmp") else "database.db"

# --- Embedded HTML Templates (Single-File Setup) ---

WELCOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Plant System - Welcome</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #04100c 0%, #0c241c 50%, #020705 100%); 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
            margin: 0; 
            color: #ffffff;
            overflow-x: hidden;
            position: relative;
            padding: 20px;
        }
        body::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(0,255,136,0.12) 0%, rgba(0,242,254,0.04) 50%, transparent 70%);
            z-index: 0;
            pointer-events: none;
        }
        .hero-card { 
            position: relative;
            z-index: 1;
            background: rgba(10, 26, 20, 0.85); 
            backdrop-filter: blur(14px);
            padding: 50px 40px; 
            border-radius: 16px; 
            box-shadow: 0 0 40px rgba(0, 255, 136, 0.2), inset 0 0 20px rgba(0, 242, 254, 0.1); 
            border: 1px solid rgba(0, 255, 136, 0.4);
            width: 100%;
            max-width: 550px; 
            text-align: center; 
        }
        h1 { 
            margin: 0 0 10px 0;
            font-size: 36px; 
            text-transform: uppercase; 
            letter-spacing: 3px;
            color: #00ff88; 
            text-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
            font-weight: 800;
        }
        h3 { 
            margin: 0 0 25px 0;
            font-size: 13px; 
            color: #00f2fe; 
            letter-spacing: 4px; 
            text-transform: uppercase;
            text-shadow: 0 0 8px rgba(0, 242, 254, 0.4);
            font-weight: 600;
        }
        .intro-text {
            color: #b0c4bc;
            font-size: 15px;
            line-height: 1.6;
            margin-bottom: 30px;
            text-align: left;
            background: rgba(4, 16, 12, 0.6);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(0, 242, 254, 0.2);
        }
        .btn-group {
            display: flex;
            gap: 15px;
            margin-top: 10px;
        }
        .btn { 
            flex: 1;
            padding: 14px; 
            border-radius: 8px; 
            font-size: 14px;
            font-weight: 700; 
            text-transform: uppercase;
            letter-spacing: 1.5px;
            cursor: pointer; 
            text-decoration: none;
            transition: all 0.3s ease;
            display: inline-block;
        }
        .btn-login {
            background: linear-gradient(90deg, #00ff88, #00b0ff); 
            color: #04100c; 
            border: none;
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
        }
        .btn-login:hover { 
            background: linear-gradient(90deg, #00f2fe, #00ff88); 
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.5);
            transform: translateY(-2px);
        }
        .btn-signup {
            background: transparent;
            color: #00f2fe;
            border: 1px solid rgba(0, 242, 254, 0.5);
            box-shadow: inset 0 0 10px rgba(0, 242, 254, 0.1);
        }
        .btn-signup:hover {
            background: rgba(0, 242, 254, 0.1);
            border-color: #00f2fe;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.3);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="hero-card">
        <h1>Smart Plant</h1>
        <h3>Automated Ecosystem</h3>
        
        <div class="intro-text">
            Welcome to the remote monitoring hub for your smart greenhouse hardware. This web application pairs with your automated system to <strong>water your plants intelligently based on live humidity sensors</strong>. Monitor real-time status, hardware feedback, and LCD telemetry directly from your device anywhere you go.
        </div>

        <div class="btn-group">
            <a href="/login" class="btn btn-login">Login</a>
            <a href="/register" class="btn btn-signup">Sign Up</a>
        </div>
    </div>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Plant System - Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #04100c 0%, #0c241c 50%, #020705 100%); 
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
            background: radial-gradient(circle, rgba(0,255,136,0.12) 0%, rgba(0,242,254,0.04) 50%, transparent 70%);
            z-index: 0;
            pointer-events: none;
        }
        .card { 
            position: relative;
            z-index: 1;
            background: rgba(10, 26, 20, 0.85); 
            backdrop-filter: blur(14px);
            padding: 40px 30px; 
            border-radius: 14px; 
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.2), inset 0 0 15px rgba(0, 242, 254, 0.1); 
            border: 1px solid rgba(0, 255, 136, 0.4);
            width: 350px; 
            text-align: center; 
        }
        h2 { 
            margin: 0;
            font-size: 28px; 
            text-transform: uppercase; 
            letter-spacing: 2px;
            color: #00ff88; 
            text-shadow: 0 0 12px rgba(0, 255, 136, 0.4);
            font-weight: 700;
        }
        h3 { 
            margin: 5px 0 25px 0;
            font-size: 14px; 
            color: #00f2fe; 
            letter-spacing: 3px; 
            text-transform: uppercase;
            text-shadow: 0 0 8px rgba(0, 242, 254, 0.4);
            font-weight: 500;
        }
        input { 
            width: 100%; 
            padding: 12px 16px; 
            margin: 10px 0; 
            background: rgba(4, 16, 12, 0.8);
            border: 1px solid rgba(0, 242, 254, 0.3); 
            border-radius: 8px; 
            color: #ffffff;
            font-size: 14px;
            outline: none;
            transition: all 0.3s ease;
        }
        input:focus {
            border-color: #00ff88;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }
        button { 
            width: 100%; 
            padding: 12px; 
            margin-top: 15px;
            background: linear-gradient(90deg, #00ff88, #00b0ff); 
            color: #04100c; 
            border: none; 
            border-radius: 8px; 
            font-size: 15px;
            font-weight: 700; 
            text-transform: uppercase;
            letter-spacing: 1.5px;
            cursor: pointer; 
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
            transition: all 0.3s ease;
        }
        button:hover { 
            background: linear-gradient(90deg, #00f2fe, #00ff88); 
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.5);
            transform: translateY(-1px);
        }
        .error-msg {
            background-color: rgba(255, 0, 85, 0.15);
            color: #ff3366;
            border: 1px solid rgba(255, 51, 102, 0.4);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 0 8px rgba(255, 51, 102, 0.2);
        }
        p { margin-top: 25px; font-size: 13px; color: #8fa39b; }
        a { color: #00f2fe; text-decoration: none; font-weight: 600; transition: color 0.2s; }
        a:hover { color: #00ff88; text-shadow: 0 0 6px rgba(0, 255, 136, 0.4); }
    </style>
</head>
<body>
    <div class="card">
        <h2>Plant Net</h2>
        <h3>Secure Access</h3>
        {% if error %}
            <div class="error-msg">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Sign In</button>
        </form>
        <p>New ecosystem account? <a href="/register">Register</a></p>
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
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #04100c 0%, #0c241c 50%, #020705 100%); 
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
            background: radial-gradient(circle, rgba(0,242,254,0.12) 0%, rgba(0,255,136,0.04) 50%, transparent 70%);
            z-index: 0;
            pointer-events: none;
        }
        .card { 
            position: relative;
            z-index: 1;
            background: rgba(10, 26, 20, 0.85); 
            backdrop-filter: blur(14px);
            padding: 40px 30px; 
            border-radius: 14px; 
            box-shadow: 0 0 30px rgba(0, 242, 254, 0.2), inset 0 0 15px rgba(0, 255, 136, 0.1); 
            border: 1px solid rgba(0, 242, 254, 0.4);
            width: 350px; 
            text-align: center; 
        }
        h2 { 
            margin: 0 0 25px 0;
            font-size: 26px; 
            text-transform: uppercase; 
            letter-spacing: 2px;
            color: #00f2fe; 
            text-shadow: 0 0 12px rgba(0, 242, 254, 0.4);
            font-weight: 700;
        }
        input { 
            width: 100%; 
            padding: 12px 16px; 
            margin: 10px 0; 
            background: rgba(4, 16, 12, 0.8);
            border: 1px solid rgba(0, 255, 136, 0.3); 
            border-radius: 8px; 
            color: #ffffff;
            font-size: 14px;
            outline: none;
            transition: all 0.3s ease;
        }
        input:focus {
            border-color: #00f2fe;
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
        }
        button { 
            width: 100%; 
            padding: 12px; 
            margin-top: 15px;
            background: linear-gradient(90deg, #00f2fe, #00ff88); 
            color: #04100c; 
            border: none; 
            border-radius: 8px; 
            font-size: 15px;
            font-weight: 700; 
            text-transform: uppercase;
            letter-spacing: 1.5px;
            cursor: pointer; 
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.3);
            transition: all 0.3s ease;
        }
        button:hover { 
            background: linear-gradient(90deg, #00ff88, #00f2fe); 
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
            transform: translateY(-1px);
        }
        .error-msg {
            background-color: rgba(255, 0, 85, 0.15);
            color: #ff3366;
            border: 1px solid rgba(255, 51, 102, 0.4);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 0 8px rgba(255, 51, 102, 0.2);
        }
        p { margin-top: 25px; font-size: 13px; color: #8fa39b; }
        a { color: #00ff88; text-decoration: none; font-weight: 600; transition: color 0.2s; }
        a:hover { color: #00f2fe; text-shadow: 0 0 6px rgba(0, 242, 254, 0.4); }
    </style>
</head>
<body>
    <div class="card">
        <h2>Join Network</h2>
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

SETUP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Plant System - Setup</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #04100c 0%, #0c241c 50%, #020705 100%); 
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
            background: radial-gradient(circle, rgba(0,255,136,0.12) 0%, rgba(0,242,254,0.04) 50%, transparent 70%);
            z-index: 0;
            pointer-events: none;
        }
        .card { 
            position: relative;
            z-index: 1;
            background: rgba(10, 26, 20, 0.85); 
            backdrop-filter: blur(14px);
            padding: 40px 30px; 
            border-radius: 14px; 
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.2), inset 0 0 15px rgba(0, 242, 254, 0.1); 
            border: 1px solid rgba(0, 255, 136, 0.4);
            width: 380px; 
            text-align: center; 
        }
        h2 { 
            margin: 0 0 10px 0;
            font-size: 24px; 
            text-transform: uppercase; 
            letter-spacing: 2px;
            color: #00ff88; 
            text-shadow: 0 0 12px rgba(0, 255, 136, 0.4);
            font-weight: 700;
        }
        p.subtitle {
            color: #8fa39b;
            font-size: 13px;
            margin-bottom: 25px;
        }
        input { 
            width: 100%; 
            padding: 12px 16px; 
            margin: 10px 0; 
            background: rgba(4, 16, 12, 0.8);
            border: 1px solid rgba(0, 242, 254, 0.3); 
            border-radius: 8px; 
            color: #ffffff;
            font-size: 14px;
            outline: none;
            transition: all 0.3s ease;
        }
        input:focus {
            border-color: #00ff88;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }
        button { 
            width: 100%; 
            padding: 12px; 
            margin-top: 15px;
            background: linear-gradient(90deg, #00ff88, #00b0ff); 
            color: #04100c; 
            border: none; 
            border-radius: 8px; 
            font-size: 15px;
            font-weight: 700; 
            text-transform: uppercase;
            letter-spacing: 1.5px;
            cursor: pointer; 
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.3);
            transition: all 0.3s ease;
        }
        button:hover { 
            background: linear-gradient(90deg, #00f2fe, #00ff88); 
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.5);
            transform: translateY(-1px);
        }
        .error-msg {
            background-color: rgba(255, 0, 85, 0.15);
            color: #ff3366;
            border: 1px solid rgba(255, 51, 102, 0.4);
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 13px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>System Configuration</h2>
        <p class="subtitle">Please assign a designation to your automated water system.</p>
        {% if error %}
            <div class="error-msg">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/setup-system">
            <input type="text" name="system_name" placeholder="e.g., Greenhouse Alpha" required><br>
            <button type="submit">Initialize System</button>
        </form>
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
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #04100c 0%, #0c241c 50%, #020705 100%); 
            min-height: 100vh;
            margin: 0; 
            padding: 30px; 
            color: #ffffff;
        }
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: rgba(10, 26, 20, 0.85); 
            backdrop-filter: blur(14px);
            padding: 20px 30px; 
            border-radius: 14px; 
            border: 1px solid rgba(0, 255, 136, 0.3);
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.15); 
            max-width: 900px;
            margin: 0 auto;
        }
        .header h2 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
        }
        .header h2 span {
            color: #00ff88;
            text-shadow: 0 0 8px rgba(0, 255, 136, 0.4);
        }
        .container { 
            background: rgba(10, 26, 20, 0.85); 
            backdrop-filter: blur(14px);
            padding: 35px; 
            border-radius: 14px; 
            margin: 25px auto 0 auto; 
            max-width: 900px;
            border: 1px solid rgba(0, 242, 254, 0.3);
            box-shadow: 0 0 25px rgba(0, 242, 254, 0.15); 
        }
        h3, h4 {
            color: #00f2fe;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            text-shadow: 0 0 6px rgba(0, 242, 254, 0.4);
            margin-top: 0;
            font-size: 16px;
        }
        .status-badge { 
            display: inline-block; 
            padding: 6px 14px; 
            border-radius: 20px; 
            font-weight: 700; 
            text-transform: uppercase; 
            letter-spacing: 1px;
            font-size: 13px;
        }
        .on { 
            background-color: rgba(0, 255, 136, 0.15); 
            color: #00ff88; 
            border: 1px solid rgba(0, 255, 136, 0.4);
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
        }
        .off { 
            background-color: rgba(255, 51, 102, 0.15); 
            color: #ff3366; 
            border: 1px solid rgba(255, 51, 102, 0.4);
            box-shadow: 0 0 10px rgba(255, 51, 102, 0.3);
        }
        pre { 
            background: #020705; 
            color: #00ff88; 
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid rgba(0, 255, 136, 0.25);
            box-shadow: inset 0 0 15px rgba(0, 255, 136, 0.1);
            font-family: 'Courier New', Courier, monospace; 
            font-size: 15px; 
            white-space: pre-wrap; 
            word-wrap: break-word; 
            text-shadow: 0 0 5px rgba(0, 255, 136, 0.3);
        }
        .logout-btn { 
            color: #ff3366; 
            text-decoration: none; 
            font-weight: 600; 
            text-transform: uppercase;
            letter-spacing: 1px;
            border: 1px solid rgba(255, 51, 102, 0.4);
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 13px;
            transition: all 0.3s ease;
        }
        .logout-btn:hover {
            background: #ff3366;
            color: #04100c;
            box-shadow: 0 0 10px rgba(255, 51, 102, 0.5);
        }
    </style>
    <script>
        const username = "{{ username }}";
        const systemName = "{{ system_name }}";

        async function fetchStatus() {
            try {
                let response = await fetch('/api/status');
                let data = await response.json();
                
                let stateElem = document.getElementById('state');
                let isConnected = data.state.toLowerCase() === 'on';
                
                stateElem.innerText = data.state;
                stateElem.className = 'status-badge ' + (isConnected ? 'on' : 'off');
                
                let headerTitle = document.getElementById('header-title');
                if (isConnected) {
                    headerTitle.innerHTML = `Hello ${username}, <span>${systemName}</span> has connected successfully!`;
                } else {
                    headerTitle.innerHTML = `Hello ${username}, <span>${systemName}</span> is awaiting for connection`;
                }
                
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
        <h2 id="header-title">Hello {{ username }}, <span>{{ system_name }}</span> is awaiting for connection</h2>
        <div><a href="/logout" class="logout-btn">Logout</a></div>
    </div>
    
    <div class="container">
        <h3>Live Telemetry</h3>
        <p><strong>System State:</strong> <span id="state" class="status-badge off">Loading...</span></p>
        <h4 style="margin-top: 30px;">LCD Display Feedback:</h4>
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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                water_system_name TEXT
            )
        ''')

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


# --- Routes ---

@app.route("/")
def home():
    """Welcome screen landing page."""
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template_string(WELCOME_HTML)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user["password_hash"], password):
                session["user"] = username
                if not user["water_system_name"]:
                    return redirect(url_for("setup_system"))
                return redirect(url_for("dashboard"))

            return render_template_string(LOGIN_HTML, error="Invalid Credentials")
        except Exception as e:
            return render_template_string(LOGIN_HTML, error=f"Database Error: {e}")

    return render_template_string(LOGIN_HTML, error=None)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template_string(REGISTER_HTML, error="Missing username or password")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, water_system_name) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), None)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template_string(REGISTER_HTML, error="Username already exists!")
        except Exception as e:
            return render_template_string(REGISTER_HTML, error=f"Database Error: {e}")

    return render_template_string(REGISTER_HTML, error=None)


@app.route("/setup-system", methods=["GET", "POST"])
def setup_system():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        system_name = request.form.get("system_name")
        if not system_name:
            return render_template_string(SETUP_HTML, error="Water system name is required")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET water_system_name = ? WHERE username = ?", (system_name, session["user"]))
            conn.commit()
            conn.close()
            return redirect(url_for("dashboard"))
        except Exception as e:
            return render_template_string(SETUP_HTML, error=f"Database Error: {e}")

    return render_template_string(SETUP_HTML, error=None)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT water_system_name FROM users WHERE username = ?", (session["user"],))
        user = cursor.fetchone()
        conn.close()

        if not user or not user["water_system_name"]:
            return redirect(url_for("setup_system"))
            
        return render_template_string(DASHBOARD_HTML, username=session["user"], system_name=user["water_system_name"])
    except Exception:
        return redirect(url_for("setup_system"))


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
            cursor.execute("UPDATE telemetry SET device_state = ?, lcd_text = ? WHERE id = 1", (new_lcd,)) # handled appropriately

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
