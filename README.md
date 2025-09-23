# SMP-Event-Orchestrator

**SMP-Event-Orchestrator** is a tool that brings fun and automated multiplayer events into your Minecraft server using RCON and vanilla scoreboard commands.  
It also integrates with Discord, allowing you to schedule, monitor, and manage custom events directly from a web-based Admin GUI.  

This project makes it possible to run complex, repeatable events within the vanilla confines of the game—without the need for plugins or mods.  

---

## ✨ Features

- **Admin GUI**  
  A clean, browser-based interface with verbose logging and an event scheduler.  

- **Authentication**  
  Secure login system with admin password and session secret key.  

- **Cross-Platform**  
  Works on both Windows and Linux servers.  

- **Event Automation**  
  Automates event lifecycle:
  - Start & stop events  
  - Scoreboard display  
  - Cleanup after events  
  - Winner calculation and reward distribution  

- **Discord Integration**  
  Automatically posts event notifications to a Discord server using a bot.  

---

## ⚙️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/SMP-Event-Orchestrator.git
   cd SMP-Event-Orchestrator
   ```
2. Create a Python virtual environment:
  ```bash
    python3 -m venv venv
    source venv/bin/activate   # On Linux / macOS
    venv\Scripts\activate      # On Windows
  ```
3. Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
4.Make and configure your .env file in the base directory:
  ```bash
  touch .env
  # Open with text editor of your choice and fill in the following
  # Tokens for discord bot
  DISCORD_TOKEN=
  ADMIN_ID=
  GUILD_ID=
  EVENT_CHANNEL_ID=

  # File paths - defaults provided
  CALENDAR_FILE=./events/events_calendar/event_calendar.json
  EVENTS_JSON_PATH=./events/events_json/
  LOGS_PATH=./logs/

  # RCON info
  RCON_HOST=
  RCON_PORT=
  RCON_PASS=

  # Admin password for webgui and secret key for sessions
  ADMIN_PASSWORD=
  SECRET_KEY=
```

## Usage
1. Start the Flask app:
  ```bash
  python app.py
  ```
2. Open the Admin GUI in your browser to schedule and monitor events.
3. View logs in real-time via the Event Monitor page.
4. Play Minecraft and enjoy your automated, custom server events.

## License

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
