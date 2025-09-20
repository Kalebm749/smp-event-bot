import json
from datetime import datetime, timedelta, timezone

EVENT_FILE = "events.json"

# Current UTC time
now = datetime.utcnow().replace(tzinfo=timezone.utc)

# Event starts 24 hours and 30 seconds from now
start_time = now + timedelta(hours=24, seconds=30)
end_time = start_time + timedelta(hours=1)  # lasts 1 hour

event_24h = {
    "name": "24h Test Event",
    "description": "This event is a 24-hour notification test.",
    "start": start_time.isoformat(),
    "end": end_time.isoformat(),
    "notif_24h": False,
    "notif_30m": False,
    "notif_start": False,
    "notif_end": False
}

# Save to events.json
with open(EVENT_FILE, "w") as f:
    json.dump([event_24h], f, indent=2)

print(f"Event created! Starts at {start_time} UTC, ends at {end_time} UTC.")
