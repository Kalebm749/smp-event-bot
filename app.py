from flask import Flask, render_template, jsonify, request, redirect, url_for
import os
import json
from datetime import datetime, timezone
import pytz

app = Flask(__name__)

# Paths
EVENTS_JSON_PATH = os.path.join(".", "events", "events_json")
CALENDAR_FILE = os.path.join(".", "events", "events_calendar", "event_calendar.json")
LOGS_PATH = os.path.join(".", "logs")

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
def index():
    return render_template("index.html")

@app.route("/api/calendar")
def api_calendar():
    events = load_calendar()
    for e in events:
        e["status"] = get_event_status(e)
    return jsonify(events)

@app.route("/api/event_files")
def api_event_files():
    files = load_event_files()
    return jsonify(files)

@app.route("/api/logs")
def api_logs():
    files = load_logs()
    return jsonify(files)

@app.route("/api/log_content/<filename>")
def api_log_content(filename):
    path = os.path.join(LOGS_PATH, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return "", 404

@app.route("/api/event_json_content/<filename>")
def api_event_json_content(filename):
    path = os.path.join(EVENTS_JSON_PATH, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            # Return pretty-printed JSON
            data = json.load(f)
            return json.dumps(data, indent=2)
    return "", 404

@app.route("/create_event", methods=["GET", "POST"])
def create_event():
    if request.method == "POST":
        # Extract form data
        name = request.form.get("name")
        description = request.form.get("description")
        event_json = request.form.get("event_json")
        timezone_str = request.form.get("timezone")

        start_date = request.form.get("start_date")
        start_time = request.form.get("start_time")
        start_ampm = request.form.get("start_ampm")
        end_date = request.form.get("end_date")
        end_time = request.form.get("end_time")
        end_ampm = request.form.get("end_ampm")

        # Validate timezone
        if not timezone_str or timezone_str not in pytz.all_timezones:
            return "Invalid timezone selected", 400
        tz = pytz.timezone(timezone_str)

        # Combine date, time, AM/PM for parsing
        start_str = f"{start_date.replace('-', '/') } {start_time}{start_ampm}"
        end_str = f"{end_date.replace('-', '/') } {end_time}{end_ampm}"

        # Parse using strptime
        try:
            start_local = datetime.strptime(start_str, "%m/%d/%Y %I:%M%p")
            end_local = datetime.strptime(end_str, "%m/%d/%Y %I:%M%p")
        except ValueError:
            return "Invalid date/time format. Use MM/DD/YYYY HH:MM AM/PM", 400

        # Localize to selected timezone and convert to UTC
        start_dt = tz.localize(start_local).astimezone(pytz.UTC)
        end_dt = tz.localize(end_local).astimezone(pytz.UTC)

        # Load current calendar
        if os.path.exists(CALENDAR_FILE):
            with open(CALENDAR_FILE, "r") as f:
                calendar = json.load(f)
        else:
            calendar = []

        # Build event dict
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

        # Append and save
        calendar.append(event)
        with open(CALENDAR_FILE, "w") as f:
            json.dump(calendar, f, indent=2)

        return redirect(url_for("index"))

    # GET request: render the form
    event_files = [f for f in os.listdir(EVENTS_JSON_PATH) if f.endswith(".json")]
    return render_template("create_event.html", event_files=event_files)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

