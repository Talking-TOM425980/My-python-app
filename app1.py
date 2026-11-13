import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = "/tmp/database.db" if os.path.exists("/tmp") else "database.db"

# --- Embedded HTML Templates ---

WELCOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Plant - Automated Ecosystem</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #04100c 0%, #0c241c 50%, #020705 100%); margin: 0; min-height: 100vh; color: #ffffff; display: flex; flex-direction: column; }
        nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 50px; background: rgba(10, 26, 20, 0.7); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(0, 255, 136, 0.15); }
        .logo { font-size: 20px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; color: #00ff88; text-decoration: none; display: flex; align-items: center; gap: 10px; }
        .logo span { color: #00f2fe; }
        .nav-auth { display: flex; gap: 15px; align-items: center; }
        .nav-login { color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; padding: 8px 16px; }
        .nav-signup { background: #ffffff; color: #04100c; text-decoration: none; font-size: 14px; font-weight: 700; padding: 9px 18px; border-radius: 6px; }
        .hero-container { flex: 1; display: flex; align-items: center; justify-content: space-between; max-width: 1200px; margin: 0 auto; padding: 60px 50px; width: 100%; gap: 50px; }
        .hero-content { flex: 1; max-width: 600px; }
        h1 { font-size: 52px; line-height: 1.1; margin: 0 0 20px 0; font-weight: 800; color: #ffffff; }
        h1 span { background: linear-gradient(90deg, #00ff88, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .hero-desc { font-size: 17px; line-height: 1.6; color: #9fb3ab; margin-bottom: 35px; }
        .btn-primary { background: linear-gradient(90deg, #00ff88, #00b0ff); color: #04100c; padding: 14px 28px; border-radius: 8px; font-weight: 700; text-decoration: none; text-transform: uppercase; font-size: 14px; }
    </style>
</head>
<body>
    <nav>
        <a href="/" class="logo">🌿 Smart <span>Plant</span></a>
        <div class="nav-auth">
            <a href="/login" class="nav-login">Login</a>
            <a href="/register" class="nav-signup">Sign Up</a>
        </div>
    </nav>
    <div class="hero-container">
        <div class="hero-content">
            <h1>Automated care for your <span>plants & systems</span></h1>
            <p class="hero-desc">Smart Plant intelligently waters your greenery based on live humidity sensor thresholds.</p>
            <a href="/register" class="btn-primary">Get Started</a>
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
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #04100c 0%, #0c241c 50%, #020705 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; color: #ffffff; }
        .card { background: rgba(10, 26, 20, 0.85); backdrop-filter: blur(14px); padding: 40px 30px; border-radius: 14px; border: 1px solid rgba(0, 255, 136, 0.4); width: 350px; text-align: center; }
        h2 { margin: 0; font-size: 28px; text-transform: uppercase; color: #00ff88; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: rgba(4, 16, 12, 0.8); border: 1px solid rgba(0, 242, 254, 0.3); border-radius: 8px; color: #ffffff; outline: none; }
        button { width: 100%; padding: 12px; margin-top: 15px; background: linear-gradient(90deg, #00ff88, #00b0ff); color: #04100c; border: none; border-radius: 8px; font-weight: 700; text-transform: uppercase; cursor: pointer; }
        .error-msg { background: rgba(255, 0, 85, 0.15); color: #ff3366; padding: 10px; border-radius: 8px; margin-bottom: 15px; }
        p { margin-top: 25px; font-size: 13px; color: #8fa39b; }
        a { color: #00f2fe; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Plant Net</h2>
        {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Sign In</button>
        </form>
        <p>New ecosystem? <a href="/register">Register</a></p>
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
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #04100c 0%, #0c241c 50%, #020705 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; color: #ffffff; }
        .card { background: rgba(10, 26, 20, 0.85); backdrop-filter: blur(14px); padding: 40px 30px; border-radius: 14px; border: 1px solid rgba(0, 242, 254, 0.4); width: 350px; text-align: center; }
        h2 { margin: 0 0 25px 0; font-size: 26px; text-transform: uppercase; color: #00f2fe; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: rgba(4, 16, 12, 0.8); border: 1px solid rgba(0, 255, 136, 0.3); border-radius: 8px; color: #ffffff; outline: none; }
        button { width: 100%; padding: 12px; margin-top: 15px; background: linear-gradient(90deg, #00f2fe, #00ff88); color: #04100c; border: none; border-radius: 8px; font-weight: 700; text-transform: uppercase; cursor: pointer; }
        .error-msg { background: rgba(255, 0, 85, 0.15); color: #ff3366; padding: 10px; border-radius: 8px; margin-bottom: 15px; }
        p { margin-top: 25px; font-size: 13px; color: #8fa39b; }
        a { color: #00ff88; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Join Network</h2>
        {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
        <form method="POST" action="/register">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Register</button>
        </form>
        <p>Already registered? <a href="/login">Login</a></p>
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
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #04100c 0%, #0c241c 50%, #020705 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; color: #ffffff; }
        .card { background: rgba(10, 26, 20, 0.85); backdrop-filter: blur(14px); padding: 40px 30px; border-radius: 14px; border: 1px solid rgba(0, 255, 136, 0.4); width: 380px; text-align: center; }
        h2 { margin: 0 0 10px 0; font-size: 24px; text-transform: uppercase; color: #00ff88; }
        p.subtitle { color: #8fa39b; font-size: 13px; margin-bottom: 25px; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: rgba(4, 16, 12, 0.8); border: 1px solid rgba(0, 242, 254, 0.3); border-radius: 8px; color: #ffffff; outline: none; }
        button { width: 100%; padding: 12px; margin-top: 15px; background: linear-gradient(90deg, #00ff88, #00b0ff); color: #04100c; border: none; border-radius: 8px; font-weight: 700; text-transform: uppercase; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h2>System Configuration</h2>
        <p class="subtitle">Assign a designation to your automated water system.</p>
        {% if error %}<div style="color:#ff3366;">{{ error }}</div>{% endif %}
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
        body.theme-emerald { background: linear-gradient(135deg, #04100c 0%, #0c241c 50%, #020705 100%); color: #ffffff; }
        body.theme-cyan { background: linear-gradient(135deg, #081d28 0%, #0b374d 50%, #031018 100%); color: #e0f7fc; }
        body.theme-oled { background: #000000; color: #00ff88; }

        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; min-height: 100vh; margin: 0; padding: 25px; transition: all 0.4s ease; }
        .header { display: flex; justify-content: space-between; align-items: center; background: rgba(10, 26, 20, 0.85); backdrop-filter: blur(14px); padding: 20px 30px; border-radius: 14px; border: 1px solid rgba(0, 255, 136, 0.3); max-width: 950px; margin: 0 auto 25px auto; }
        .header h2 { margin: 0; font-size: 18px; font-weight: 600; }
        .header h2 span { color: #00ff88; }

        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; max-width: 950px; margin: 0 auto; }
        .action-card { background: rgba(10, 26, 20, 0.85); backdrop-filter: blur(14px); border: 1px solid rgba(0, 242, 254, 0.3); border-radius: 14px; padding: 25px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.3s ease; }
        .action-title { font-size: 18px; font-weight: 700; color: #00ff88; margin-bottom: 8px; }
        .action-desc { font-size: 13px; color: #a0b5ad; line-height: 1.5; margin-bottom: 20px; flex-grow: 1; }

        .btn-action { width: 100%; padding: 14px; border-radius: 8px; border: none; font-size: 14px; font-weight: 700; text-transform: uppercase; cursor: pointer; transition: all 0.3s ease; }
        .btn-motor { background: linear-gradient(90deg, #00b0ff, #00ff88); color: #04100c; }
        .btn-power { background: linear-gradient(90deg, #ff3366, #ff6600); color: #ffffff; }
        .btn-live { background: linear-gradient(90deg, #00f2fe, #00ff88); color: #04100c; }

        /* Professional Telemetry Layout styling */
        .full-card { grid-column: 1 / -1; background: rgba(10, 26, 20, 0.85); backdrop-filter: blur(14px); border: 1px solid rgba(0, 255, 136, 0.3); border-radius: 14px; padding: 25px; }
        .telemetry-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .telemetric-box { background: rgba(4, 16, 12, 0.9); border: 1px solid rgba(0, 242, 254, 0.25); border-radius: 10px; padding: 15px 20px; display: flex; flex-direction: column; gap: 8px; }
        .telemetric-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #00f2fe; font-weight: 700; }
        .telemetric-value { font-size: 20px; font-weight: 700; color: #ffffff; font-family: 'Segoe UI', Tahoma, sans-serif; }
        
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: 700; text-transform: uppercase; font-size: 12px; }
        .on { background-color: rgba(0, 255, 136, 0.15); color: #00ff88; border: 1px solid #00ff88; }
        .off { background-color: rgba(255, 51, 102, 0.15); color: #ff3366; border: 1px solid #ff3366; }

        .lcd-container { margin-top: 15px; background: #020705; color: #00ff88; padding: 18px; border-radius: 10px; border: 1px solid rgba(0, 255, 136, 0.25); font-family: 'Courier New', Courier, monospace; font-size: 14px; white-space: pre-wrap; }

        .custom-group { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .custom-input-box { display: flex; flex-direction: column; gap: 5px; }
        .custom-input-box label { font-size: 12px; color: #00f2fe; text-transform: uppercase; font-weight: 700; }
        select, input[type="text"] { background: rgba(4, 16, 12, 0.8); border: 1px solid rgba(0, 242, 254, 0.3); border-radius: 8px; padding: 10px; color: #ffffff; outline: none; }
        .logout-btn { color: #ff3366; text-decoration: none; font-weight: 600; border: 1px solid rgba(255, 51, 102, 0.4); padding: 6px 14px; border-radius: 8px; font-size: 13px; }
        .logout-btn:hover { background: #ff3366; color: #04100c; }
    </style>
    <script>
        let username = "{{ username }}";
        let systemName = "{{ system_name }}";
        let refreshInterval = 2000;
        let timerId = null;

        async function fetchStatus() {
            try {
                let response = await fetch('/api/status');
                let data = await response.json();
                
                let stateElem = document.getElementById('state');
                let isConnected = !data.lcd_text.includes("System Initializing") && !data.lcd_text.includes("Waiting for Raspberry Pi connection");
                
                // Update Badge State
                stateElem.innerText = data.state;
                stateElem.className = 'status-badge ' + (data.state.toLowerCase() === 'on' ? 'on' : 'off');
                
                // Update Independent Telemetry Cards
                document.getElementById('soil-val').innerText = (data.soil_moisture !== undefined ? data.soil_moisture.toFixed(4) : "0.0000");
                
                // Extract Air Humidity from LCD text or handle safely
                let humidMatch = data.lcd_text.match(/Air Humid:\s*([0-9.]+)/);
                document.getElementById('humid-val').innerText = humidMatch ? humidMatch[1] + "% RH" : "Active / Live";

                document.getElementById('header-title').innerHTML = isConnected 
                    ? `Hello ${username}, <span id="disp-sys-name">${systemName}</span> is ONLINE`
                    : `Hello ${username}, <span id="disp-sys-name">${systemName}</span> is awaiting connection`;
                
                document.getElementById('lcd').innerText = data.lcd_text;
            } catch (err) {
                console.error("Error fetching status:", err);
            }
        }

        async function triggerWaterMotor() {
            let duration = prompt("How many seconds would you like to hydrate your soil?", "5");
            if (duration && !isNaN(duration) && parseInt(duration) > 0) {
                let seconds = parseInt(duration);
                
                await fetch('/api/device', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'ON', lcd_text: `[WEB]: Motor running for up to ${seconds}s (Target: 0.4)...` })
                });

                let currentSoil = 0.0;
                for (let i = 0; i < seconds; i++) {
                    await new Promise(r => setTimeout(r, 1000));
                    let res = await fetch('/api/status');
                    let data = await res.json();
                    currentSoil = data.soil_moisture || 0.0;
                    if (currentSoil >= 0.4) break;
                }

                if (currentSoil < 0.4) {
                    let keepGoing = confirm(`Soil is at ${currentSoil.toFixed(4)} (below 0.4 target). Do you want to continue hydrating until it reaches 0.4?`);
                    if (keepGoing) {
                        alert("Watering resumed until soil moisture reaches 0.4...");
                        await fetch('/api/device', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ action: 'ON', lcd_text: `[WEB]: Resumed until soil reaches 0.4...` })
                        });

                        while (true) {
                            await new Promise(r => setTimeout(r, 1000));
                            let checkRes = await fetch('/api/status');
                            let checkData = await checkRes.json();
                            if ((checkData.soil_moisture || 0.0) >= 0.4) break;
                        }
                    }
                }

                await fetch('/api/device', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'OFF', lcd_text: 'Hydration cycle finished.' })
                });

                fetchStatus();
                alert("💦 Watering cycle complete!");
            }
        }

        async function toggleSystemPower() {
            let stateElem = document.getElementById('state');
            let newState = (stateElem.innerText.toLowerCase() === 'on') ? 'OFF' : 'ON';
            await fetch('/api/device', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: newState, lcd_text: `[POWER]: Toggled to ${newState}` })
            });
            fetchStatus();
        }

        function toggleLiveTelemetry() {
            let telemetrySection = document.getElementById('telemetry-section');
            telemetrySection.style.display = telemetrySection.style.display === 'none' ? 'block' : 'none';
        }

        function changeTheme(themeName) {
            document.body.className = 'theme-' + themeName;
            localStorage.setItem('user_theme', themeName);
        }

        function updateRobotName() {
            let inputName = document.getElementById('robot_name_input').value.trim();
            if (inputName) {
                systemName = inputName;
                document.getElementById('disp-sys-name').innerText = systemName;
                alert(`System name updated to: ${systemName}`);
            }
        }

        function updatePollRate(val) {
            refreshInterval = parseInt(val);
            if (timerId) clearInterval(timerId);
            timerId = setInterval(fetchStatus, refreshInterval);
        }

        window.onload = function() {
            let savedTheme = localStorage.getItem('user_theme') || 'emerald';
            changeTheme(savedTheme);
            document.getElementById('theme_select').value = savedTheme;
            fetchStatus();
            timerId = setInterval(fetchStatus, refreshInterval);
        };
    </script>
</head>
<body>
    <div class="header">
        <h2 id="header-title">Hello {{ username }}, <span id="disp-sys-name">{{ system_name }}</span></h2>
        <div><a href="/logout" class="logout-btn">Logout</a></div>
    </div>
    
    <div class="dashboard-grid">
        <div class="action-card">
            <div>
                <div class="action-title">💧 Hydrate Soil (Motor)</div>
                <div class="action-desc">Engages water motor with custom duration and 0.4 moisture target limits.</div>
            </div>
            <button onclick="triggerWaterMotor()" class="btn-action btn-motor">Start Motor</button>
        </div>

        <div class="action-card">
            <div>
                <div class="action-title">⚡ System On/Off</div>
                <div class="action-desc">Master power control for your remote water setup.</div>
            </div>
            <button onclick="toggleSystemPower()" class="btn-action btn-power">Toggle Power</button>
        </div>

        <div class="action-card">
            <div>
                <div class="action-title">📡 Live Feed Screen</div>
                <div class="action-desc">Open telemetry feed showing real-time sensor and LCD feedback.</div>
            </div>
            <button onclick="toggleLiveTelemetry()" class="btn-action btn-live">Watch Status Live</button>
        </div>

        <!-- Professional Independent Section Statuses Telemetry Card -->
        <div id="telemetry-section" class="full-card" style="display: none;">
            <h3 style="color:#00f2fe; margin-top:0; margin-bottom: 5px;">Live Telemetry & Diagnostics</h3>
            <p style="color: #a0b5ad; font-size: 13px; margin-top: 0;">Real-time independent status sections updating directly from your hardware.</p>
            
            <div class="telemetry-grid">
                <div class="telemetric-box">
                    <span class="telemetric-label">System State</span>
                    <div><span id="state" class="status-badge off">Loading...</span></div>
                </div>
                <div class="telemetric-box">
                    <span class="telemetric-label">Soil Moisture Ratio</span>
                    <span id="soil-val" class="telemetric-value">0.0000</span>
                </div>
                <div class="telemetric-box">
                    <span class="telemetric-label">Air Humidity</span>
                    <span id="humid-val" class="telemetric-value">-- % RH</span>
                </div>
            </div>

            <h4 style="color:#00ff88; margin-top: 25px; margin-bottom: 10px;">Hardware LCD Feed Output:</h4>
            <div id="lcd" class="lcd-container">Connecting to hardware feed...</div>
        </div>

        <div class="full-card">
            <h3 style="color:#00f2fe; margin-top:0;">⚙️ Customize Your System</h3>
            <div class="custom-group">
                <div class="custom-input-box">
                    <label>Background Theme</label>
                    <select id="theme_select" onchange="changeTheme(this.value)">
                        <option value="emerald">Emerald Cyber (Dark)</option>
                        <option value="cyan">Neon Cyan</option>
                        <option value="oled">Midnight OLED</option>
                    </select>
                </div>
                <div class="custom-input-box">
                    <label>Rename System</label>
                    <input type="text" id="robot_name_input" placeholder="{{ system_name }}">
                    <button onclick="updateRobotName()" style="margin-top:5px; padding:6px; background:#00ff88; color:#000; border:none; border-radius:6px; font-weight:700; cursor:pointer;">Update</button>
                </div>
                <div class="custom-input-box">
                    <label>Refresh Rate</label>
                    <select onchange="updatePollRate(this.value)">
                        <option value="1000">Fast (Every 1s)</option>
                        <option value="2000" selected>Normal (Every 2s)</option>
                        <option value="5000">Eco (Every 5s)</option>
                    </select>
                </div>
            </div>
        </div>
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
                soil_moisture REAL DEFAULT 0.0,
                lcd_text TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            INSERT OR IGNORE INTO telemetry (id, device_state, soil_moisture, lcd_text) 
            VALUES (1, 'off', 0.0, 'System Initializing...\nWaiting for Raspberry Pi connection...')
        ''')

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database Initialization Error: {e}")


init_db()


# --- Routes ---

@app.route("/")
def home():
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT device_state, soil_moisture, lcd_text FROM telemetry WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify(state=row["device_state"], soil_moisture=row["soil_moisture"], lcd_text=row["lcd_text"])
        return jsonify(state="off", soil_moisture=0.0, lcd_text="System Initializing...")
    except Exception as e:
        return jsonify(state="off", soil_moisture=0.0, lcd_text=f"Database error: {e}"), 500


@app.route("/api/device", methods=["POST"])
def control_device():
    data = request.get_json(silent=True) or {}
    new_state = data.get("action")
    new_soil = data.get("soil")
    new_lcd = data.get("lcd_text")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if new_state and new_soil is not None and new_lcd:
            cursor.execute("UPDATE telemetry SET device_state = ?, soil_moisture = ?, lcd_text = ? WHERE id = 1", (new_state, new_soil, new_lcd))
        elif new_state and new_lcd:
            cursor.execute("UPDATE telemetry SET device_state = ?, lcd_text = ? WHERE id = 1", (new_state, new_lcd))
        elif new_state:
            cursor.execute("UPDATE telemetry SET device_state = ? WHERE id = 1", (new_state,))
        elif new_soil is not None and new_lcd:
            cursor.execute("UPDATE telemetry SET soil_moisture = ?, lcd_text = ? WHERE id = 1", (new_soil, new_lcd))
        elif new_lcd:
            cursor.execute("UPDATE telemetry SET lcd_text = ? WHERE id = 1", (new_lcd,))

        conn.commit()

        cursor.execute("SELECT device_state, soil_moisture, lcd_text FROM telemetry WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify(state=row["device_state"], soil_moisture=row["soil_moisture"], lcd_text=row["lcd_text"])
        return jsonify(state=new_state or "off", soil_moisture=new_soil or 0.0, lcd_text=new_lcd or "")
    except Exception as e:
        return jsonify(error=str(e)), 500


# --- Server Start ---

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
