import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # 1. Users table (Existing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # 2. Telemetry table (Added to persist LCD & device state)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            device_state TEXT NOT NULL,
            lcd_text TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO telemetry (id, device_state, lcd_text) 
        VALUES (1, 'off', 'System Initializing...\nWaiting for Raspberry Pi telemetry...')
    ''')
    
    conn.commit()
    conn.close()


init_db()


# --- Authentication Routes ---

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already exists!", 400
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session["user"] = username
            return redirect(url_for("dashboard"))

        return "Invalid Credentials", 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")


# --- Real-Time API Routes ---

@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns current device state and LCD screen text to the browser dashboard."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT device_state, lcd_text FROM telemetry WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify(state=row[0], lcd_text=row[1])
    return jsonify(state="off", lcd_text="System Initializing...")


@app.route("/api/device", methods=["POST"])
def control_device():
    """Receives live updates from the Raspberry Pi or dashboard commands."""
    data = request.get_json(silent=True) or {}
    new_state = data.get("action")
    new_lcd = data.get("lcd_text")

    conn = sqlite3.connect("database.db")
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

    return jsonify(state=row[0], lcd_text=row[1])


if __name__ == "__main__":
    app.run(debug=True)
