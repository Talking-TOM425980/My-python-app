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
            max-width: 420px;
            padding: 20px;
        }

        /* Neon Glassmorphism Card */
        .card {
            background: rgba(15, 7, 26, 0.75);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 0, 128, 0.3);
            border-radius: 24px;
            padding: 32px 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6),
                        0 0 30px rgba(236, 72, 153, 0.2);
            text-align: center;
        }

        /* Vibrant Titles */
        .title {
            font-size: 32px;
            font-weight: 900;
            font-style: italic;
            text-transform: uppercase;
            letter-spacing: 2px;
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
            letter-spacing: 3px;
            margin-bottom: 24px;
            opacity: 0.9;
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
    </style>
</head>
<body>

    <div class="screen-container">
        <div class="card">
            <h1 class="title">Pi Control Panel</h1>
            <p class="subtitle">Live Presentation Remote System</p>
            
            <div class="lcd-display" id="lcd-screen">{{ lcd_data }}</div>

            <div id="status" class="status-badge status-{{ state }}">
                Device is {{ state }}
            </div>

            <div class="control-grid">
                <button class="btn btn-on" onclick="sendAction('on')">ON</button>
                <button class="btn btn-off" onclick="sendAction('off')">OFF</button>
            </div>
        </div>
    </div>

    <script>
        function sendAction(actionValue) {
            fetch('/api/device', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: actionValue })
            })
            .then(res => res.json())
            .then(data => {
                const statusDiv = document.getElementById('status');
                statusDiv.innerText = "Device is " + data.state;
                statusDiv.className = "status-badge " + (data.state === 'on' ? "status-on" : "status-off");
            })
            .catch(err => console.error("Error updating button state:", err));
        }

        setInterval(() => {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('lcd-screen').innerText = data.lcd_text;
                    const statusDiv = document.getElementById('status');
                    statusDiv.innerText = "Device is " + data.state;
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
