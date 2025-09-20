import json

def load_json(event_file):
    with open(event_file, "r") as f:
        event_data = json.load(f)

    return event_data

x = load_json('../events_json/ExampleEvent.json')

print(x['reward_cmd'])