import json
import time
import sys
from mcrcon import MCRcon # type: ignore
from datetime import datetime
import re

# --- RCON settings ---
rcon_host = "10.0.0.70"
rcon_port = 25575
rcon_pass = "1234"


def load_json(event_file):
    with open(event_file, "r") as f:
        event_data = json.load(f)

    return event_data


def escape_mc_string(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def write_to_log_file(result):
    log_file_path = '../framework_logs/event_logs.txt'

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

    for player in player_list:
        # Set aggregate scoreboard objective to zero
        aggregate_to_zero = f"scoreboard players set {player} {agg_obj} 0"
        result_to_zero = mcrcon_wrapper(aggregate_to_zero)
        write_to_log_file(f"Got the following result setting {agg_obj} to 0 for {player}: {result_to_zero}")

        for objective in objectives:
            aggregate_scores_additive_cmd = f"scoreboard players operation {player} {agg_obj} += {player} {objective}"
            additive_result = mcrcon_wrapper(aggregate_scores_additive_cmd)
            write_to_log_file(f"Got the following result aggregating {agg_obj} with {objective} for {player}: {additive_result}")

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
            print(f"LEADING SCORE {number}")
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

    with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
        result = mcr.command(f'scoreboard objectives setdisplay sidebar {event_data["aggregate_objective"]}')

        print(f"Displaying the scoreboard for {event_data["sidebar"]["duration"]} seconds")
        time.sleep(event_data["sidebar"]["duration"])

        result = mcr.command("scoreboard objectives setdisplay sidebar")

    print("✅ Scoreboard was displayed")

# Remove anything related to the event
def cleanup_objs(event_data):
    objectives = event_data["commands"]["cleanup"]

    with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
        for objective in objectives:
            result = mcr.command(f"scoreboard objectives remove {objective}")
            print(result)

    print("✅ Event has been cleaned up!")

def write_event_winner(event_data, leaderstr, leader_scr):
    """Write final event results to a text file"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{event_data['name']}_{timestamp}.txt"
    filepath = f'../event_results/{filename}'

    with open(filepath, "w") as f:
        f.write(f"Event: {event_data['name']}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Description: {event_data.get('description','')}\n\n")
        f.write("Leaders:\n")
        f.write(f"{leaderstr}\n\n")
        f.write(f"Final Score: {leader_scr}\n")




#Give the winnig players their reward item!
def give_reward_item(winners, event_data):

    # Check the list of online players so that we don't give a prize to a non-online player
    with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
        player_list = mcr.command("list")
        print(player_list)

    get_player_pattern = r"online:\s*(.+)$"
    match = re.search(get_player_pattern, player_list)
    if match:
        online_players = [p.strip() for p in match.group(1).split(",")]
    else:
        print(f"Error: couldn't match online players: {player_list}")

    # Make a list of winners who are also online
    online_winners = [player for player in online_players if player in winners]
    print(online_winners)

    for winner in winners:
        if winner in online_winners:
            with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
                mcr.command(f'tellraw {winner} "You have won the {event_data["name"]} event!"')
                time.sleep(1)
                mcr.command(f'tellraw {winner} "You will be recieving your prize in..."')
                time.sleep(1)
                mcr.command(f'tellraw {winner} "3!"')
                time.sleep(1)
                mcr.command(f'tellraw {winner} "2!!"')
                time.sleep(1)
                mcr.command(f'tellraw {winner} "1!!!"')
                time.sleep(1)
                item_gen_str = f'give {winner} ' + event_data["reward_cmd"]
                item_gen_str = item_gen_str.replace("'", '"')
                print(item_gen_str)
                result = mcr.command(item_gen_str)
                print(result)
                mcr.command(f'tellraw {winner} "You have been rewared with the legendary {event_data['reward_name']}"!!!')
        else: 
            pass
        #TODO: Handle notifying via discord bot when winner isn't online

def run_event(action, json_file):
    event_data = load_json(f'../events_json/{json_file}')

    if action == "start":
        start_event(event_data)
    elif action == "display":
        aggregate_scores(event_data)
        find_leaders(event_data)
        display_scoreboard(event_data)
    elif action == "clean":
        aggregate_scores(event_data)
        leader_str, leader_scr = find_leaders(event_data, silent=True)
        print(leader_str)
        with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
                event_end_text = f"The {event_data['name']} event has ended!"
                for i in range(5):
                    mcr.command('execute at @p run particle minecraft:firework ~ ~ ~ 1 1 1 0.2 100 force')
                    mcr.command('execute as @a at @s run playsound minecraft:entity.firework_rocket.twinkle master @s ~ ~ ~ 100')
                    time.sleep(0.3)
                json_end_text = {"text": event_end_text, "color": "gold"}
                display_end_text = f"tellraw @a {json.dumps(json_end_text)}"
                result = mcr.command(display_end_text)
                winner_str = ", ".join(leader_str) + f" won the event with {leader_scr} {event_data["score_text"]}!"
                winner_str_json = {"text": winner_str, "color": "green"}
                display_winner_text = f"tellraw @a {json.dumps(winner_str_json)}"
                result = mcr.command(display_winner_text)
                result = mcr.command('execute as @a at @s run playsound minecraft:music_disc.lava_chicken master @s ~ ~ ~ 100')
                display_scoreboard(event_data)
                result = mcr.command('stopsound @a')
                give_reward_item(leader_str, event_data)
        write_event_winner(event_data, leader_str, leader_scr)
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