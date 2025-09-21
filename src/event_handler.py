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
BOT_PY_PATH = "./bot.py"
RCON_FRAMEWORK_PATH = "./rcon_event_framework.py"
RESULTS_PATH = os.getenv("LOGS_PATH")
CHECK_INTERVAL = 30  # seconds, how often to check for events

# ====== HELPER FUNCTIONS ======
def load_calendar():
    try:
        with open(CALENDAR_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
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
    print("Event handler started...")
    while True:
        now = datetime.now(timezone.utc)
        calendar = load_calendar()
        calendar_changed = False

        for event in calendar:
            start_time = datetime.fromisoformat(event["start"])
            end_time = datetime.fromisoformat(event["end"])
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)

            unique_name = event["unique_event_name"]
            event_file = event["event_json"]

            # --- 24-hour notification ---
            if not event.get("24_hour_sent", False) and now >= start_time - timedelta(hours=24):
                send_discord_notification("twenty_four", unique_name)
                event["24_hour_sent"] = True
                calendar_changed = True

            # --- 30-minute notification ---
            if not event.get("30_minute_sent", False) and now >= start_time - timedelta(minutes=30):
                send_discord_notification("thirty", unique_name)
                event["30_minute_sent"] = True
                calendar_changed = True

            # --- Event start ---
            if not event.get("event_start_sent", False) and now >= start_time:
                send_discord_notification("now", unique_name)
                call_rcon_framework("start", event_file)
                event["event_start_sent"] = True
                event["event_in_progress"] = True
                calendar_changed = True

            # --- Event in progress display (every 15 minutes) ---
            if event.get("event_in_progress", True):
                last_time_str = event.get("last_scoreboard_time", "")
                now = datetime.now(timezone.utc)

                call_display = False

                if last_time_str:
                    try:
                        last_time = datetime.fromisoformat(last_time_str)
                        if now - last_time >= timedelta(minutes=15):
                            call_display = True
                    except ValueError:
                        # invalid format, just call display
                        print("Value Error for why?")
                        call_display = True
                        event["last_scoreboard_time"] = now.isoformat()
                else:
                    # never displayed before
                    event["last_scoreboard_time"] = now.isoformat()

                if call_display:
                    call_rcon_framework("display", event_file)
                    # update last_scoreboard_time
                    event["last_scoreboard_time"] = now.isoformat()

            # --- Event over ---

            if not event.get("event_over_sent", False) and now >= end_time:
                #Stop the event on the server
                call_rcon_framework("clean", event_file)

                # Determine today's results file
                date_str = datetime.now().strftime("%m-%d-%Y")
                safe_event_name = event['name'].replace(" ", "-")
                results_pattern = f"{RESULTS_PATH}{safe_event_name}-{date_str}.json"                

                winners = []
                score = None

                results_file = glob.glob(results_pattern)
                if results_file:
                    try:
                        with open(results_file[0], 'r') as f:
                            results_data = json.load(f)
                            winners = results_data.get("Leaders", [])
                            score = results_data.get("FinalScore", None)
                    except Exception as e:
                        print(f"ERROR Finding Results File")
                else:
                    print("Couldn't find results file!")

                print(winners, score)

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

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
