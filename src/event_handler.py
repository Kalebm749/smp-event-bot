#!/usr/bin/python3.12
import json
import glob
import os
import subprocess
import time
import sql_calendar
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# ====== CONFIG ======
load_dotenv()
RESULTS_PATH = os.getenv("LOGS_PATH")
CHECK_INTERVAL = 30  # seconds, how often to check for events

# ===== Script Paths =====
BOT_PY_PATH = "./src/bot.py"
RCON_FRAMEWORK_PATH = "./src/rcon_event_framework.py"

# ====== HELPER FUNCTIONS ======

def send_discord_notification(action, unique_name, winners=None, score=None):
    """Call the bot.py script with subprocess"""
    cmd = ["python3", BOT_PY_PATH, action, unique_name]
    if winners and score:
        cmd.append(",".join(winners))
        cmd.append(str(score))
    print(f"Sending Discord notification: {' '.join(cmd)}")
    sql_calendar.log_message(f"Sending Discord notification: {' '.join(cmd)}")
    subprocess.run(cmd)

def call_rcon_framework(action, json_file):
    """Call the RCON framework script"""
    cmd = ["python3", RCON_FRAMEWORK_PATH, action, json_file]
    print(f"Calling RCON framework: {' '.join(cmd)}")
    sql_calendar.log_message(f"Calling RCON framework: {' '.join(cmd)}")
    subprocess.run(cmd)

def get_event_results(event_name):
    """Get event results from results file"""
    date_str = datetime.now().strftime("%m-%d-%Y")
    safe_event_name = event_name.replace(" ", "-")
    results_pattern = f"{RESULTS_PATH}{safe_event_name}-{date_str}.json"
    
    winners = []
    score = None
    
    sql_calendar.log_message(f"Looking for results file: {results_pattern}")
    results_file = glob.glob(results_pattern)
    
    if results_file:
        try:
            with open(results_file[0], 'r') as f:
                results_data = json.load(f)
                winners = results_data.get("Leaders", [])
                score = results_data.get("FinalScore", None)
                sql_calendar.log_message(f"Found results: winners={winners}, score={score}")
        except Exception as e:
            sql_calendar.log_message(f"Error reading results file: {e}", "ERROR")
    else:
        sql_calendar.log_message("No results file found")
    
    if not winners:
        winners = ['no_Participants']
        score = 1
    
    return winners, score

# ====== MAIN LOOP ======
def main():
    sql_calendar.log_message("Event handler starting up")

    while True:
        try:
            # === PRIORITY 1: Start Events ===
            start_event_list = sql_calendar.events_needing_started()
            
            for event in start_event_list:
                event_id, unique_name, name, event_json = event[0], event[1], event[2], event[3]
                print(f"DEBUG| Starting Event {name}")
                sql_calendar.log_message(f"Starting event: {name} (ID: {event_id})")
                
                call_rcon_framework("start", event_json)
                sql_calendar.start_event_by_id(event_id)

            # === PRIORITY 2: Send Event Start Notifications ===
            missing_start_notifications = sql_calendar.find_missing_now_notif()
            
            for event in missing_start_notifications:
                event_id, unique_name, name = event[0], event[1], event[2]
                print(f"DEBUG| Sending start notification for {name}")
                sql_calendar.log_message(f"Sending start notification for: {name}")
                
                send_discord_notification("now", unique_name)
                sql_calendar.send_start_notification(event_id)

            # === PRIORITY 3: End Events ===
            end_event_list = sql_calendar.events_needing_ending()
            
            for event in end_event_list:
                event_id, unique_name, name, event_json = event[0], event[1], event[2], event[3]
                print(f"DEBUG| Ending Event {name}")
                sql_calendar.log_message(f"Ending event: {name} (ID: {event_id})")
                
                # Stop the event on the server
                call_rcon_framework("clean", event_json)
                
                # Get results
                winners, score = get_event_results(name)
                
                # Send Discord notification
                send_discord_notification("over", unique_name, winners=winners, score=score)
                
                # Mark event as ended and send notification
                sql_calendar.end_event_by_id(event_id)
                sql_calendar.send_end_notification(event_id)

            # === PRIORITY 4: Display Scoreboards ===
            scoreboard_events = sql_calendar.events_needing_scoreboard_display()
            
            for event in scoreboard_events:
                event_id, unique_name, name, event_json = event[0], event[1], event[2], event[3]
                print(f"DEBUG| Displaying scoreboard for {name}")
                sql_calendar.log_message(f"Displaying scoreboard for: {name}")
                
                call_rcon_framework("display", event_json)
                # Update scoreboard time will be handled in the RCON framework now

            # === PRIORITY 5: Send 30 Minute Notifications ===
            missing_30min_notifications = sql_calendar.find_missing_30m_notif()
            
            for event in missing_30min_notifications:
                event_id, unique_name, name = event[0], event[1], event[2]
                print(f"DEBUG| Sending 30min notification for {name}")
                sql_calendar.log_message(f"Sending 30min notification for: {name}")
                
                send_discord_notification("thirty", unique_name)
                sql_calendar.send_30min_notification(event_id)

            # === PRIORITY 6: Send 24 Hour Notifications ===
            missing_24h_notifications = sql_calendar.find_missing_24h_notif()
            
            for event in missing_24h_notifications:
                event_id, unique_name, name = event[0], event[1], event[2]
                print(f"DEBUG| Sending 24h notification for {name}")
                sql_calendar.log_message(f"Sending 24h notification for: {name}")
                
                send_discord_notification("twenty_four", unique_name)
                sql_calendar.send_24h_notification(event_id)

        except Exception as e:
            error_msg = f"Error in main loop: {e}"
            print(f"ERROR| {error_msg}")
            sql_calendar.log_message(error_msg, "ERROR")

        # Sleep before next cycle
        sql_calendar.log_message(f"Sleeping for {CHECK_INTERVAL} seconds")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()