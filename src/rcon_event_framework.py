#!/usr/bin/env python3
import json
import time
import sys
import os
from mcrcon import MCRcon # type: ignore
from datetime import datetime, timezone
from dotenv import load_dotenv
import re
import sql_calendar

# LOAD CONFIG
load_dotenv()
rcon_host = os.getenv("RCON_HOST")
rcon_port = int(os.getenv("RCON_PORT"))
rcon_pass = os.getenv("RCON_PASS")
events_path = os.getenv("EVENTS_JSON_PATH")

def load_json(event_file):
    with open(event_file, "r") as f:
        event_data = json.load(f)
    return event_data

def escape_mc_string(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')

def log_to_sql(message, level="INFO"):
    """Log to SQLite database with proper UTC timestamp format"""
    try:
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        sql_calendar.log_message_with_timestamp(message, level, timestamp)
    except Exception as e:
        print(f"SQL logging failed: {e} - Message: {message}")

def mcrcon_wrapper(cmds):
    """Execute RCON commands with error handling and logging"""
    if isinstance(cmds, str):
        cmds = [cmds]

    cmd_results = []

    try:
        with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
            for cmd in cmds:
                result = mcr.command(cmd)
                cmd_results.append(result)
                log_to_sql(f"RCON command executed: {cmd}")
        return cmd_results
    except Exception as e:
        error_msg = f"MCRCON error: {e}"
        log_to_sql(error_msg, "ERROR")
        for cmd in cmds:
            log_to_sql(f"Failed RCON command: {cmd}", "ERROR")
        return []

def get_players():
    """Get list of tracked players from scoreboard"""
    player_list_cmd = "scoreboard players list"
    results = mcrcon_wrapper(player_list_cmd)
    
    if not results:
        log_to_sql("No results from player list command", "WARN")
        return []
    
    log_to_sql(f"Player list query result: {results}")

    match = re.search(r"There are \d+ tracked entity/entities: (.+)", results[0])
    if match:
        players = match.group(1).split(", ")
        log_to_sql(f"Found tracked players: {players}")
        return players
    else:
        log_to_sql("Could not parse tracked players from scoreboard", "WARN")
        return []

def start_event(event_data):
    """Start an event with announcements and setup commands"""
    log_to_sql(f"Starting event: {event_data.get('name', 'Unknown')}")

    # Event start announcement
    event_start_text = f"The {event_data['name']} event is starting"
    json_start_text = {"text": event_start_text, "color": "gold"}
    display_title_text = f"tellraw @a {json.dumps(json_start_text)}"

    # Event description
    event_description_text = f"{event_data['description']}"
    json_desc_text = {"text": event_description_text, "color": "aqua"}
    display_description_text = f"tellraw @a {json.dumps(json_desc_text)}"

    # Display start text
    result_start_text = mcrcon_wrapper(display_title_text)
    log_to_sql(f"Event start announcement sent with result: {result_start_text}")

    # Play event start bells
    bells_command = 'execute as @a at @s run playsound minecraft:block.bell.use master @s ~ ~ ~ 100'
    for i in range(9):
        bell_result = mcrcon_wrapper(bells_command)
        log_to_sql(f"Bell sound {i+1}/9 played")
        time.sleep(0.25)

    # Display description
    result_description = mcrcon_wrapper(display_description_text)
    log_to_sql(f"Event description displayed with result: {result_description}")

    # Play wither death sound
    wither_sound_cmd = 'execute as @a at @s run playsound minecraft:entity.wither.death master @s ~ ~ ~ 100'
    wither_result = mcrcon_wrapper(wither_sound_cmd)
    log_to_sql(f"Wither sound played with result: {wither_result}")

    # Execute setup commands
    try:
        setup_commands = event_data["commands"]["setup"]
        for cmd in setup_commands:
            cmd_result = mcrcon_wrapper(cmd)
            log_to_sql(f"Setup command executed: {cmd} - Result: {cmd_result}")
    except KeyError:
        log_to_sql("No setup commands found in event JSON", "WARN")
    except Exception as e:
        log_to_sql(f"Error executing setup commands: {e}", "ERROR")

    log_to_sql("Event setup completed successfully")
    print("✅ Event Setup Completed")

def aggregate_scores(event_data):
    """Aggregate player scores for events that require it"""
    player_list = get_players()
    
    if not player_list:
        log_to_sql("No tracked players found for score aggregation", "WARN")
        print("No tracked players. Nothing to aggregate.")
        return

    log_to_sql(f"Aggregating scores for players: {player_list}")

    try:
        agg_obj = event_data["aggregate_objective"]
        objectives = event_data["commands"]["aggregate"]
        is_aggregate_event = event_data.get("is_aggregate", False)
    except KeyError as e:
        log_to_sql(f"Missing required field for aggregation: {e}", "ERROR")
        return

    if not is_aggregate_event:
        log_to_sql("Event does not require score aggregation")
        return

    for player in player_list:
        # Reset aggregate score to zero
        reset_cmd = f"scoreboard players set {player} {agg_obj} 0"
        reset_result = mcrcon_wrapper(reset_cmd)
        log_to_sql(f"Reset {agg_obj} to 0 for {player}: {reset_result}")

        # Aggregate each objective
        for objective in objectives:
            agg_cmd = f"scoreboard players operation {player} {agg_obj} += {player} {objective}"
            agg_result = mcrcon_wrapper(agg_cmd)
            log_to_sql(f"Aggregated {objective} into {agg_obj} for {player}: {agg_result}")

    log_to_sql("Score aggregation completed")
    print("✅ Calculated Aggregate Scores")

def find_leaders(event_data, silent=False):
    """Find the leading players and optionally announce them"""
    player_list = get_players()
    
    if not player_list:
        log_to_sql("No players to check for leaders", "WARN")
        return [], 0

    try:
        main_obj = event_data["aggregate_objective"]
    except KeyError:
        log_to_sql("Missing aggregate_objective in event data", "ERROR")
        return [], 0

    leaders = []
    leading_score = 0

    log_to_sql(f"Checking scores for objective: {main_obj}")

    for player in player_list:
        score_cmd = f"scoreboard players get {player} {main_obj}"
        score_result = mcrcon_wrapper(score_cmd)
        log_to_sql(f"Score check for {player}: {score_result}")

        if not score_result:
            continue

        # Parse score from result
        match = re.search(r"has (\d+)", score_result[0])
        if match:
            score = int(match.group(1))
            
            if not leaders or score > leading_score:
                leaders = [player]
                leading_score = score
            elif score == leading_score:
                leaders.append(player)
        else:
            log_to_sql(f"Could not parse score for {player} from: {score_result[0]}", "WARN")

    # FIXED: Check if top score is 0 (nobody participated)
    if leading_score == 0:
        log_to_sql("Top score is 0 - no participation in event")
        if not silent:
            message = f"No one participated in the {event_data['name']} event."
            announcement = {"text": message, "color": "red"}
            announce_cmd = f"tellraw @a {json.dumps(announcement)}"
            announce_result = mcrcon_wrapper(announce_cmd)
            log_to_sql(f"No participation announcement sent: {announce_result}")
        return [], 0

    # Format leader announcement for actual scores
    if leaders:
        leader_names = ", ".join(leaders)
        log_to_sql(f"Current leaders: {leader_names} with score {leading_score}")

        if not silent:
            if len(leaders) == 1:
                message = f"{leader_names} is leading the {event_data['name']} event with {leading_score} {event_data.get('score_text', 'points')}!"
            else:
                message = f"{leader_names} are tied for first in the {event_data['name']} event with {leading_score} {event_data.get('score_text', 'points')}!"

            announcement = {"text": message, "color": "gold"}
            announce_cmd = f"tellraw @a {json.dumps(announcement)}"
            announce_result = mcrcon_wrapper(announce_cmd)
            log_to_sql(f"Leader announcement sent: {announce_result}")
    else:
        log_to_sql("No leaders found")

    print("✅ Leaders determined!")
    return leaders, leading_score

def display_scoreboard(event_data, unique_event_name=None):
    """Display the event scoreboard for a specified duration"""
    try:
        tracked_obj = event_data["aggregate_objective"]
        display_name = event_data["sidebar"]["displayName"]
        duration = event_data["sidebar"]["duration"]
        bold = event_data["sidebar"]["bold"]
        color = event_data["sidebar"]["color"]
    except KeyError as e:
        log_to_sql(f"Missing scoreboard configuration: {e}", "ERROR")
        return

    log_to_sql(f"Displaying scoreboard for {duration} seconds")

    # Set up scoreboard display
    display_cmd = f'scoreboard objectives setdisplay sidebar {tracked_obj}'
    display_result = mcrcon_wrapper(display_cmd)
    log_to_sql(f"Scoreboard display set: {display_result}")

    # Format scoreboard title
    title_format = {
        "text": str(display_name),
        "color": str(color),
        "bold": bool(bold)
    }
    
    modify_cmd = f"scoreboard objectives modify {tracked_obj} displayname {json.dumps(title_format)}"
    modify_result = mcrcon_wrapper(modify_cmd)
    log_to_sql(f"Scoreboard title modified: {modify_result}")

    # Display for specified duration
    time.sleep(duration)

    # Clear scoreboard
    clear_cmd = "scoreboard objectives setdisplay sidebar"
    clear_result = mcrcon_wrapper(clear_cmd)
    log_to_sql(f"Scoreboard cleared: {clear_result}")

    # Update the scoreboard display time in database
    if unique_event_name:
        update_scoreboard_display_time(unique_event_name)

    log_to_sql("Scoreboard display completed")
    print("✅ Scoreboard was displayed")

def cleanup_objs(event_data):
    """Clean up scoreboard objectives after event"""
    try:
        cleanup_objectives = event_data["commands"]["cleanup"]
    except KeyError:
        log_to_sql("No cleanup objectives specified", "WARN")
        return

    log_to_sql(f"Cleaning up objectives: {cleanup_objectives}")

    for objective in cleanup_objectives:
        cleanup_cmd = f'scoreboard objectives remove {objective}'
        cleanup_result = mcrcon_wrapper(cleanup_cmd)
        log_to_sql(f"Cleaned up objective {objective}: {cleanup_result}")

    log_to_sql("Event cleanup completed")
    print("✅ Event has been cleaned up!")

def update_scoreboard_display_time(unique_event_name):
    """Update the last scoreboard display time with proper UTC format"""
    try:
        event_id = sql_calendar.get_event_id_by_unique_name(unique_event_name)
        if not event_id:
            log_to_sql(f"Could not find event ID for: {unique_event_name}", "ERROR")
            return False
            
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        sql_calendar.update_scoreboard_time(event_id, timestamp)
        log_to_sql(f"Updated scoreboard display time for event {event_id} ({unique_event_name}) to {timestamp}")
        return True
    except Exception as e:
        log_to_sql(f"Error updating scoreboard time: {e}", "ERROR")
        return False

def save_winners_to_sql(event_data, leaders, final_score):
    """Save event winners directly to SQLite database"""
    try:
        unique_name = event_data.get('unique_event_name')
        if not unique_name:
            log_to_sql("No unique_event_name found in event data", "ERROR")
            return
            
        event_id = sql_calendar.get_event_id_by_unique_name(unique_name)
        if not event_id:
            log_to_sql(f"Could not find event ID for: {unique_name}", "ERROR")
            return

        # FIXED: Don't save winners if nobody participated (empty leaders list)
        if not leaders or final_score == 0:
            log_to_sql("No winners to save (nobody participated)")
            print("✅ Event ended with no winners (no participation)")
            return

        # Get online players to determine who was online
        online_cmd = "list"
        online_result = mcrcon_wrapper(online_cmd)
        online_players = []
        
        if online_result:
            online_match = re.search(r"online:\s*(.+)$", online_result[0])
            if online_match:
                online_players = [p.strip() for p in online_match.group(1).split(",")]

        # Save each winner
        for winner in leaders:
            was_online = winner in online_players
            sql_calendar.insert_winner(event_id, winner, final_score, was_online)
            log_to_sql(f"Saved winner: {winner} (online: {was_online})")

        log_to_sql(f"Saved {len(leaders)} winners for event {unique_name}")
        print(f"✅ Event results saved: {', '.join(leaders)} with score {final_score}")
        
    except Exception as e:
        log_to_sql(f"Error saving winners to database: {e}", "ERROR")

def give_reward_item(winners, event_data):
    """Give reward items to online winners"""
    if not winners:
        log_to_sql("No winners to reward")
        return

    # Get online players
    online_cmd = "list"
    online_result = mcrcon_wrapper(online_cmd)
    
    if not online_result:
        log_to_sql("Could not get online players list", "ERROR")
        return

    log_to_sql(f"Online players query result: {online_result}")

    # Parse online players
    online_match = re.search(r"online:\s*(.+)$", online_result[0])
    if online_match:
        online_players = [p.strip() for p in online_match.group(1).split(",")]
    else:
        log_to_sql("Could not parse online players list", "WARN")
        online_players = []

    online_winners = [player for player in winners if player in online_players]
    offline_winners = [player for player in winners if player not in online_players]

    log_to_sql(f"Online winners: {online_winners}, Offline winners: {offline_winners}")

    for winner in online_winners:
        try:
            # Winner notification sequence
            notifications = [
                f'tellraw {winner} "You have won the {event_data["name"]} event!"',
                f'tellraw {winner} "You will be receiving your prize in..."',
                f'tellraw {winner} "3!"',
                f'tellraw {winner} "2!"',
                f'tellraw {winner} "1!"'
            ]
            
            for notif in notifications:
                mcrcon_wrapper(notif)
                time.sleep(1)

            # Give reward item
            reward_cmd = f'give {winner} {event_data["reward_cmd"]}'
            reward_cmd = reward_cmd.replace("'", '"')
            reward_result = mcrcon_wrapper(reward_cmd)
            log_to_sql(f"Gave reward to {winner}: {reward_result}")

            # Item received notification
            item_msg = f"You have been given the legendary {event_data['reward_name']}!"
            item_json = {"text": item_msg, "color": "light_purple"}
            item_cmd = f'tellraw {winner} {json.dumps(item_json)}'
            mcrcon_wrapper(item_cmd)

            log_to_sql(f"Reward sequence completed for {winner}")

        except KeyError as e:
            log_to_sql(f"Missing reward configuration: {e}", "ERROR")
        except Exception as e:
            log_to_sql(f"Error rewarding {winner}: {e}", "ERROR")

    if offline_winners:
        log_to_sql(f"Offline winners need manual reward: {offline_winners}", "WARN")

    log_to_sql("Reward distribution completed")
    print("✅ Distributed rewards to online winners!")

def closing_ceremony(event_data):
    """Execute closing ceremony with effects and winner announcements"""
    log_to_sql("Starting closing ceremony")

    # Find winners silently
    leaders, final_score = find_leaders(event_data, silent=True)

    # Event end announcement
    end_text = f"The {event_data['name']} event has ended!"
    end_json = {"text": end_text, "color": "gold"}
    end_cmd = f"tellraw @a {json.dumps(end_json)}"
    mcrcon_wrapper(end_cmd)

    # Fireworks display
    firework_particles = 'execute as @a at @s run particle minecraft:firework ~ ~ ~ 1 1 1 0.2 100 force'
    firework_sounds = 'execute as @a at @s run playsound minecraft:entity.firework_rocket.twinkle master @s ~ ~ ~ 100'

    log_to_sql("Playing fireworks display")
    for i in range(5):
        mcrcon_wrapper([firework_particles, firework_sounds])
        time.sleep(0.3)

    # FIXED: Handle different winner scenarios
    if not leaders or final_score == 0:
        # Nobody participated
        no_winner_text = "Unfortunately, nobody participated in this event!"
        no_winner_json = {"text": no_winner_text, "color": "red"}
        no_winner_cmd = f"tellraw @a {json.dumps(no_winner_json)}"
        mcrcon_wrapper(no_winner_cmd)
        log_to_sql("No participation announcement sent")
    else:
        # We have winners with actual scores
        winner_text = f"{', '.join(leaders)} won the event with {final_score} {event_data.get('score_text', 'points')}"
        winner_json = {"text": winner_text, "color": "green"}
        winner_cmd = f"tellraw @a {json.dumps(winner_json)}"
        mcrcon_wrapper(winner_cmd)
        log_to_sql(f"Winner announcement: {winner_text}")

    # Ceremony music
    music_cmd = 'execute as @a at @s run playsound minecraft:music_disc.lava_chicken master @s ~ ~ ~ 100'
    mcrcon_wrapper(music_cmd)
    log_to_sql("Started ceremony music")

    # Display final scoreboard
    display_scoreboard(event_data)
    
    # Stop music
    stop_cmd = 'stopsound @a'
    mcrcon_wrapper(stop_cmd)
    log_to_sql("Stopped ceremony music")

    # FIXED: Only distribute rewards if there are actual winners
    if leaders and final_score > 0:
        give_reward_item(leaders, event_data)

    # Save results to database
    save_winners_to_sql(event_data, leaders, final_score)

    log_to_sql("Closing ceremony completed")

def run_event(action, json_file, unique_name=None):
    """Main event runner function"""
    log_to_sql(f"Running event action: {action} with file: {json_file}")
    
    # Load event data
    try:
        event_data = load_json(f'{events_path}{json_file}')
        log_to_sql(f"Loaded event data for: {event_data.get('name', 'Unknown')}")
        
        # Add unique_event_name to event_data if provided
        if unique_name:
            event_data['unique_event_name'] = unique_name
            log_to_sql(f"Added unique_event_name to event data: {unique_name}")
            
    except Exception as e:
        error_msg = f"Failed to load event JSON {json_file}: {e}"
        log_to_sql(error_msg, "ERROR")
        print(f"❌ {error_msg}")
        sys.exit(1)

    # Get event ID for database operations
    event_id = None
    if unique_name:
        event_id = sql_calendar.get_event_id_by_unique_name(unique_name)

    # Execute requested action
    try:
        if action == "start":
            start_event(event_data)
        elif action == "display":
            aggregate_scores(event_data)
            find_leaders(event_data)
            display_scoreboard(event_data, unique_event_name=unique_name)
        elif action == "clean":
            aggregate_scores(event_data)
            closing_ceremony(event_data)
            cleanup_objs(event_data)
        else:
            error_msg = f"Unknown action: {action}"
            log_to_sql(error_msg, "ERROR")
            print(f"❌ {error_msg}")
            sys.exit(1)
            
        log_to_sql(f"Event action '{action}' completed successfully")
        
    except Exception as e:
        error_msg = f"Error during {action} action: {e}"
        log_to_sql(error_msg, "ERROR")
        print(f"❌ {error_msg}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python rcon_event_framework.py <start|display|clean> <json-file> [unique_event_name]")
        sys.exit(1)

    action = sys.argv[1]
    json_file = sys.argv[2]
    unique_name = sys.argv[3] if len(sys.argv) > 3 else None

    run_event(action, json_file, unique_name)