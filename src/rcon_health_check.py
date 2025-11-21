#!/usr/bin/env python3
"""
RCON Health Check Script
Simple standalone script to test RCON connectivity without threading issues.
"""

import sys
import os
import json
from dotenv import load_dotenv
from mcrcon import MCRcon

def check_rcon_health():
    """Check RCON connectivity and return status as JSON"""
    load_dotenv()
    
    try:
        # Get RCON configuration
        rcon_host = os.getenv("RCON_HOST")
        rcon_port = int(os.getenv("RCON_PORT", 25575))
        rcon_pass = os.getenv("RCON_PASS")
        
        if not all([rcon_host, rcon_port, rcon_pass]):
            return {
                "healthy": False,
                "status": "error",
                "error": "RCON configuration incomplete"
            }
        
        # Test RCON connection
        with MCRcon(rcon_host, rcon_pass, port=rcon_port) as mcr:
            result = mcr.command("list")
        
        if result and len(result.strip()) > 0:
            return {
                "healthy": True,
                "status": "connected",
                "result": result.strip(),
                "message": "RCON connection successful"
            }
        else:
            return {
                "healthy": False,
                "status": "error",
                "error": "RCON command returned empty result"
            }
            
    except Exception as e:
        return {
            "healthy": False,
            "status": "error",
            "error": f"RCON connection failed: {str(e)}"
        }

if __name__ == "__main__":
    result = check_rcon_health()
    print(json.dumps(result))
    sys.exit(0 if result["healthy"] else 1)