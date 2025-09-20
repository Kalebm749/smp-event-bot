import json
from datetime import datetime, timedelta, timezone

EVENT_FILE = "events.json"

# Current UTC time
now = datetime.utcnow().replace(tzinfo=timezone.utc)

# Event starts in 2 minutes
start_time = now + timedelta(minutes=2)
end_time = start_time + timedelta(minutes=5)  # lasts 5 minutes

test_event = {
    "name": "Test Quick Event",
    "description": "This is a quick test event for notifications.",
    "start": start_time.isoformat(),
    "end": end_time.isoformat(),
    "notif_24h": False,
    "notif_30m": False,
    "notif_start": False,
    "notif_end": False
}

# Save to events.json
with open(EVENT_FILE, "w") as f:
    json.dump([test_event], f, indent=2)

print(f"Test event created! Starts at {start_time} UTC, ends at {end_time} UTC.")
