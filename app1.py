from flask import Flask, jsonify, request

app = Flask(__name__)
device_state = "off"


@app.get("/")
def home():
    return "Pi server is running!"


@app.post("/api/device")
def control_device():
    global device_state

    data = request.get_json(silent=True) or {}
    action = data.get("action")

    if action not in ("on", "off"):
        return jsonify(error="Choose on or off"), 400

    device_state = action

    # Later, add your hardware-control code here.

    return jsonify(state=device_state)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
