import sqlite3
from flask import Flask, jsonify, request, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "plant_waterer_secret_key_change_in_production"

device_state = "off"
lcd_text = "System Initializing...\nWaiting for Raspberry Pi connection..."

# Initialize SQLite database for persistent user storage
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Plant Hydro-Dash</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800;900&family=Share+Tech+Mono&display=swap');

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', -apple-system, sans-serif;
            background: linear-gradient(135deg, #0d0118 0%, #2a0036 25%, #6a0d4f 55%, #d9383a 82%, #f99f38 100%);
            background-attachment: fixed;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow-x: hidden;
            color: #ffffff;
        }

        body::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at 50% 30%, rgba(255, 0, 128, 0.25) 0%, transparent 70%);
            pointer-events: none;
        }

        .screen-container {
            position: relative;
            z-index: 10;
            width: 100%;
            max-width: 440px;
            padding: 20px;
        }

        /* Neon Glassmorphism Card */
        .card {
            background: rgba(15, 7, 26, 0.78);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 0, 128, 0.3);
            border-radius: 24px;
            padding: 32px 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6),
                        0 0 30px rgba(236, 72, 153, 0.2);
            text-align: center;
            transition: all 0.3s ease;
        }

        .hidden {
            display: none !important;
        }

        /* Vibrant Titles */
        .title {
            font-size: 30px;
            font-weight: 900;
            font-style: italic;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            background: linear-gradient(180deg, #ffffff 10%, #ff71ce 60%, #b92b88 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(255, 113, 206, 0.6);
            margin-bottom: 4px;
        }

        .subtitle {
            color: #f472b6;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 20px;
            opacity: 0.9;
        }

        /* Features List on Welcome Screen */
        .desc-text {
            color: #cbd5e1;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 20px;
            text-align: left;
        }

        .features-list {
            text-align: left;
            margin-bottom: 24px;
            list-style: none;
        }

        .features-list li {
            color: #f8fafc;
            font-size: 13px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .features-list span {
            color: #ff71ce;
            font-weight: bold;
        }

        /* Input Controls */
        .input-group {
            margin-bottom: 16px;
            text-align: left;
        }

        .input-group label {
            display: block;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #fb7185;
            margin-bottom: 6px;
        }

        .input-field {
            width: 100%;
            padding: 14px 16px;
            background: rgba(10, 4, 18, 0.8);
            border: 1px solid rgba(244, 114, 182, 0.3);
            border-radius: 12px;
            color: #38bdf8;
            font-family: 'Share Tech Mono', monospace;
            font-size: 14px;
            outline: none;
            transition: all 0.3s ease;
        }

        .input-field:focus {
            border-color: #ff71ce;
            box-shadow: 0 0 12px rgba(255, 113, 206, 0.5);
        }

        /* Action Buttons */
        .btn {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 12px;
            font-family: 'Outfit', sans-serif;
            font-size: 16px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }

        .btn:hover {
            transform: translateY(-2px);
            opacity: 0.95;
        }

        .btn-primary {
            background: linear-gradient(90deg, #ec4899 0%, #f43f5e 100%);
            color: #ffffff;
            box-shadow: 0 4px 15px rgba(236, 72, 153, 0.4);
        }

        .toggle-link {
            display: block;
            margin-top: 16px;
            color: #94a3b8;
            font-size: 12px;
            text-decoration: none;
            cursor: pointer;
            transition: color 0.2s;
        }

        .toggle-link:hover {
            color: #f472b6;
        }

        /* Terminal-style LCD Display */
        .lcd-display {
            background-color: #05030a;
            color: #38bdf8;
            font-family: 'Share Tech Mono', monospace;
            padding: 16px;
            border-radius: 14px;
            text-align: left;
            margin-bottom: 20px;
            border: 2px solid rgba(56, 189, 248, 0.4);
            font-size: 13px;
            line-height: 1.5;
            white-space: pre-wrap;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.9), 0 0 15px rgba(56, 189, 248, 0.2);
            min-height: 85px;
        }

        .status-badge {
            display: inline-block;
            padding: 8px 18px;
            border-radius: 20px;
            font-weight: 800;
            font-size: 12px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 20px;
        }

        .status-on {
            background: rgba(34, 197, 94, 0.2);
            color: #4ade80;
            border: 1px solid #22c55e;
            box-shadow: 0 0 12px rgba(34, 197, 94, 0.3);
        }

        .status-off {
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
            border: 1px solid #ef4444;
            box-shadow: 0 0 12px rgba(239, 68, 68, 0.3);
        }

        .control-grid {
            display: flex;
            gap: 12px;
        }

        .btn-on {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }

        .btn-off {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
        }

        .msg-box {
            color: #f43f5e;
            font-size: 12px;
            margin-bottom: 12px;
            font-weight: 600;
        }
    </style>
</head>
<body>

    <div class="screen-container">

        <!-- SCREEN 1: WELCOME SCREEN -->
        <div id="welcome-card" class="card">
            <h1 class="title">AquaPlant AI</h1>
            <p class="subtitle">Automatic Plant Irrigation System</p>
            
            <p class="desc-text">
                Welcome to AquaPlant! Your automated companion for smart hydration, soil monitoring, and automated pump scheduling via your Raspberry Pi.
            </p>

            <ul class="features-list">
                <li><span>💧</span> Automated Moisture Diagnostics</li>
                <li><span>⚡</span> Real-time Remote Pump Control</li>
                <li><span>📟</span> Live LCD System Telemetry</li>
            </ul>

            <button class="btn btn-primary" onclick="showAuthScreen()">Get Started</button>
        </div>

        <!-- SCREEN 2: ACCOUNT CREATION / LOGIN SCREEN -->
        <div id="auth-card" class="card hidden">
            <h1 class="title" id="auth-title">Create Account</h1>
            <p class="subtitle" id="auth-subtitle">Secure Access Portal</p>

            <div id="auth-msg" class="msg-box"></div>

            <form id="auth-form" onsubmit="handleAuth(event)">
                <div class="input-group">
                    <label>Username</label>
                    <input type="text" id="username" class="input-field" placeholder="Enter username" required>
                </div>

                <div class="input-group">
                    <label>Password</label>
                    <input type="password" id="password" class="input-field" placeholder="••••••••" required>
                </div>

                <button type="submit" class="btn btn-primary" id="auth-btn">Register</button>
            </form>

            <a class="toggle-link" id="auth-toggle" onclick="toggleAuthMode()">Already have an account? Log In</a>
        </div>

        <!-- SCREEN 3: MAIN CONTROL PANEL -->
        <div id="dashboard-card" class="card hidden">
            <h1 class="title">Plant Control</h1>
            <p class="subtitle">Pump & LCD Telemetry</p>
            
            <div class="lcd-display" id="lcd-screen">{{ lcd_data }}</div>

            <div id="status" class="status-badge status-{{ state }}">
                Pump is {{ state }}
            </div>

            <div class="control-grid">
                <button class="btn btn-on" onclick="sendAction('on')">WATER ON</button>
                <button class="btn btn-off" onclick="sendAction('off')">WATER OFF</button>
            </div>

            <a class="toggle-link" onclick="logout()">Log Out Session</a>
        </div>

    </div>

    <script>
        let isLoginMode = false;

        function showAuthScreen() {
            document.getElementById('welcome-card').classList.add('hidden');
            document.getElementById('auth-card').classList.remove('hidden');
        }

        function toggleAuthMode() {
            isLoginMode = !isLoginMode;
            document.getElementById('auth-title').innerText = isLoginMode ? "User Login" : "Create Account";
            document.getElementById('auth-subtitle').innerText = isLoginMode ? "Enter credentials" : "Secure Access Portal";
            document.getElementById('auth-btn').innerText = isLoginMode ? "Log In" : "Register";
            document.getElementById('auth-toggle').innerText = isLoginMode ? "Need an account? Register" : "Already have an account? Log In";
            document.getElementById('auth-msg').innerText = "";
        }

        function handleAuth(e) {
            e.preventDefault();
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            const endpoint = isLoginMode ? '/api/login' : '/api/register';

            fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: u, password: p })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('auth-card').classList.add('hidden');
                    document.getElementById('dashboard-card').classList.remove('hidden');
                } else {
                    document.getElementById('auth-msg').innerText = data.message;
                }
            })
            .catch(err => console.error("Auth error:", err));
        }

        function logout() {
            fetch('/api/logout', { method: 'POST' }).then(() => {
                document.getElementById('dashboard-card').classList.add('hidden');
                document.getElementById('welcome-card').classList.remove('hidden');
            });
        }

        function sendAction(actionValue) {
            fetch('/api/device', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: actionValue })
            })
            .then(res => res.json())
            .then(data => {
                const statusDiv = document.getElementById('status');
                statusDiv.innerText = "Pump is " + data.state;
                statusDiv.className = "status-badge " + (data.state === 'on' ? "status-on" : "status-off");
            })
            .catch(err => console.error("Error updating pump state:", err));
        }

        setInterval(() => {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('lcd-screen').innerText = data.lcd_text;
                    const statusDiv = document.getElementById('status');
                    statusDiv.innerText = "Pump is " + data.state;
                    statusDiv.className = "status-badge " + (data.state === 'on' ? "status-on" : "status-off");
                })
                .catch(err => console.error("Sync Error:", err));
        }, 1000);
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE, state=device_state, lcd_data=lcd_text)

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify(success=False, message="Username and password are required.")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        pw_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
        conn.commit()
        session["user"] = username
        return jsonify(success=True)
    except sqlite3.IntegrityError:
        return jsonify(success=False, message="Username already exists.")
    finally:
        conn.close()

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and check_password_hash(row[0], password):
        session["user"] = username
        return jsonify(success=True)
    
    return jsonify(success=False, message="Invalid username or password.")

@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify(success=True)

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify(state=device_state, lcd_text=lcd_text)

@app.route("/api/device", methods=["POST"])
def control_device():
    global device_state, lcd_text
    data = request.get_json(silent=True) or {}
    
    if "action" in data:
        device_state = data.get("action")
    if "lcd_text" in data:
        lcd_text = data.get("lcd_text")
        
    return jsonify(state=device_state, lcd_text=lcd_text)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
