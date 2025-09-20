import discord
import asyncio
import json
import os
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# ====== LOAD CONFIG ======
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("EVENT_CHANNEL_ID"))
EVENT_FILE = os.getenv("EVENT_FILE")
LOG_FILE = "event_bot.log"

# ====== SETUP LOGGING ======
logger = logging.getLogger("EventBot")
logger.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)

# File handler
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

# ====== DISCORD CLIENT ======
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ====== HELPER FUNCTIONS ======
async def send_event_embed(channel, event, message_text, include_description=False):
    start_time = datetime.fromisoformat(event["start"])
    end_time = datetime.fromisoformat(event["end"])

    embed = discord.Embed(
        title=event["name"],
        color=discord.Color.blue()
    )

    if include_description and "description" in event:
        embed.description = event["description"]

    embed.add_field(
        name="Notification",
        value=message_text,
        inline=False
    )

    embed.add_field(
        name="Starts",
        value=f"<t:{int(start_time.timestamp())}:F>\n<t:{int(start_time.timestamp())}:R>",
        inline=False
    )
    embed.add_field(
        name="Ends",
        value=f"<t:{int(end_time.timestamp())}:F>\n<t:{int(end_time.timestamp())}:R>",
        inline=False
    )

    await channel.send(embed=embed)
    logger.info(f"Notification sent for event '{event['name']}': {message_text}")

def load_events():
    try:
        with open(EVENT_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_events(events):
    with open(EVENT_FILE, "w") as f:
        json.dump(events, f, indent=2)

# ====== EVENT LOOP ======
async def event_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            events = load_events()
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            changed = False
            action_taken = False

            for event in events[:]:  # iterate over a copy for safe removal
                start_time = datetime.fromisoformat(event["start"])
                end_time = datetime.fromisoformat(event["end"])

                # 24h before
                if now >= start_time - timedelta(hours=24) and not event.get("notif_24h", False):
                    message_text = "📅 This event will start in **24 hours**!"
                    await send_event_embed(
                        channel,
                        event,
                        message_text,
                        include_description=True
                    )
                    event["notif_24h"] = True
                    changed = True
                    action_taken = True

                    # Special log if overdue
                    if now > start_time - timedelta(hours=24):
                        logger.info(f"Event '{event['name']}' 24-hour notification sent immediately (overdue).")

                # 30m before
                if now >= start_time - timedelta(minutes=30) and not event.get("notif_30m", False):
                    await send_event_embed(channel, event, "⏰ This event will start in **30 minutes**!", include_description=True)
                    event["notif_30m"] = True
                    changed = True
                    action_taken = True

                # Start
                if now >= start_time and not event.get("notif_start", False):
                    await send_event_embed(channel, event, "✅ This event has **started**!", include_description=True)
                    event["notif_start"] = True
                    changed = True
                    action_taken = True

                # End
                if now >= end_time and not event.get("notif_end", False):
                    await send_event_embed(channel, event, "❌ This event has **ended**!", include_description=True)
                    event["notif_end"] = True
                    changed = True
                    action_taken = True

                # Cleanup: remove event 20 minutes after it ends
                if now >= end_time + timedelta(minutes=20):
                    events.remove(event)
                    changed = True
                    action_taken = True
                    logger.info(f"Event '{event['name']}' removed after 20 minutes.")

            if changed:
                save_events(events)

            # Only log if something happened this loop
            if action_taken:
                logger.info("Event loop iteration completed with actions.\n")

        except Exception as e:
            logger.error(f"Error in event loop: {e}")

        await asyncio.sleep(60)  # check every 60 seconds

# ====== START BOT ======
@client.event
async def on_ready():
    logger.info(f"✅ Bot is online as {client.user}")
    client.loop.create_task(event_loop())

client.run(TOKEN)
