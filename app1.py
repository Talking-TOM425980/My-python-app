import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = "/tmp/database.db" if os.path.exists("/tmp") else "database.db"

# --- Embedded Biodiversity Presentation Theme Templates ---

SETUP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Fairview Biodiversity - System Configuration</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1b3b2b; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; color: #1b3b2b; }
        .card { background: #f4f0e6; padding: 45px 35px; border-radius: 20px; border: 2px solid #2d6a4f; width: 400px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        h2 { margin: 0 0 10px 0; font-size: 26px; text-transform: uppercase; color: #1b3b2b; letter-spacing: 1px; }
        p.subtitle { color: #405d52; font-size: 14px; margin-bottom: 25px; }
        input { width: 100%; padding: 14px; margin: 10px 0; background: #ffffff; border: 1px solid #2d6a4f; border-radius: 10px; color: #1b3b2b; font-size: 15px; outline: none; text-align: center; }
        button { width: 100%; padding: 14px; margin-top: 20px; background: #2d6a4f; color: #f4f0e6; border: none; border-radius: 10px; font-weight: 700; text-transform: uppercase; font-size: 14px; letter-spacing: 1px; cursor: pointer; transition: background 0.3s; }
        button:hover { background: #1b3b2b; }
        .error-msg { background: rgba(217, 4, 41, 0.1); color: #d90429; padding: 10px; border-radius: 8px; margin-bottom: 15px; font-size: 13px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🌿 Fairview Biodiversity</h2>
        <p class="subtitle">Enter a designation for your automated prototype system.</p>
        {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
        <form method="POST" action="/setup-system">
            <input type="text" name="system_name" placeholder="e.g., Prototype Alpha" required autocomplete="off"><br>
            <button type="submit">Initialize Prototype</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Fairview Biodiversity - Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1b3b2b; color: #1b3b2b; min-height: 100vh; margin: 0; padding: 25px; }
        
        .header { display: flex; justify-content: space-between; align-items: center; background: #f4f0e6; padding: 20px 30px; border-radius: 16px; border: 2px solid #2d6a4f; max-width: 950px; margin: 0 auto 25px auto; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .header h2 { margin: 0; font-size: 18px; font-weight: 700; color: #1b3b2b; }
        .header h2 span { color: #2d6a4f; }

        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; max-width: 950px; margin: 0 auto; }
        
        .action-card { background: #f4f0e6; border: 2px solid #2d6a4f; border-radius: 16px; padding: 25px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: transform 0.2s; }
        .action-title { font-size: 18px; font-weight: 700; color: #2d6a4f; margin-bottom: 8px; }
        .action-desc { font-size: 13px; color: #405d52; line-height: 1.5; margin-bottom: 20px; flex-grow: 1; }

        .btn-action { width: 100%; padding: 14px; border-radius: 10px; border: none; font-size: 14px; font-weight: 700; text-transform: uppercase; cursor: pointer; transition: background 0.3s; letter-spacing: 0.5px; }
        .btn-motor { background: #2d6a4f; color: #f4f0e6; }
        .btn-motor:hover { background: #1b3b2b; }
        .btn-power { background: #d90429; color: #ffffff; }
        .btn-power:hover { background: #b50322; }
        .btn-live { background: #405d52; color: #f4f0e6; }
        .btn-live:hover { background: #2d6a4f; }

        .full-card { grid-column: 1 / -1; background: #f4f0e6; border: 2px solid #2d6a4f; border-radius: 16px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .telemetry-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-top: 15px; }
        .telemetric-box { background: #ffffff; border: 1px solid #b7c4bc; border-radius: 12px; padding: 15px 20px; display: flex; flex-direction: column; gap: 8px; }
        .telemetric-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #405d52; font-weight: 700; }
        .telemetric-value { font-size: 20px; font-weight: 700; color: #1b3b2b; }
        
        .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: 700; text-transform: uppercase; font-size: 12px; }
        .on { background-color: rgba(45, 106, 79, 0.15); color: #2d6a4f; border: 1px solid #2d6a4f; }
        .off { background-color: rgba(217, 4, 41, 0.15); color: #d90429; border: 1px solid #d90429; }

        .lcd-container { margin-top: 15px; background: #1b3b2b; color: #52b788; padding: 18px; border-radius: 12px; border: 1px solid #2d6a4f; font-family: 'Courier New', Courier, monospace; font-size: 14px; white-space: pre-wrap; }

        .custom-group { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .custom-input-box { display: flex; flex-direction: column; gap: 5px; }
        .custom-input-box label { font-size: 12px; color: #405d52; text-transform: uppercase; font-weight: 700; }
        select, input[type="text"] { background: #ffffff; border: 1px solid #2d6a4f; border-radius: 8px; padding: 10px; color: #1b3b2b; outline: none; font-size: 14px; }
        
        .reconfigure-btn { color: #f4f0e6; background: #405d52; text-decoration: none; font-weight: 600; padding: 8px 16px; border-radius: 8px; font-size: 13px; transition: background 0.2s; }
        .reconfigure-btn:hover { background: #2d6a4f; }
    </style>
    <script>
        let systemName = "{{ system_name }}";
        let refreshInterval = 2000;
        let timerId = null;

        async function fetchStatus() {
            try {
                let response = await fetch('/api/status');
                let data = await response.json();
                
                let stateElem = document.getElementById('state');
                let isConnected = !data.lcd_text.includes("System Initializing") && !data.lcd_text.includes("Waiting for Raspberry Pi connection");
                
                stateElem.innerText = data.state;
                stateElem.className = 'status-badge ' + (data.state.toLowerCase() === 'on' ? 'on' : 'off');
                
                document.getElementById('soil-val').innerText = (data.soil_moisture !== undefined ? data.soil_moisture.toFixed(4) : "0.0000");
                document.getElementById('temp-val').innerText = (data.temperature !== undefined ? data.temperature.toFixed(1) + " °C" : "-- °C");
                
                let humidMatch = data.lcd_text.match(/Air Humid:\s*([0-9.]+)/);
                document.getElementById('humid-val').innerText = humidMatch ? humidMatch[1] + "% RH" : "-- % RH";

                document.getElementById('header-title').innerHTML = `Prototype System: <span id="disp-sys-name">${systemName}</span>`;
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
                alert("🌿 Watering cycle complete!");
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
            fetchStatus();
            timerId = setInterval(fetchStatus, refreshInterval);
        };
    </script>
</head>
<body>
    <div class="header">
        <h2 id="header-title">Prototype System: <span id="disp-sys-name">{{ system_name }}</span></h2>
        <div><a href="/setup-system" class="reconfigure-btn">⚙️ Configure Name</a></div>
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
                <div class="action-desc">Toggle telemetry feed view showing real-time sensor and LCD feedback.</div>
            </div>
            <button onclick="toggleLiveTelemetry()" class="btn-action btn-live">Toggle Status Feed</button>
        </div>

        <div id="telemetry-section" class="full-card">
            <h3 style="color:#2d6a4f; margin-top:0; margin-bottom: 5px;">Live Telemetry & Diagnostics</h3>
            <p style="color: #405d52; font-size: 13px; margin-top: 0;">Real-time independent status cards updating directly from your hardware.</p>
            
            <div class="telemetry-grid">
                <div class="telemetric-box">
                    <span class="telemetric-label">System State</span>
                    <div><span id="state" class="status-badge off">Loading...</span></div>
                </div>
                <div class="telemetric-box">
                    <span class="telemetric-label">Soil Moisture</span>
                    <span id="soil-val" class="telemetric-value">0.0000</span>
                </div>
                <div class="telemetric-box">
                    <span class="telemetric-label">Temperature</span>
                    <span id="temp-val" class="telemetric-value">-- °C</span>
                </div>
                <div class="telemetric-box">
                    <span class="telemetric-label">Air Humidity</span>
                    <span id="humid-val" class="telemetric-value">-- % RH</span>
                </div>
            </div>

            <h4 style="color:#2d6a4f; margin-top: 25px; margin-bottom: 10px;">Hardware LCD Feed Output:</h4>
            <div id="lcd" class="lcd-container">Connecting to hardware feed...</div>
        </div>

        <div class="full-card">
            <h3 style="color:#2d6a4f; margin-top:0;">⚙️ System Customization</h3>
            <div class="custom-group">
                <div class="custom-input-box">
                    <label>Rename Prototype</label>
                    <input type="text" id="robot_name_input" placeholder="{{ system_name }}">
                    <button onclick="updateRobotName()" style="margin-top:5px; padding:8px; background:#2d6a4f; color:#f4f0e6; border:none; border-radius:6px; font-weight:700; cursor:pointer;">Update</button>
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
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                water_system_name TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                device_state TEXT NOT NULL,
                soil_moisture REAL DEFAULT 0.0,
                temperature REAL DEFAULT 0.0,
                lcd_text TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            INSERT OR IGNORE INTO system_config (id, water_system_name) 
            VALUES (1, 'Biodiversity Prototype Alpha')
        ''')

        cursor.execute('''
            INSERT OR IGNORE INTO telemetry (id, device_state, soil_moisture, temperature, lcd_text) 
            VALUES (1, 'off', 0.0, 0.0, 'System Initializing...\nWaiting for Raspberry Pi connection...')
        ''')

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database Initialization Error: {e}")


init_db()


# --- Routes (No Login / Register Required) ---

@app.route("/")
def home():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT water_system_name FROM system_config WHERE id = 1")
        config = cursor.fetchone()
        conn.close()

        if not config or not config["water_system_name"]:
            return redirect(url_for("setup_system"))
            
        return redirect(url_for("dashboard"))
    except Exception:
        return redirect(url_for("setup_system"))


@app.route("/setup-system", methods=["GET", "POST"])
def setup_system():
    if request.method == "POST":
        system_name = request.form.get("system_name")
        if not system_name:
            return render_template_string(SETUP_HTML, error="Water system name is required")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE system_config SET water_system_name = ? WHERE id = 1", (system_name,))
            conn.commit()
            conn.close()
            return redirect(url_for("dashboard"))
        except Exception as e:
            return render_template_string(SETUP_HTML, error=f"Database Error: {e}")

    return render_template_string(SETUP_HTML, error=None)


@app.route("/dashboard")
def dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT water_system_name FROM system_config WHERE id = 1")
        config = cursor.fetchone()
        conn.close()

        if not config or not config["water_system_name"]:
            return redirect(url_for("setup_system"))
            
        return render_template_string(DASHBOARD_HTML, system_name=config["water_system_name"])
    except Exception:
        return redirect(url_for("setup_system"))


# --- Real-Time API Routes ---

@app.route("/api/status", methods=["GET"])
def get_status():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT device_state, soil_moisture, temperature, lcd_text FROM telemetry WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify(state=row["device_state"], soil_moisture=row["soil_moisture"], temperature=row["temperature"], lcd_text=row["lcd_text"])
        return jsonify(state="off", soil_moisture=0.0, temperature=0.0, lcd_text="System Initializing...")
    except Exception as e:
        return jsonify(state="off", soil_moisture=0.0, temperature=0.0, lcd_text=f"Database error: {e}"), 500


@app.route("/api/device", methods=["POST"])
def control_device():
    data = request.get_json(silent=True) or {}
    new_state = data.get("action")
    new_soil = data.get("soil")
    new_temp = data.get("temperature")
    new_lcd = data.get("lcd_text")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if new_state and new_soil is not None and new_temp is not None and new_lcd:
            cursor.execute("UPDATE telemetry SET device_state = ?, soil_moisture = ?, temperature = ?, lcd_text = ? WHERE id = 1", (new_state, new_soil, new_temp, new_lcd))
        elif new_state and new_soil is not None and new_lcd:
            cursor.execute("UPDATE telemetry SET device_state = ?, soil_moisture = ?, lcd_text = ? WHERE id = 1", (new_state, new_soil, new_lcd))
        elif new_state and new_lcd:
            cursor.execute("UPDATE telemetry SET device_state = ?, lcd_text = ? WHERE id = 1", (new_state, new_lcd))
        elif new_state:
            cursor.execute("UPDATE telemetry SET device_state = ? WHERE id = 1", (new_state,))
        elif new_soil is not None and new_temp is not None and new_lcd:
            cursor.execute("UPDATE telemetry SET soil_moisture = ?, temperature = ?, lcd_text = ? WHERE id = 1", (new_soil, new_temp, new_lcd))
        elif new_lcd:
            cursor.execute("UPDATE telemetry SET lcd_text = ? WHERE id = 1", (new_lcd,))

        conn.commit()

        cursor.execute("SELECT device_state, soil_moisture, temperature, lcd_text FROM telemetry WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify(state=row["device_state"], soil_moisture=row["soil_moisture"], temperature=row["temperature"], lcd_text=row["lcd_text"])
        return jsonify(state=new_state or "off", soil_moisture=new_soil or 0.0, temperature=new_temp or 0.0, lcd_text=new_lcd or "")
    except Exception as e:
        return jsonify(error=str(e)), 500


# --- Server Start ---

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
