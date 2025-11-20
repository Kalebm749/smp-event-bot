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
    
    # For 'over' action, always add winners and score (even if empty/zero)
    if action == "over":
        if winners is None:
            winners = ['no_Participants']
        if score is None:
            score = 0
        cmd.append(",".join(winners))
        cmd.append(str(score))
    
    print(f"Sending Discord notification: {' '.join(cmd)}")
    sql_calendar.log_message(f"Sending Discord notification: {' '.join(cmd)}")
    subprocess.run(cmd)

def call_rcon_framework(action, json_file, unique_name=None):
    """Call the RCON framework script"""
    cmd = ["python3", RCON_FRAMEWORK_PATH, action, json_file]
    if unique_name:
        cmd.append(unique_name)
    print(f"Calling RCON framework: {' '.join(cmd)}")
    sql_calendar.log_message(f"Calling RCON framework: {' '.join(cmd)}")
    subprocess.run(cmd)

def get_event_results(unique_event_name):
    """Get event results from database (NOT from files)"""
    winners = []
    score = None
    
    try:
        # Get event ID from unique name
        event_id = sql_calendar.get_event_id_by_unique_name(unique_event_name)
        if not event_id:
            sql_calendar.log_message(f"Could not find event ID for: {unique_event_name}", "ERROR")
            return ['no_Participants'], 0
        
        # Get winners from database
        winners_data = sql_calendar.get_event_winners(event_id)
        
        if winners_data:
            # Extract winner names and get the final score from the first winner
            winners = [winner[2] for winner in winners_data]  # player_name is index 2
            score = winners_data[0][3] if winners_data[0][3] is not None else 0  # final_score is index 3
            sql_calendar.log_message(f"Found winners in database: {winners} with score {score}")
        else:
            sql_calendar.log_message("No winners found in database")
            winners = ['no_Participants']
            score = 0
            
    except Exception as e:
        sql_calendar.log_message(f"Error getting event results from database: {e}", "ERROR")
        winners = ['no_Participants']
        score = 0
    
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
                
                # Stop the event on the server - this will save winners to database
                call_rcon_framework("clean", event_json, unique_name)
                
                # Give the RCON framework time to save winners to database
                time.sleep(3)
                
                # Get results from database using unique_name
                winners, score = get_event_results(unique_name)
                
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
                
                call_rcon_framework("display", event_json, unique_name)  
    # Pass unique_name as third argument
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