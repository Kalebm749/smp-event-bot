import subprocess
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone
from functools import wraps
import pytz
import platform

load_dotenv()
PASSWORD = os.getenv("ADMIN_PASSWORD")

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Paths
EVENTS_JSON_PATH = os.path.join(".", "events", "events_json")
CALENDAR_FILE = os.path.join(".", "events", "events_calendar", "event_calendar.json")
LOGS_PATH = os.path.join(".", "logs")

def start_event_handler():
    try:
        if not is_event_handler_running():
            if platform.system() == "Windows":
                subprocess.Popen(["python", "./src/event_handler.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["python3", "./src/event_handler.py"])
            return True
        return False
    except Exception as e:
        print("Error starting event handler:", e)
        return False

def stop_event_handler():
    try:
        if is_event_handler_running():
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "python.exe"])
            else:
                subprocess.run(["pkill", "-f", "event_handler.py"])
            return True
        return False
    except Exception as e:
        print("Error stopping event handler:", e)
        return False

def is_event_handler_running():
    """
    Check if 'event_handler.py' is running.
    Works on Linux and Windows.
    """
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["tasklist"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return "event_handler.py" in result.stdout
        else:  # Linux
            result = subprocess.run(
                ["pgrep", "-f", "event_handler.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            return result.returncode == 0
    except Exception as e:
        print("Error checking event handler:", e)
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# --- Load calendar ---
def load_calendar():
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, "r") as f:
            return json.load(f)
    return []

# --- Load event JSON files ---
def load_event_files():
    if os.path.exists(EVENTS_JSON_PATH):
        return [f for f in os.listdir(EVENTS_JSON_PATH) if f.endswith(".json")]
    return []

# --- Load logs ---
def load_logs():
    if os.path.exists(LOGS_PATH):
        return [f for f in os.listdir(LOGS_PATH) if f.endswith(".txt") or f.endswith(".json")]
    return []

# --- Helper to determine event status ---
def get_event_status(event):
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(event["start"])
    end = datetime.fromisoformat(event["end"])
    if start > now:
        return "future"
    elif start <= now <= end:
        return "ongoing"
    else:
        return "past"

# --- Routes ---

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        print(f"Entered password: {repr(password)}")
        print(f"Expected password: {repr(PASSWORD)}")
        if password == PASSWORD:
            session["logged_in"] = True
            print("Login successful")
            return redirect(url_for("index"))
        else:
            print("Login failed")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/api/calendar")
@login_required
def api_calendar():
    events = load_calendar()
    for e in events:
        e["status"] = get_event_status(e)
    return jsonify(events)

@app.route("/api/event_handler/start", methods=["POST"])
@login_required
def api_start_event_handler():
    success = start_event_handler()
    return jsonify({"success": success, "status": "Running" if is_event_handler_running() else "Not Running"})

@app.route("/event_monitor")
@login_required
def event_monitor():
    return render_template("event_monitor.html")

@app.route("/api/event_handler_status")
@login_required
def api_event_handler_status():
    running = is_event_handler_running()
    return jsonify({
        "status": "Running" if running else "Not Running"
    })

@app.route("/api/event_handler/stop", methods=["POST"])
@login_required
def api_stop_event_handler():
    success = stop_event_handler()
    return jsonify({"success": success, "status": "Running" if is_event_handler_running() else "Not Running"})

@app.route("/api/event_files")
@login_required
def api_event_files():
    files = load_event_files()
    return jsonify(files)

@app.route("/api/logs")
@login_required
def api_logs():
    files = load_logs()
    return jsonify(files)

@app.route("/api/log_content/<filename>")
@login_required
def api_log_content(filename):
    path = os.path.join(LOGS_PATH, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return "", 404

@app.route("/api/event_json_content/<filename>")
@login_required
def api_event_json_content(filename):
    path = os.path.join(EVENTS_JSON_PATH, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            # Return pretty-printed JSON
            data = json.load(f)
            return json.dumps(data, indent=2)
    return "", 404

@app.route("/api/event_handler/logs")
def event_handler_logs():
    log_path = os.path.join("logs", "handler_logs.txt")

    def generate():
        with open(log_path, "r") as f:
            lines = f.readlines()
            # Start with last 20 lines
            buffer = lines[-20:]
            yield "data: " + "\n".join(buffer) + "\n\n"

        # Tail the file in real time
        with open(log_path, "r") as f:
            f.seek(0, os.SEEK_END)  # move to end
            while True:
                line = f.readline()
                if line:
                    yield f"data: {line}\n\n"

    return Response(generate(), mimetype="text/event-stream")

@app.route("/create_event", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        # Extract form data
        name = request.form.get("name")
        description = request.form.get("description")
        event_json = request.form.get("event_json")
        timezone_str = request.form.get("timezone")

        # Extract combined hidden fields from JS
        start_str = request.form.get("start")
        end_str = request.form.get("end")

        # Validate timezone
        if not timezone_str or timezone_str not in pytz.all_timezones:
            return "Invalid timezone selected", 400
        tz = pytz.timezone(timezone_str)

        # Parse start and end
        try:
            start_local = datetime.strptime(start_str, "%Y-%m-%d %I:%M %p")
            end_local = datetime.strptime(end_str, "%Y-%m-%d %I:%M %p")
        except ValueError:
            return "Invalid date/time format. Use MM/DD/YYYY HH:MM AM/PM", 400

        # Localize to selected timezone and convert to UTC
        start_dt = tz.localize(start_local).astimezone(pytz.UTC)
        end_dt = tz.localize(end_local).astimezone(pytz.UTC)

        # Load calendar
        if os.path.exists(CALENDAR_FILE):
            with open(CALENDAR_FILE, "r") as f:
                calendar = json.load(f)
        else:
            calendar = []

        # Build event
        unique_event_name = f"{name.replace(' ','-')}-{start_dt.strftime('%m-%d-%Y')}"
        event = {
            "unique_event_name": unique_event_name,
            "name": name,
            "event_json": event_json,
            "description": description,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "24_hour_sent": False,
            "30_minute_sent": False,
            "event_start_sent": False,
            "event_over_sent": False,
            "event_in_progress": False,
            "last_scoreboard_time": "",
            "event_started": False,
            "event_over": False
        }

        calendar.append(event)
        with open(CALENDAR_FILE, "w") as f:
            json.dump(calendar, f, indent=2)

        return redirect(url_for("index"))

    # GET request
    event_files = [f for f in os.listdir(EVENTS_JSON_PATH) if f.endswith(".json")]
    return render_template("create_event.html", event_files=event_files)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

