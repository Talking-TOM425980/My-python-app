from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
device_state = "off"
lcd_text = "System Initializing...\nWaiting for Raspberry Pi connection..."

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pi Controller Dash</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f4f6f9;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .card {
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            text-align: center;
            width: 340px;
        }
        h1 { color: #1e293b; font-size: 24px; margin-bottom: 8px; }
        p { color: #64748b; margin-bottom: 24px; }
        
        .lcd-display {
            background-color: #0f172a;
            color: #38bdf8;
            font-family: "Courier New", Courier, monospace;
            padding: 18px;
            border-radius: 10px;
            text-align: left;
            margin-bottom: 24px;
            border: 3px solid #475569;
            font-size: 14px;
            font-weight: bold;
            min-height: 70px;
            line-height: 1.6;
            white-space: pre-wrap;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.5);
        }
        
        .status-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            margin-bottom: 24px;
        }
        .status-on { background-color: #dcfce7; color: #15803d; }
        .status-off { background-color: #fee2e2; color: #b91c1c; }
        .btn-container { display: flex; gap: 12px; justify-content: center; }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100px;
            transition: opacity 0.2s;
        }
        .btn-on { background-color: #22c55e; color: white; }
        .btn-off { background-color: #ef4444; color: white; }
        button:hover { opacity: 0.9; }
    </style>
</head>
<body>

    <div class="card">
        <h1>Pi Control Panel</h1>
        <p>Live Presentation Remote System</p>
        
        <div class="lcd-display" id="lcd-screen">{{ lcd_data }}</div>

        <div id="status" class="status-badge status-{{ state }}">
            Device is {{ state }}
        </div>

        <div class="btn-container">
            <button class="btn-on" onclick="sendAction('on')">ON</button>
            <button class="btn-off" onclick="sendAction('off')">OFF</button>
        </div>
    </div>

    <script>
        // FIXED: Explicitly defining the sendAction function the buttons are clicking for
        function sendAction(actionValue) {
            fetch('/api/device', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: actionValue })
            })
            .then(res => res.json())
            .then(data => {
                // Update the button state instantly on the UI
                const statusDiv = document.getElementById('status');
                statusDiv.innerText = "Device is " + data.state;
                statusDiv.className = data.state === 'on' ? "status-badge status-on" : "status-badge status-off";
            })
            .catch(err => console.error("Error updating button state:", err));
        }

        // Automatically fetches live data updates from your Pi every 1 second
        setInterval(() => {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('lcd-screen').innerText = data.lcd_text;
                    // Only update the state badge if the user isn't actively clicking
                    const statusDiv = document.getElementById('status');
                    statusDiv.innerText = "Device is " + data.state;
                    statusDiv.className = data.state === 'on' ? "status-badge status-on" : "status-badge status-off";
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
