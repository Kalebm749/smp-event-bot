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

def get_players():
    with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
        player_list = mcr.command("scoreboard players list")
        match = re.search(r"There are \d+ tracked entity/entities: (.+)", player_list)
        if match:
            return match.group(1).split(", ")
        return []


def start_event(event_data):

    # Grab the event start text and format it
    event_start_text = f"The {event_data['name']} event is starting"
    json_start_text = {"text": event_start_text, "color": "gold"}
    display_title_text = f"tellraw @a {json.dumps(json_start_text)}"

    # Grab the event description text and format it
    event_description_text = f"{event_data['description']}"
    json_desc_text = {"text": event_description_text, "color": "aqua"}
    display_description_text = f"tellraw @a {json.dumps(json_desc_text)}"

    #Grab the setup commands
    event_setup_commands = event_data["commands"]["setup"]

    with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
        result = mcr.command(display_title_text)
        print(f"Command Return = {result} : Sent String {display_title_text}")

        for i in range(9):
            result = mcr.command('execute as @a at @s run playsound minecraft:block.bell.use master @s ~ ~ ~ 100')
            time.sleep(0.25)

        result = mcr.command(display_description_text)
        print(f"Command Return = {result} : Sent String {display_description_text}")

        result = mcr.command('execute as @a at @s run playsound minecraft:entity.wither.death master @s ~ ~ ~ 100')

        for cmd in event_setup_commands:
            result = mcr.command(cmd)
            print(f"Command Return = {result} : Sent String {cmd}")

    print("✅ Event Setup Completed")


#Runs all of the aggregate commands for all players
def aggregate_scores(event_data):
    #Grab a list of all the players
    player_list = get_players()

    #Grabs the aggregate objective
    agg_obj = event_data["aggregate_objective"]

    #Grab the objectives to aggregate on
    objectives = event_data["commands"]["aggregate"]
    #print(objectives)

    with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
        for player in player_list:
            result = mcr.command(f"scoreboard players set {player} {agg_obj} 0")
            #print(result)
            for objective in objectives:
                result = mcr.command(f"scoreboard players operation {player} {agg_obj} += {player} {objective}")
                #print(result)

    print("✅ Calculated Aggregate Scores")

#Looks through the scoreboard objectives to find the leaders
def find_leaders(event_data, silent=False):
    player_list = get_players()

    main_obj = event_data["aggregate_objective"]

    leaders = []
    leading_score = 0

    with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
        for player in player_list:
            result = mcr.command(f"scoreboard players get {player} {main_obj}")
            #print(result)
            match = re.search(r"has (\d+)", result)
            if match:
                number = int(match.group(1))
                #print(number)
                if not leaders:
                    leaders.append(player)
                elif number == leading_score:
                    leaders.append(player)
                elif number > leading_score:
                    leaders = []
                    leaders.append(player)
                    leading_score = number
            else:
                print(f"Error getting score for {player}")

        #print(leaders)

        #Tell the server whos winning
        player_string = ""
        for leads in leaders:
            player_string += f"{leads}, "
            if len(leaders) == 1:
                player_string = leads

        if player_string.endswith(", "):
            player_string = player_string[:-2]

        if len(leaders) == 1:
            player_string += f" is leading the pack for the {event_data["name"]} event with a score of {leading_score} {event_data["score_text"]}!"
        else:
            player_string += f" are tied for first in the {event_data["name"]} event with scores of {leading_score} {event_data["score_text"]}!"

        leader_string = {"text": player_string, "color": "gold"}
        leader_cmd = f"tellraw @a {json.dumps(leader_string)}"

        if not silent:
            result = mcr.command(leader_cmd)
    
    print("✅ Displayed leaders!")
    return leaders, leading_score

#Displays the scordboard for a set amount of time
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
    for winner in winners:
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