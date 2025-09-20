import json
from datetime import datetime, timedelta
import pytz

EVENT_FILE = "events.json"

# List of common US and Europe timezones
COMMON_TIMEZONES = [
    "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
    "Europe/London", "Europe/Berlin", "Europe/Paris", "Europe/Madrid",
    "Europe/Rome", "Europe/Amsterdam"
]

def input_timezone():
    print("\nSelect your timezone from the list below:")
    for i, tz in enumerate(COMMON_TIMEZONES):
        print(f"{i + 1}. {tz}")
    while True:
        choice = input("Enter the number of your timezone: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(COMMON_TIMEZONES):
            return pytz.timezone(COMMON_TIMEZONES[int(choice) - 1])
        else:
            print("Invalid selection. Try again.")

def input_date():
    while True:
        date_str = input("Enter start date (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

def input_time():
    while True:
        time_str = input("Enter start time (HH:MM, 24-hour): ").strip()
        try:
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except ValueError:
            print("Invalid time format. Please use HH:MM in 24-hour format.")

def input_length():
    while True:
        length_str = input("Enter event length in minutes: ").strip()
        if length_str.isdigit() and int(length_str) > 0:
            return int(length_str)
        else:
            print("Invalid length. Please enter a positive integer.")

def create_event():
    name = input("\nEnter event name: ").strip()
    description = input("Enter event description: ").strip()
    tz = input_timezone()
    start_date = input_date()
    start_time = input_time()
    length_minutes = input_length()

    # Combine date and time
    local_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    local_dt = tz.localize(local_dt)  # make timezone-aware
    utc_start = local_dt.astimezone(pytz.utc)
    utc_end = utc_start + timedelta(minutes=length_minutes)

    # Build event object
    event = {
        "name": name,
        "description": description,
        "start": utc_start.isoformat(),
        "end": utc_end.isoformat(),
        "notif_24h": False,
        "notif_30m": False,
        "notif_start": False,
        "notif_end": False
    }

    # Load existing events
    try:
        with open(EVENT_FILE, "r") as f:
            events = json.load(f)
    except FileNotFoundError:
        events = []

    # Append new event and save
    events.append(event)
    with open(EVENT_FILE, "w") as f:
        json.dump(events, f, indent=2)

    print(f"\n✅ Event '{name}' added! Starts at {utc_start} UTC, ends at {utc_end} UTC.\n")

def main():
    print("=== Discord Event Creator ===")
    while True:
        create_event()
        again = input("Do you want to create another event? (y/n): ").strip().lower()
        if again != "y":
            print("Exiting event creator.")
            break

if __name__ == "__main__":
    main()
