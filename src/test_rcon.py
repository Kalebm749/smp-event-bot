#!/usr/bin/env python3
from mcrcon import MCRcon

# Update these with your server's details
RCON_HOST = "73.95.116.62"   # IP of your Raspberry Pi
RCON_PORT = 25575            # Default RCON port
RCON_PASS = "1234"

try:
    with MCRcon(RCON_HOST, RCON_PASS, port=RCON_PORT) as mcr:
        resp = mcr.command("list")  # Ask server for online players
        print("RCON connection successful!")
        print("Server response:", resp)
except Exception as e:
    print("RCON connection failed:")
    print(e)
