#!/usr/bin/env python3
import json
import time
import sys
import os
from mcrcon import MCRcon # type: ignore
from datetime import datetime
from dotenv import load_dotenv
import re

# LOAD CONFIG
load_dotenv()
rcon_host = os.getenv("RCON_HOST")
rcon_port = int(os.getenv("RCON_PORT"))
rcon_pass = os.getenv("RCON_PASS")
events_path = os.getenv("EVENTS_JSON_PATH")
logs_path = os.getenv("LOGS_PATH")



def load_json(event_file):
    with open(event_file, "r") as f:
        event_data = json.load(f)

    return event_data


def escape_mc_string(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def write_to_log_file(result):
    log_file_path = f'{logs_path}event_logs.txt'

    with open (log_file_path, "a") as f:
        f.write(f"{result}\n")


def mcrcon_wrapper(cmds):

    #If cmds is a single string convert it to a list
    if isinstance(cmds, str):
        cmds = [cmds]

    cmd_results = []

    try:
        with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
            for cmd in cmds:
                result = mcr.command(cmd)
                cmd_results.append(result)
        return cmd_results
    except:
        for cmd in cmds:
            write_to_log_file(f"MCRCON error with command {cmd}")


def get_players():
    
    player_list_cmd = "scoreboard players list"

    results = mcrcon_wrapper(player_list_cmd)
    write_to_log_file(f"Found the following players {results}")

    match = re.search(r"There are \d+ tracked entity/entities: (.+)", results[0])
    if match:
        return match.group(1).split(", ")
    else:
        write_to_log_file(f"Could not find any tracked players in cmds '{player_list_cmd}'")

    
def start_event(event_data):

    # Grab the event start text and format it
    event_start_text = f"The {event_data['name']} event is starting"
    json_start_text = {"text": event_start_text, "color": "gold"}
    display_title_text = f"tellraw @a {json.dumps(json_start_text)}"

    # Grab the event description text and format it
    event_description_text = f"{event_data['description']}"
    json_desc_text = {"text": event_description_text, "color": "aqua"}
    display_description_text = f"tellraw @a {json.dumps(json_desc_text)}"

    # Display the event start text on the server
    result_start_text = mcrcon_wrapper(display_title_text)
    write_to_log_file(f"Attempted to start the event. Got response {result_start_text}")

    # Play the event start bells 9 times when the event starts
    bells_command = 'execute as @a at @s run playsound minecraft:block.bell.use master @s ~ ~ ~ 100'
    for i in range(9):
        bell_sound_result = mcrcon_wrapper(bells_command)
        write_to_log_file(f"Played event start bell sound. Got response {bell_sound_result}")
        time.sleep(0.25)

    # Display the event description text on the server
    result_description_text = mcrcon_wrapper(display_description_text)
    write_to_log_file(f"Attempted to display the event description. Got response {result_description_text}")

    # Play the wither.death event start sound
    wither_sounds_command = 'execute as @a at @s run playsound minecraft:entity.wither.death master @s ~ ~ ~ 100'
    wither_sound_result = mcrcon_wrapper(wither_sounds_command)
    write_to_log_file(f"Played event start wither sound. Got response {wither_sound_result}")

    # Run the start-up commands
    try:
        event_setup_commands = event_data["commands"]["setup"]
        for cmd in event_setup_commands:
            cmd_result = mcrcon_wrapper(cmd)
            write_to_log_file(f"Sent setup cmd: {cmd}")
            write_to_log_file(f"Got result: {cmd_result}")
    except:
        write_to_log_file(f"Failed to execute the event setup commands. Check event JSON formatting.")

    write_to_log_file("✅ Event Setup Completed")
    print("✅ Event Setup Completed")


#Runs all of the aggregate commands for all players
def aggregate_scores(event_data):
    #Grab a list of all the players
    player_list = get_players()
    write_to_log_file(f"Found the following tracked players for aggregate_scores {player_list}")

    #Grabs the aggregate objective
    try:
        agg_obj = event_data["aggregate_objective"]
    except:
        write_to_log_file("Failed to pull the aggregate objective. Check event JSON format")

    #Grab the objectives to aggregate on
    try:
        objectives = event_data["commands"]["aggregate"]
    except:
        write_to_log_file("Failed to pull the list of objectives to aggregate. Check event JSON format")

    #Try to check if this is an aggregate style event
    try:
        is_aggregate_event = event_data["is_aggregate"]
    except:
        write_to_log_file("Failed to check if this is an aggregate event. Check JSON format")

    if is_aggregate_event:
        for player in player_list:
            # Set aggregate scoreboard objective to zero
            aggregate_to_zero = f"scoreboard players set {player} {agg_obj} 0"
            result_to_zero = mcrcon_wrapper(aggregate_to_zero)
            write_to_log_file(f"Got the following result setting {agg_obj} to 0 for {player}: {result_to_zero}")

            for objective in objectives:
                aggregate_scores_additive_cmd = f"scoreboard players operation {player} {agg_obj} += {player} {objective}"
                additive_result = mcrcon_wrapper(aggregate_scores_additive_cmd)
                write_to_log_file(f"Got the following result aggregating {agg_obj} with {objective} for {player}: {additive_result}")
    else:
        write_to_log_file("Scores do not need aggregating for this event")

    print("✅ Calculated Aggregate Scores")
    write_to_log_file(f"✅ Calculated Aggregate Scores")


#Looks through the scoreboard objectives to find the leaders
def find_leaders(event_data, silent=False):
    player_list = get_players()

    try:
        main_obj = event_data["aggregate_objective"]
    except:
        write_to_log_file("Failed to pull the aggregate objective. Check event JSON format")

    leaders = []
    leading_score = 0

    for player in player_list:
        get_player_aggregate_score_cmd = f"scoreboard players get {player} {main_obj}"
        aggregate_score_result = mcrcon_wrapper(get_player_aggregate_score_cmd)
        write_to_log_file(f"Checked score for {player} got {aggregate_score_result}")

        #Search the aggregate score result for the numerical value
        match = re.search(r"has (\d+)", aggregate_score_result[0])
        if match:
            number = int(match.group(1))
            if not leaders:
                leaders.append(player)
                leading_score = number
            elif number == leading_score:
                leaders.append(player)
            elif number > leading_score:
                leaders = []
                leaders.append(player)
                leading_score = number
        else:
            write_to_log_file(f"Failed parse the score for {player}")

    #Tell the server whos winning
    player_string = ""
    for player in leaders:
        player_string += f"{player}, "
        if len(leaders) == 1:
            player_string = player

    if player_string.endswith(", "):
        player_string = player_string[:-2]

    write_to_log_file(f"Found the following leaders {player_string} with score {leading_score}")

    if len(leaders) == 1:
        player_string += f" is leading the pack for the {event_data["name"]} event with a score of {leading_score} {event_data["score_text"]}!"
    else:
        player_string += f" are tied for first in the {event_data["name"]} event with scores of {leading_score} {event_data["score_text"]}!"

    #If we want to actually send the message
    if not silent:
        leader_string = {"text": player_string, "color": "gold"}
        leader_cmd = f"tellraw @a {json.dumps(leader_string)}"
        result_display_leader_server = mcrcon_wrapper(leader_cmd)
        write_to_log_file(f"Displayed leaders {leader_string} with result: {result_display_leader_server}")
    
    print("✅ Displayed leaders!")
    write_to_log_file("✅ Displayed leaders!")

    return leaders, leading_score


# Displays the scordboard for a set amount of time specified in the event_data
def display_scoreboard(event_data):

    #What is being tracked, how long should it be displayed, should it be bold, what color?
    try:
        get_tracked_object = event_data["aggregate_objective"]
        scoreboard_display_name = event_data["sidebar"]["displayName"]
        scoreboard_duration = event_data["sidebar"]["duration"]
        scoreboard_bold = event_data["sidebar"]["bold"]
        scoreboard_color = event_data["sidebar"]["color"]
    except:
        write_to_log_file(f"Failed to parse scoreboard options. Check event JSON format.")

    #Create the scoreboard
    create_tracked_obj_scoreboard = f'scoreboard objectives setdisplay sidebar {get_tracked_object}'
    result_create_scordboard = mcrcon_wrapper(create_tracked_obj_scoreboard)
    write_to_log_file(f"Created event scordboard with result: {result_create_scordboard}")

    #Color and text the scoreboard
    if scoreboard_bold:
        scoreboard_decor = {"text":str(scoreboard_display_name),
                            "color":str(scoreboard_color),
                            "bold":True}
    else:
        scoreboard_decor = {"text":str(scoreboard_display_name),
                            "color":str(scoreboard_color)}
        
    modify_scoreboard_cmd = f"scoreboard objectives modify {get_tracked_object} displayname {json.dumps(scoreboard_decor, ensure_ascii=False)}"
    result_scoreboard_modify = mcrcon_wrapper(modify_scoreboard_cmd)
    write_to_log_file(f"Modified the scoreboard with result: {result_scoreboard_modify}")

    #Display the scoreboard for the time specified in event json
    write_to_log_file(f"Sleeping to display the scoreboard for {scoreboard_duration} seconds")
    time.sleep(scoreboard_duration)

    #Remove the scoreboard after sleeping
    score_board_cleanup_cmd = "scoreboard objectives setdisplay sidebar"
    result_cleanup_scoreboard = mcrcon_wrapper(score_board_cleanup_cmd)
    write_to_log_file(f"Cleaned up the scoreboard with result: {result_cleanup_scoreboard}")

    write_to_log_file("✅ Scoreboard was displayed")
    print("✅ Scoreboard was displayed")


# Remove anything related to the event
def cleanup_objs(event_data):

    try:
        cleanup_objectives = event_data["commands"]["cleanup"]
    except:
        write_to_log_file(f"Error couldn't parse cleanup objectives. Check Event JSON format.")

    for objective in cleanup_objectives:
        cleanup_objective_cmd = f'scoreboard objectives remove {objective}'
        result_cleanup = mcrcon_wrapper(cleanup_objective_cmd)
        write_to_log_file(f"Cleaned up objective {objective} with result: {result_cleanup}")

    print("✅ Event has been cleaned up!")
    write_to_log_file(f"✅ Event has been cleaned up!")


def write_event_winner(event_data, leaders, final_score):
 
    # Format filename: Event-Name-MM-DD-YYYY.json
    date_str = datetime.now().strftime("%m-%d-%Y")
    safe_event_name = event_data['name'].replace(" ", "-")
    filename = f"{safe_event_name}-{date_str}.json"
    filepath = os.path.join(logs_path, filename)
    
    # Prepare JSON data
    output_data = {
        "Event": event_data['name'],
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Description": event_data.get("description", ""),
        "Leaders": leaders,
        "FinalScore": final_score
    }
    
    # Write JSON file
    try:
        with open(filepath, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"✅ Event results saved to {filepath}")
    except Exception as e:
        print(f"❌ Failed to save event results: {e}")

#Give the winnig players their reward item!
def give_reward_item(winners, event_data):

    get_online_players_cmd = "list"
    result_get_online_players = mcrcon_wrapper(get_online_players_cmd)
    write_to_log_file(f"Queried for online players with result: {result_get_online_players}")

    # Regex search for just the player list
    get_player_pattern = r"online:\s*(.+)$"
    match = re.search(get_player_pattern, result_get_online_players[0])
    if match:
        online_players = [p.strip() for p in match.group(1).split(",")]
    else:
        write_to_log_file(f"Couldn't match the online players list with result: {result_get_online_players}")

    # Make a list of winners who are also online, do it for offline player too
    online_winners = [player for player in online_players if player in winners]
    offline_winners = [player for player in winners if player not in online_players]
    write_to_log_file(f"Found online players: {online_winners}")

    for winner in winners:
        if winner in online_winners:
            winning_text_event = f'tellraw {winner} "You have won the {event_data["name"]} event!"'
            winning_text_prize = f'tellraw {winner} "You will be recieving your prize in..."'
            winnig_text_countdown_3 = f'tellraw {winner} "3!"'
            winnig_text_countdown_2 = f'tellraw {winner} "2!"'
            winnig_text_countdown_1 = f'tellraw {winner} "1!"'
            
            # Get winner item
            item_gen_str = f'give {winner} ' + event_data["reward_cmd"]
            item_gen_str = item_gen_str.replace("'", '"')

            # Item notification
            item_name_text = f"You have been given the legendary {event_data["reward_name"]}!"
            item_json = {"text": item_name_text, "color": "light_purple"}
            item_won_text = f'tellraw {winner} {json.dumps(item_json)}'

            result_winning_event = mcrcon_wrapper(winning_text_event)
            time.sleep(1)
            result_winning_prize = mcrcon_wrapper(winning_text_prize)
            time.sleep(1)
            result_winning_countdown_3 = mcrcon_wrapper(winnig_text_countdown_3)
            time.sleep(1)
            result_winning_countdown_2 = mcrcon_wrapper(winnig_text_countdown_2)
            time.sleep(1)
            result_winning_countdown_1 = mcrcon_wrapper(winnig_text_countdown_1 )
            time.sleep(1)
            result_give_item = mcrcon_wrapper(item_gen_str)
            result_won_text = mcrcon_wrapper(item_won_text)

            write_to_log_file(f'Displayed winning event text to {winner} with result: {result_winning_event}')
            write_to_log_file(f'Displayed winning prize text to {winner} with result: {result_winning_prize}')
            write_to_log_file(f'Displayed winning count3 text to {winner} with result: {result_winning_countdown_3}')
            write_to_log_file(f'Displayed winning count2 text to {winner} with result: {result_winning_countdown_2}')
            write_to_log_file(f'Displayed winning count1 text to {winner} with result: {result_winning_countdown_1}')
            write_to_log_file(f'Gave item to {winner} with result: {result_give_item}')
            write_to_log_file(f'Displayed item recieved text to {winner} with result: {result_won_text}')

        else:
            pass
            #TODO: Handle notifying via discord bot when winner isn't online

    
    print(f"✅ Distrubted items to online winners and notified admins that {offline_winners} are offline!")
    write_to_log_file(f"✅ Distrubted items to online winners and notified admins that {offline_winners} are offline!")


#Displays the closing ceremony particles, sound and text and distributes items
def closing_ceremony(event_data):

    # Find the winner(s) and their score without displaying the chat message
    leader_list, leader_score = find_leaders(event_data, silent=True)

    #Event end text
    event_end_text = f"The {event_data['name']} event has ended!"
    json_end_text = {"text": event_end_text, "color": "gold"}
    end_text_cmd = f"tellraw @a {json.dumps(json_end_text)}"

    # Closing ceremony particles
    firework_particle_cmd = 'execute as @a at @s run particle minecraft:firework ~ ~ ~ 1 1 1 0.2 100 force'
    firework_sound_cmd = 'execute as @a at @s run playsound minecraft:entity.firework_rocket.twinkle master @s ~ ~ ~ 100'

    try:
        event_score_text = event_data["score_text"]
    except:
        write_to_log_file("Error. Couldn't get event score_text. Check event JSON.")

    # Event winner text
    winner_str = ", ".join(leader_list) + f" won the event with {leader_score} {event_score_text}"
    winner_str_json = {"text": winner_str, "color": "green"}
    winner_cmd = f"tellraw @a {json.dumps(winner_str_json)}"

    # Closing ceremony song
    ceremony_song_cmd = f'execute as @a at @s run playsound minecraft:music_disc.lava_chicken master @s ~ ~ ~ 100'
    ceremony_song_stop_cmd = 'stopsound @a'

    # Display event end text
    result_event_end = mcrcon_wrapper(end_text_cmd)
    write_to_log_file(f"Sent closing ceremony text to server with result {result_event_end}")

    #Display the firework effects
    for i in range(5):
        particle_result = mcrcon_wrapper(firework_particle_cmd)
        firework_sound_result = mcrcon_wrapper(firework_sound_cmd)
        write_to_log_file(f"Displayed closing ceremony particles with result {particle_result}")
        write_to_log_file(f"Displayed closing ceremony firework sounds with result {firework_sound_result}")
        time.sleep(0.3)

    # Display the winner(s)
    result_display_winner = mcrcon_wrapper(winner_cmd)
    write_to_log_file(f"Displayed the event winners with result {result_display_winner}")

    # Play the closing ceremony song and show the scoreboard
    ceremony_song_result = mcrcon_wrapper(ceremony_song_cmd)
    write_to_log_file(f"Started the ceremony song with result {ceremony_song_result}")
    display_scoreboard(event_data)
    
    # Stop the ceremony song
    ceremony_song_stop_result = mcrcon_wrapper(ceremony_song_stop_cmd)
    write_to_log_file(f"Stopped the ceremony song with result {ceremony_song_stop_result}")

    #Give out the reward items to online players
    give_reward_item(leader_list, event_data)

    #Write the event winner to event_results
    write_event_winner(event_data, leader_list, leader_score)

def run_event(action, json_file):
    # Load the requested json file
    try:
        event_data = load_json(f'{events_path}{json_file}')
    except:
        print(f"❌ Failed to load data for {json_file}. Check event JSON file exists")
        exit()

    # Start the event
    if action == "start":
        start_event(event_data)
    # Display the leaderboard for the event
    elif action == "display":
        aggregate_scores(event_data)
        find_leaders(event_data)
        display_scoreboard(event_data)
    # Stop the event, distribute prizes, and clean up the server
    elif action == "clean":
        # Calculate scores for everyone one last time
        aggregate_scores(event_data)
        closing_ceremony(event_data)
        cleanup_objs(event_data)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python rcon_event_framework.py <start|display|clean> <json-file>")
        sys.exit(1)

    action = sys.argv[1]
    json_file = sys.argv[2]

    run_event(action, json_file)