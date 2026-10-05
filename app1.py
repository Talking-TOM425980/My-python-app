from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
device_state = "off"

# Modern, clean HTML/CSS template embedded directly in Python
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
            width: 320px;
        }
        h1 {
            color: #1e293b;
            font-size: 24px;
            margin-bottom: 8px;
        }
        p {
            color: #64748b;
            margin-bottom: 24px;
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
        .btn-container {
            display: flex;
            gap: 12px;
            justify-content: center;
        }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s ease, opacity 0.2s;
            width: 100px;
        }
        button:active { transform: scale(0.96); }
        .btn-on { background-color: #22c55e; color: white; }
        .btn-off { background-color: #ef4444; color: white; }
        button:hover { opacity: 0.9; }
    </style>
</head>
<body>

    <div class="card">
        <h1>Pi Control Panel</h1>
        <p>Live Presentation Remote System</p>
        
        <!-- Status Indicator Display -->
        <div id="status" class="status-badge status-{{ state }}">
            Device is {{ state }}
        </div>

        <!-- Interactive Control Buttons -->
        <div class="btn-container">
            <button class="btn-on" onclick="sendAction('on')">ON</button>
            <button class="btn-off" onclick="sendAction('off')">OFF</button>
        </div>
    </div>

    <script>
        // JavaScript logic to update the state instantly without reloading the page
        function sendAction(actionValue) {
            fetch('/api/device', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: actionValue })
            })
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('status');
                statusDiv.innerText = "Device is " + data.state;
                
                if (data.state === 'on') {
                    statusDiv.className = "status-badge status-on";
                } else {
                    statusDiv.className = "status-badge status-off";
                }
            })
            .catch(err => console.error("Error communicating with backend:", err));
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    # Dynamically inject the current system state into our layout design
    return render_template_string(HTML_TEMPLATE, state=device_state)

@app.route("/api/device", methods=["POST"])
def control_device():
    global device_state
    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if action not in ["on", "off"]:
        return jsonify(error="Choose on or off"), 400

    device_state = action
    return jsonify(state=device_state)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
