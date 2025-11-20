#!/usr/bin/env python3
import discord
import json
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import sql_calendar

# ====== LOAD CONFIG ======
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("EVENT_CHANNEL_ID"))

# ====== DISCORD CLIENT ======
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ====== HELPER: FIND EVENT IN DATABASE ======
def find_event_by_unique_name(unique_name):
    """Find event in database by unique name"""
    try:
        event_id = sql_calendar.get_event_id_by_unique_name(unique_name)
        if not event_id:
            return None
            
        event_data = sql_calendar.get_event_by_id(event_id)
        if not event_data:
            return None
            
        # Convert database row to dict format expected by bot
        event = {
            "unique_event_name": event_data[1],  # unique_event_name
            "name": event_data[2],               # name
            "event_json": event_data[3],         # event_json
            "description": event_data[4],        # description
            "start": event_data[5],              # start_time
            "end": event_data[6],                # end_time
            "event_in_progress": bool(event_data[7]),
            "event_started": bool(event_data[8]),
            "event_over": bool(event_data[9])
        }
        
        sql_calendar.log_message(f"Found event for Discord notification: {unique_name}")
        return event
        
    except Exception as e:
        sql_calendar.log_message(f"Error finding event {unique_name}: {e}", "ERROR")
        return None

# ====== HELPER: EMBEDS ======
def build_embed(event, msg_type, winners=None, score=None):
    # Handle both old ISO format and new Z format
    start_str = event["start"]
    end_str = event["end"]
    
    # Convert Z format to standard ISO format for parsing
    if start_str.endswith('Z'):
        start_str = start_str.replace('Z', '+00:00')
    if end_str.endswith('Z'):
        end_str = end_str.replace('Z', '+00:00')
    
    start_time = datetime.fromisoformat(start_str)
    end_time = datetime.fromisoformat(end_str)

    embed = discord.Embed(
        title=event["name"],
        color=discord.Color.blue()
    )

    if "description" in event and event["description"]:
        embed.description = event["description"]

    if msg_type == "twenty_four":
        embed.add_field(name="Notification", value="📅 This event will start in **24 hours**!", inline=False)

    elif msg_type == "thirty":
        return f"⏰ Reminder: **{event['name']}** will begin in 30 minutes!"

    elif msg_type == "now":
        embed.add_field(name="Notification", value="✅ This event has **started**!", inline=False)

    elif msg_type == "over":
        embed.add_field(name="Status", value="⏹ This event has ended!", inline=False)
        if winners and winners[0] == "no_Participants":
            embed.add_field(name="❌ There are no winners. Nobody participated in the event :(", value="", inline=False)
        elif winners:
            embed.add_field(name="🏆 Winners", value="\n".join(winners), inline=False)
        if score:
            embed.add_field(name="Score(s)", value=score, inline=False)

    # Add times for everything *except* "over"
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
        sql_calendar.log_message("Bot called with insufficient arguments", "ERROR")
        await client.close()
        return

    cmd = sys.argv[1]
    unique_name = sys.argv[2]
    
    # Find event in database instead of JSON file
    event = find_event_by_unique_name(unique_name)

    if not event:
        error_msg = f"Event '{unique_name}' not found in database"
        print(error_msg)
        sql_calendar.log_message(error_msg, "ERROR")
        await client.close()
        return

    try:
        if cmd == "twenty_four":
            embed = build_embed(event, "twenty_four")
            await channel.send(embed=embed)
            sql_calendar.log_message(f"Sent 24h notification for {unique_name}")

        elif cmd == "thirty":
            msg = build_embed(event, "thirty")
            await channel.send(msg)
            sql_calendar.log_message(f"Sent 30min notification for {unique_name}")

        elif cmd == "now":
            embed = build_embed(event, "now")
            await channel.send(embed=embed)
            sql_calendar.log_message(f"Sent start notification for {unique_name}")

        elif cmd == "over":
            if len(sys.argv) < 5:
                print("Usage: ./bot.py over <unique_event_name> <winner1,winner2,...> <score>")
                await client.close()
                return

            winners = [w.strip() for w in sys.argv[3].split(",") if w.strip()]
            score = sys.argv[4]

            embed = build_embed(event, "over", winners, score)
            await channel.send(embed=embed)
            sql_calendar.log_message(f"Sent end notification for {unique_name} - Winners: {winners}")

        else:
            error_msg = f"Unknown command: {cmd}"
            print(error_msg)
            sql_calendar.log_message(error_msg, "ERROR")

    except Exception as e:
        error_msg = f"Error sending Discord notification: {e}"
        print(error_msg)
        sql_calendar.log_message(error_msg, "ERROR")

    await client.close()

# ====== RUN BOT ======
if __name__ == "__main__":
    client.run(TOKEN)
