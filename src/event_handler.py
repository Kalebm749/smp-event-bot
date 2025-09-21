#!/usr/bin/python3.12
import json
import glob
import os
import subprocess
import time
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# ====== CONFIG ======
load_dotenv()
CALENDAR_FILE = os.getenv("CALENDAR_FILE")
BOT_PY_PATH = "./src/bot.py"
RCON_FRAMEWORK_PATH = "./src/rcon_event_framework.py"
RESULTS_PATH = os.getenv("LOGS_PATH")
CHECK_INTERVAL = 30  # seconds, how often to check for events

# ====== HELPER FUNCTIONS ======
def handler_logger(text):
    log_file_path = f'{RESULTS_PATH}handler_logs.txt'

    with open(log_file_path, "a") as f:
        f.write(f"{str(datetime.now(timezone.utc))}: {text}\n")

def load_calendar():
    try:
        with open(CALENDAR_FILE, "r") as f:
            handler_logger("Opened the calendar file correctly")
            return json.load(f)
    except FileNotFoundError:
        handler_logger("Couldn't open the calendar file!")
        return []

def save_calendar(calendar):
    with open(CALENDAR_FILE, "w") as f:
        json.dump(calendar, f, indent=2)

def send_discord_notification(action, unique_name, winners=None, score=None):
    """Call the bot.py script with subprocess"""
    cmd = ["python3", BOT_PY_PATH, action, unique_name]
    if winners and score:
        cmd.append(",".join(winners))
        cmd.append(str(score))
    print(f"Sending Discord notification: {' '.join(cmd)}")
    subprocess.run(cmd)

def call_rcon_framework(action, json_file):
    """Call the RCON framework script"""
    cmd = ["python3", RCON_FRAMEWORK_PATH, action, json_file]
    print(f"Calling RCON framework: {' '.join(cmd)}")
    subprocess.run(cmd)

# ====== MAIN LOOP ======
def main():
    handler_logger("Event Handler Started")
    while True:
        now = datetime.now(timezone.utc)
        calendar = load_calendar()
        calendar_changed = False

        for event in calendar:
            handler_logger(f"Scanning event {event["unique_event_name"]}")

            start_time = datetime.fromisoformat(event["start"])
            end_time = datetime.fromisoformat(event["end"])
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)

            handler_logger(f"Event {event["unique_event_name"]} starts at {start_time} and ends at {end_time} it is now {now}")

            unique_name = event["unique_event_name"]
            event_file = event["event_json"]

            handler_logger(f"Checking 24 hour notification for {event["unique_event_name"]}")
            handler_logger(f"24 hour notification has been sent?: {event["24_hour_sent"]}")
            # --- 24-hour notification ---
            if not event.get("24_hour_sent", False) and now >= start_time - timedelta(hours=24):
                send_discord_notification("twenty_four", unique_name)
                event["24_hour_sent"] = True
                calendar_changed = True
                handler_logger(f"Sent 24 hour notification via discord for {event["unique_event_name"]}")

            handler_logger(f"Checking 30 minute notification for {event["unique_event_name"]}")
            handler_logger(f"30 minute has been sent?: {event["30_minute_sent"]}")
            # --- 30-minute notification ---
            if not event.get("30_minute_sent", False) and now >= start_time - timedelta(minutes=30):
                send_discord_notification("thirty", unique_name)
                event["30_minute_sent"] = True
                calendar_changed = True
                handler_logger(f"Sent 30 minute notification via discord for {event["unique_event_name"]}")

            handler_logger(f"Checking event start notification for {event["unique_event_name"]}")
            handler_logger(f"Event start notification sent?: {event["event_start_sent"]}")
            # --- Event start ---
            if not event.get("event_start_sent", False) and now >= start_time:
                send_discord_notification("now", unique_name)
                call_rcon_framework("start", event_file)
                event["event_start_sent"] = True
                event["event_in_progress"] = True
                calendar_changed = True
                handler_logger(f"Sent event starting notification now via discord for {event["unique_event_name"]}")

            handler_logger(f"Checking if event {event["unique_event_name"]} is in progress")
            # --- Event in progress display (every 15 minutes) ---
            if event.get("event_in_progress", True):
                handler_logger(f"{event["unique_event_name"]} is in progress")
                last_time_str = event.get("last_scoreboard_time", "")
                now = datetime.now(timezone.utc)

                call_display = False

                if last_time_str:
                    try:
                        last_time = datetime.fromisoformat(last_time_str)
                        if now - last_time >= timedelta(minutes=10):
                            call_display = True
                            handler_logger(f"It been longer than 10 minutes since {event["unique_event_name"]} had the scoreboard displayed")
                    except ValueError:
                        # invalid format, just call display
                        print("Value Error for why?")
                        call_display = True
                        event["last_scoreboard_time"] = now.isoformat()
                else:
                    # never displayed before
                    handler_logger(f"{event["unique_event_name"]} has never had the scoreboard displayed.")
                    handler_logger(f"Setting the scordboard last display time for {event["unique_event_name"]} as {now}")
                    event["last_scoreboard_time"] = now.isoformat()

                if call_display:
                    handler_logger(f"Displaying the scordboard for {event["unique_event_name"]}")
                    call_rcon_framework("display", event_file)
                    # update last_scoreboard_time
                    event["last_scoreboard_time"] = now.isoformat()
                    handler_logger(f"Updated the scoreboard last displayed time for {event["unique_event_name"]} as {now}")

            # --- Event over ---
            handler_logger(f"Checking if {event["unique_event_name"]} is over")
            if not event.get("event_over_sent", False) and now >= end_time:
                #Stop the event on the server
                handler_logger(f"{event["unique_event_name"]} is over. Time now {now}. End time {end_time}")
                call_rcon_framework("clean", event_file)

                # Determine today's results file
                date_str = datetime.now().strftime("%m-%d-%Y")
                safe_event_name = event['name'].replace(" ", "-")
                results_pattern = f"{RESULTS_PATH}{safe_event_name}-{date_str}.json"                

                winners = []
                score = None

                handler_logger(f"Trying to find results file {results_pattern}")
                results_file = glob.glob(results_pattern)
                if results_file:
                    try:
                        with open(results_file[0], 'r') as f:
                            results_data = json.load(f)
                            winners = results_data.get("Leaders", [])
                            score = results_data.get("FinalScore", None)
                            handler_logger(f"Opened results file {results_file[0]} and found winners {winners} and score {score}")
                    except Exception as e:
                        handler_logger(f"Error finding results file!")
                else:
                    handler_logger(f"Couldn't find results file")

                if not winners:
                    winners = ['no_Participants']
                    score=1

                handler_logger(f"{event["unique_event_name"]} has been cleaned up. Sending discord notification.")
                # Notify Discord
                send_discord_notification("over", unique_name, winners=winners, score=score)

                # Mark event over
                event["event_over_sent"] = True
                event["event_in_progress"] = False
                event["event_over"] = True
                calendar_changed = True

        # Save calendar if any changes
        if calendar_changed:
            save_calendar(calendar)
            handler_logger("Calendar has been updated with changes")

        handler_logger(f"Sleeping for {CHECK_INTERVAL} seconds")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
