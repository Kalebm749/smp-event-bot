#!/usr/bin/python3.12
import json
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
import re

# ====== CONFIG ======
load_dotenv()
CALENDAR_FILE = os.getenv("CALENDAR_FILE")
EVENTS_JSON_PATH = os.getenv("EVENTS_JSON_PATH")

# Common US & European timezones
TIMEZONES = [
    "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
    "Europe/London", "Europe/Berlin", "Europe/Paris", "Europe/Madrid",
    "Europe/Rome", "Europe/Amsterdam", "Europe/Stockholm", "Europe/Zurich"
]

# ====== HELPER FUNCTIONS ======
def split_camel_case(name):
    """Convert CamelCase to space-separated words"""
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', name)

def make_unique_event_name(name, start_date):
    """Create Event-Name-MM-DD-YYYY format"""
    date_str = start_date.strftime("%m-%d-%Y")
    name_hyphen = name.replace(" ", "-")
    return f"{name_hyphen}-{date_str}"

def load_calendar():
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, "r") as f:
            return json.load(f)
    return []

def save_calendar(calendar):
    with open(CALENDAR_FILE, "w") as f:
        json.dump(calendar, f, indent=2)

def select_timezone():
    print("Select your timezone from the list:")
    for i, tz in enumerate(TIMEZONES, 1):
        print(f"{i}. {tz}")
    while True:
        choice = input(f"Enter number (1-{len(TIMEZONES)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(TIMEZONES):
            return pytz.timezone(TIMEZONES[int(choice)-1])
        print("Invalid choice. Try again.")

def select_event_json():
    if not os.path.isdir(EVENTS_JSON_PATH):
        print(f"ERROR: {EVENTS_JSON_PATH} is not a directory.")
        exit(1)
    files = [f for f in os.listdir(EVENTS_JSON_PATH) if f.endswith(".json")]
    if not files:
        print(f"No JSON files found in {EVENTS_JSON_PATH}")
        exit(1)

    print("Select event JSON from the list:")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f}")

    while True:
        choice = input(f"Enter number (1-{len(files)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(files):
            return files[int(choice)-1]
        print("Invalid choice. Try again.")

def get_datetime(prompt, user_tz):
    """Prompt user for date/time and return UTC datetime"""
    while True:
        date_str = input(prompt).strip()
        try:
            dt_local = datetime.strptime(date_str, "%m/%d/%Y %I:%M %p")
            dt_local = user_tz.localize(dt_local)
            return dt_local.astimezone(pytz.UTC)
        except ValueError:
            print("Invalid format. Use MM/DD/YYYY HH:MM AM/PM")

def preview_event(event):
    print("\n===== EVENT PREVIEW =====")
    print(f"Unique Name: {event['unique_event_name']}")
    print(f"Name       : {event['name']}")
    print(f"JSON File  : {event['event_json']}")
    print(f"Description: {event['description']}")
    print(f"Start UTC  : {event['start']}")
    print(f"End UTC    : {event['end']}")
    print("=========================\n")
    while True:
        confirm = input("Save this event? (Y/N): ").strip().lower()
        if confirm in ("y", "n"):
            return confirm == "y"
        print("Invalid input. Enter Y or N.")

# ====== MAIN SCRIPT ======
def main():
    user_tz = select_timezone()
    json_file = select_event_json()
    base_name = json_file.replace(".json", "")
    event_name = split_camel_case(base_name)
    description = input("Enter event description: ").strip()

    # Get start time
    start_dt_utc = get_datetime("Enter event start (MM/DD/YYYY HH:MM AM/PM): ", user_tz)

    # Get end time and ensure it is after start
    while True:
        end_dt_utc = get_datetime("Enter event end (MM/DD/YYYY HH:MM AM/PM): ", user_tz)
        if end_dt_utc <= start_dt_utc:
            print("End time must be after start time. Try again.")
        else:
            break

    # Build event dictionary
    event = {
        "unique_event_name": make_unique_event_name(event_name, start_dt_utc),
        "name": event_name,
        "event_json": json_file,
        "description": description,
        "start": start_dt_utc.isoformat(),
        "end": end_dt_utc.isoformat(),
        "24_hour_sent": False,
        "30_minute_sent": False,
        "event_start_sent": False,
        "event_over_sent": False,
        "event_in_progress": False,
        "last_scoreboard_time": "",
        "event_started": False,
        "event_over": False
    }

    # Preview before saving
    if preview_event(event):
        calendar = load_calendar()
        calendar.append(event)
        save_calendar(calendar)
        print(f"Event '{event_name}' added successfully!")
    else:
        print("Event creation canceled.")

if __name__ == "__main__":
    main()
