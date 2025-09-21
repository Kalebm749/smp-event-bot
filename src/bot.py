#!/usr/bin/env python3
import discord
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# ====== LOAD CONFIG ======
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("EVENT_CHANNEL_ID"))
CALENDAR_FILE = os.getenv("CALENDAR_FILE")

# ====== DISCORD CLIENT ======
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ====== HELPER: LOAD EVENTS ======
def load_events():
    try:
        with open(CALENDAR_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def find_event(unique_name):
    events = load_events()
    for event in events:
        if event["unique_event_name"] == unique_name:
            return event
    return None

# ====== HELPER: EMBEDS ======
def build_embed(event, msg_type, winners=None, score=None):
    start_time = datetime.fromisoformat(event["start"])
    end_time = datetime.fromisoformat(event["end"])

    embed = discord.Embed(
        title=event["name"],
        color=discord.Color.blue()
    )

    if "description" in event:
        embed.description = event["description"]

    if msg_type == "twenty_four":
        embed.add_field(name="Notification", value="📅 This event will start in **24 hours**!", inline=False)

    elif msg_type == "thirty":
        return f"⏰ Reminder: **{event['name']}** will begin in 30 minutes!"

    elif msg_type == "now":
        embed.add_field(name="Notification", value="✅ This event has **started**!", inline=False)

    elif msg_type == "over":
        embed.add_field(name="Status", value="❌ This event has ended!", inline=False)
        if winners[0] == "no_Participants":
            embed.add_field(name="❌ There are no winners. Nobody participated in the event :(", value="", inline=False)
        elif winners:
            embed.add_field(name="🏆 Winners", value="\n".join(winners), inline=False)
        if score:
            embed.add_field(name="Score(s)", value=score, inline=False)

    # add times for everything *except* "over"
    if msg_type in ("twenty_four", "now"):
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

    return embed

# ====== MAIN SEND LOGIC ======
@client.event
async def on_ready():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        channel = await client.fetch_channel(CHANNEL_ID)

    if len(sys.argv) < 3:
        print("Usage: ./bot.py <twenty_four|thirty|now|over> <unique_event_name> [winners] [score]")
        await client.close()
        return

    cmd = sys.argv[1]
    unique_name = sys.argv[2]
    event = find_event(unique_name)

    if not event:
        print(f"Event '{unique_name}' not found in {CALENDAR_FILE}")
        await client.close()
        return

    if cmd == "twenty_four":
        embed = build_embed(event, "twenty_four")
        await channel.send(embed=embed)

    elif cmd == "thirty":
        msg = build_embed(event, "thirty")
        await channel.send(msg)

    elif cmd == "now":
        embed = build_embed(event, "now")
        await channel.send(embed=embed)

    elif cmd == "over":
        if len(sys.argv) < 5:
            print("Usage: ./bot.py over <unique_event_name> <winner1,winner2,...> <score>")
            await client.close()
            return

        winners = [w.strip() for w in sys.argv[3].split(",") if w.strip()]
        score = sys.argv[4]

        embed = build_embed(event, "over", winners, score)
        await channel.send(embed=embed)

    else:
        print(f"Unknown command: {cmd}")

    await client.close()

# ====== RUN BOT ======
client.run(TOKEN)
