import subprocess
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response, flash
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone
from functools import wraps
import pytz
import platform
import sys
import socket
import re
from mcrcon import MCRcon

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import sql_calendar
from database_manager import db_manager

load_dotenv()
PASSWORD = os.getenv("ADMIN_PASSWORD")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Database paths
DATABASE_FILE = os.getenv("DATABASE_FILE", "event_database.db")
DATABASE_DIR = os.getenv("DATABASE_DIR", "./database/")
DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA", "schema.sql")
DATABASE_PATH = os.path.join(DATABASE_DIR, DATABASE_FILE)
SCHEMA_PATH = os.path.join(DATABASE_DIR, DATABASE_SCHEMA)

# Other paths
EVENTS_JSON_PATH = os.path.join(".", "events", "events_json")
LOGS_PATH = os.path.join(".", "logs")

def get_db():
    """Get database manager instance"""
    return db_manager(DATABASE_PATH, SCHEMA_PATH)

def start_event_handler():
    try:
        if not is_event_handler_running():
            if platform.system() == "Windows":
                subprocess.Popen(["python", "./src/event_handler.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["python3", "./src/event_handler.py"])
            return True
        return False
    except Exception as e:
        print("Error starting event handler:", e)
        return False

def stop_event_handler():
    try:
        if is_event_handler_running():
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "python.exe"])
            else:
                subprocess.run(["pkill", "-f", "event_handler.py"])
            return True
        return False
    except Exception as e:
        print("Error stopping event handler:", e)
        return False

def is_event_handler_running():
    """Check if 'event_handler.py' is running."""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["tasklist"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return "event_handler.py" in result.stdout
        else:  # Linux
            result = subprocess.run(
                ["pgrep", "-f", "event_handler.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            return result.returncode == 0
    except Exception as e:
        print("Error checking event handler:", e)
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def load_events_from_db():
    """Load events from SQLite database"""
    try:
        db = get_db()
        query = """
        SELECT id, unique_event_name, name, event_json, description, 
               start_time, end_time, event_in_progress, event_started, 
               event_over, last_scoreboard_time
        FROM events 
        ORDER BY start_time DESC
        """
        results = db.db_query(query)
        
        events = []
        for row in results:
            event = {
                "id": row[0],
                "unique_event_name": row[1],
                "name": row[2],
                "event_json": row[3],
                "description": row[4],
                "start": row[5],
                "end": row[6],
                "event_in_progress": bool(row[7]),
                "event_started": bool(row[8]),
                "event_over": bool(row[9]),
                "last_scoreboard_time": row[10]
            }
            events.append(event)
        
        return events
    except Exception as e:
        print(f"Error loading events from database: {e}")
        return []

def load_event_files():
    """Load event JSON files"""
    if os.path.exists(EVENTS_JSON_PATH):
        return [f for f in os.listdir(EVENTS_JSON_PATH) if f.endswith(".json")]
    return []

def load_logs_from_db():
    """Load recent logs from database"""
    try:
        db = get_db()
        query = """
        SELECT timestamp, message, log_level 
        FROM logs 
        ORDER BY timestamp DESC 
        LIMIT 100
        """
        results = db.db_query(query)
        
        logs = []
        for row in results:
            logs.append({
                "timestamp": row[0],
                "message": row[1],
                "log_level": row[2]
            })
        
        return logs
    except Exception as e:
        print(f"Error loading logs from database: {e}")
        return []

def get_event_status(event):
    """Determine event status"""
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(event["start"].replace('Z', '+00:00'))
    end = datetime.fromisoformat(event["end"].replace('Z', '+00:00'))
    
    if event.get("event_over"):
        return "completed"
    elif event.get("event_in_progress"):
        return "ongoing"
    elif start > now:
        return "future"
    elif start <= now <= end:
        return "should_be_ongoing"
    else:
        return "past"

# Routes
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            flash("Invalid password")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/api/calendar")
@login_required
def api_calendar():
    events = load_events_from_db()
    for e in events:
        e["status"] = get_event_status(e)
    return jsonify(events)

@app.route("/event_monitor")
@login_required
def event_monitor():
    return render_template("event_monitor.html")

@app.route("/database_viewer")
@login_required
def database_viewer():
    """New database viewer page"""
    return render_template("database_viewer.html")

@app.route("/api/health/minecraft")
@login_required
def api_minecraft_health():
    """Check if Minecraft server is reachable"""
    try:
        # Get host from environment (default to localhost if not set)
        rcon_host = os.getenv("RCON_HOST")
        if not rcon_host:
            return jsonify({
                "healthy": False,
                "status": "error",
                "error": "RCON_HOST not configured in .env"
            })
        
        # Try to connect to the server port (usually 25565)
        minecraft_port = 25565  # Standard Minecraft port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        
        result = sock.connect_ex((rcon_host, minecraft_port))
        sock.close()
        
        if result == 0:
            return jsonify({
                "healthy": True,
                "status": "online",
                "message": f"Server at {rcon_host}:{minecraft_port} is reachable"
            })
        else:
            return jsonify({
                "healthy": False,
                "status": "offline",
                "error": f"Cannot connect to {rcon_host}:{minecraft_port}"
            })
            
    except Exception as e:
        return jsonify({
            "healthy": False,
            "status": "error",
            "error": str(e)
        })

@app.route("/api/health/rcon")
@login_required 
def api_rcon_health():
    """Check if RCON connection is working using external script"""
    try:
        # Run the external RCON health check script
        import subprocess
        
        script_path = os.path.join("src", "rcon_health_check.py")
        
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_path], 
            capture_output=True, 
            text=True, 
            timeout=10  # 10 second timeout
        )
        
        if result.returncode == 0:
            # Parse the JSON output from the script
            import json
            health_data = json.loads(result.stdout.strip())
            return jsonify(health_data)
        else:
            # Script failed, try to parse error output
            try:
                error_data = json.loads(result.stdout.strip())
                return jsonify(error_data)
            except:
                return jsonify({
                    "healthy": False,
                    "status": "error",
                    "error": f"RCON health check script failed: {result.stderr or 'Unknown error'}"
                })
                
    except subprocess.TimeoutExpired:
        return jsonify({
            "healthy": False,
            "status": "error",
            "error": "RCON health check timed out"
        })
    except Exception as e:
        return jsonify({
            "healthy": False,
            "status": "error",
            "error": f"Failed to run RCON health check: {str(e)}"
        })
    
@app.route("/api/health/overall")
@login_required
def api_overall_health():
    """Get overall system health status"""
    try:
        # Check both Minecraft and RCON
        minecraft_response = api_minecraft_health()
        rcon_response = api_rcon_health()
        
        minecraft_data = minecraft_response.get_json()
        rcon_data = rcon_response.get_json()
        
        minecraft_healthy = minecraft_data.get("healthy", False)
        rcon_healthy = rcon_data.get("healthy", False)
        
        overall_healthy = minecraft_healthy and rcon_healthy
        
        issues = []
        if not minecraft_healthy:
            issues.append("Minecraft Server")
        if not rcon_healthy:
            issues.append("RCON Connection")
        
        return jsonify({
            "healthy": overall_healthy,
            "minecraft": minecraft_data,
            "rcon": rcon_data,
            "issues": issues,
            "status": "All systems operational" if overall_healthy else f"Issues: {', '.join(issues)}"
        })
        
    except Exception as e:
        return jsonify({
            "healthy": False,
            "status": "error",
            "error": str(e)
        })

@app.route("/api/database/info")
@login_required
def api_database_info():
    """Get database information"""
    try:
        db = get_db()
        info = db.db_info()
        
        # Add file size info
        if os.path.exists(DATABASE_PATH):
            file_size = os.path.getsize(DATABASE_PATH)
            info["size_bytes"] = file_size
            info["size_mb"] = round(file_size / 1024 / 1024, 2)
        
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/database/table/<table_name>")
@login_required
def api_table_data(table_name):
    """Get data from a specific table"""
    allowed_tables = ["events", "event_notifications", "logs", "event_winners"]
    if table_name not in allowed_tables:
        return jsonify({"error": "Table not allowed"}), 400
    
    try:
        db = get_db()
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM {table_name}"
        count_result = db.db_query(count_query)
        total = count_result[0][0] if count_result else 0
        
        # Get table data with pagination
        query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit} OFFSET {offset}"
        results = db.db_query(query)
        
        # Get column names
        column_query = f"PRAGMA table_info({table_name})"
        column_info = db.db_query(column_query)
        columns = [col[1] for col in column_info]  # col[1] is the column name
        
        # Format results
        rows = []
        for row in results:
            row_dict = {}
            for i, col_name in enumerate(columns):
                row_dict[col_name] = row[i]
            rows.append(row_dict)
        
        return jsonify({
            "table": table_name,
            "columns": columns,
            "rows": rows,
            "total": total,
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/database/enhanced-table/<table_name>")
@login_required
def api_enhanced_table_data(table_name):
    """Get enhanced table data with joined event names for notifications and winners"""
    allowed_tables = ["event_notifications", "event_winners"]
    if table_name not in allowed_tables:
        return jsonify({"error": "Table not allowed"}), 400
    
    try:
        db = get_db()
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        if table_name == "event_notifications":
            # Join with events table to get event name
            query = f"""
            SELECT n.id, n.event_id, e.unique_event_name, e.name as event_name, 
                   n.notification_type, n.sent_at
            FROM event_notifications n
            JOIN events e ON n.event_id = e.id
            ORDER BY n.id DESC 
            LIMIT {limit} OFFSET {offset}
            """
            columns = ["id", "event_id", "unique_event_name", "event_name", "notification_type", "sent_at"]
            
            # Get total count
            count_query = "SELECT COUNT(*) FROM event_notifications"
            
        elif table_name == "event_winners":
            # Join with events table to get event name
            query = f"""
            SELECT w.id, w.event_id, e.unique_event_name, e.name as event_name,
                   w.player_name, w.final_score, w.was_online, w.rewarded_at
            FROM event_winners w
            JOIN events e ON w.event_id = e.id
            ORDER BY w.id DESC 
            LIMIT {limit} OFFSET {offset}
            """
            columns = ["id", "event_id", "unique_event_name", "event_name", "player_name", "final_score", "was_online", "rewarded_at"]
            
            # Get total count
            count_query = "SELECT COUNT(*) FROM event_winners"
        
        # Get total count
        count_result = db.db_query(count_query)
        total = count_result[0][0] if count_result else 0
        
        # Get enhanced data
        results = db.db_query(query)
        
        # Format results
        rows = []
        for row in results:
            row_dict = {}
            for i, col_name in enumerate(columns):
                row_dict[col_name] = row[i]
            rows.append(row_dict)
        
        return jsonify({
            "table": table_name,
            "columns": columns,
            "rows": rows,
            "total": total,
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/database/admin-unlock", methods=["POST"])
@login_required
def api_admin_unlock():
    """Verify DATABASE_MASTER password"""
    try:
        password = request.json.get("password")
        master_password = os.getenv("DATABASE_MASTER")
        
        if not master_password:
            return jsonify({"success": False, "error": "DATABASE_MASTER not configured"})
        
        if password == master_password:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Invalid password"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/database/admin-clear-logs", methods=["POST"])
@login_required
def api_admin_clear_logs():
    """Clear all logs from the database"""
    try:
        db = get_db()
        
        # Get count before deletion
        count_query = "SELECT COUNT(*) FROM logs"
        count_result = db.db_query(count_query)
        deleted_count = count_result[0][0] if count_result else 0
        
        # Delete all logs
        delete_query = "DELETE FROM logs"
        db.db_query_with_params(delete_query, ())
        
        # Log the action
        sql_calendar.log_message(f"Admin cleared {deleted_count} log entries via web interface", "ADMIN")
        
        return jsonify({
            "success": True,
            "deleted_count": deleted_count
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/database/admin-events-list")
@login_required
def api_admin_events_list():
    """Get list of all events for admin deletion"""
    try:
        db = get_db()
        
        query = """
        SELECT id, unique_event_name, name, start_time, end_time, event_over
        FROM events 
        ORDER BY start_time DESC
        """
        
        results = db.db_query(query)
        
        events = []
        for row in results:
            events.append({
                "id": row[0],
                "unique_event_name": row[1],
                "name": row[2],
                "start_time": row[3],
                "end_time": row[4],
                "event_over": bool(row[5])
            })
        
        return jsonify({"events": events})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/database/admin-json-files")
@login_required
def api_admin_json_files():
    """Get list of all event JSON files for admin management"""
    try:
        if not os.path.exists(EVENTS_JSON_PATH):
            return jsonify({"files": []})
        
        files = []
        for filename in os.listdir(EVENTS_JSON_PATH):
            if filename.endswith('.json'):
                filepath = os.path.join(EVENTS_JSON_PATH, filename)
                stat = os.stat(filepath)
                
                # Try to read the JSON to get event details
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    event_name = data.get('name', 'Unknown')
                    description = data.get('description', 'No description')
                except:
                    event_name = filename.replace('.json', '')
                    description = 'Could not read file'
                
                files.append({
                    "filename": filename,
                    "event_name": event_name,
                    "description": description,
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by filename
        files.sort(key=lambda x: x['filename'])
        
        return jsonify({"files": files})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/database/admin-delete-json", methods=["POST"])
@login_required
def api_admin_delete_json():
    """Delete an event JSON file"""
    try:
        filename = request.json.get("filename")
        if not filename:
            return jsonify({"success": False, "error": "No filename provided"})
        
        # Validate filename (security check)
        if not filename.endswith('.json') or '/' in filename or '\\' in filename:
            return jsonify({"success": False, "error": "Invalid filename"})
        
        filepath = os.path.join(EVENTS_JSON_PATH, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "File not found"})
        
        # Delete the file
        os.remove(filepath)
        
        # Log the deletion
        sql_calendar.log_message(f"Admin deleted event JSON file: {filename}", "ADMIN")
        
        return jsonify({
            "success": True,
            "message": f"Event JSON file '{filename}' deleted successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/database/admin-delete-event", methods=["POST"])
@login_required
def api_admin_delete_event():
    """Delete an event and all related data"""
    try:
        event_id = request.json.get("event_id")
        if not event_id:
            return jsonify({"success": False, "error": "No event ID provided"})
        
        db = get_db()
        
        # Get event details for logging
        event_query = "SELECT unique_event_name, name FROM events WHERE id = ?"
        event_result = db.db_query_with_params(event_query, (event_id,))
        
        if not event_result:
            return jsonify({"success": False, "error": "Event not found"})
        
        unique_name, event_name = event_result[0]
        
        # Delete in proper order (foreign key constraints)
        # 1. Delete event_winners
        db.db_query_with_params("DELETE FROM event_winners WHERE event_id = ?", (event_id,))
        
        # 2. Delete event_notifications  
        db.db_query_with_params("DELETE FROM event_notifications WHERE event_id = ?", (event_id,))
        
        # 3. Delete the event itself
        db.db_query_with_params("DELETE FROM events WHERE id = ?", (event_id,))
        
        # Log the deletion
        sql_calendar.log_message(f"Admin deleted event '{event_name}' ({unique_name}) and all related data via web interface", "ADMIN")
        
        return jsonify({
            "success": True,
            "message": f"Event '{event_name}' and all related data deleted successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/database/query", methods=["POST"])
@login_required
def api_database_query():
    """Execute a custom SQL query (SELECT only for safety)"""
    try:
        query = request.json.get("query", "").strip()
        
        # Only allow SELECT queries for safety
        if not query.upper().startswith("SELECT"):
            return jsonify({"error": "Only SELECT queries are allowed"}), 400
        
        db = get_db()
        results = db.db_query(query)
        
        return jsonify({
            "results": results,
            "count": len(results) if results else 0
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/create_event", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        # Extract form data
        name = request.form.get("name")
        description = request.form.get("description")
        event_json = request.form.get("event_json")
        timezone_str = request.form.get("timezone")

        # Extract combined hidden fields from JS
        start_str = request.form.get("start")
        end_str = request.form.get("end")

        # Validate timezone
        if not timezone_str or timezone_str not in pytz.all_timezones:
            flash("Invalid timezone selected")
            return redirect(url_for("create_event"))

        tz = pytz.timezone(timezone_str)

        # Parse start and end
        try:
            start_local = datetime.strptime(start_str, "%Y-%m-%d %I:%M %p")
            end_local = datetime.strptime(end_str, "%Y-%m-%d %I:%M %p")
        except ValueError:
            flash("Invalid date/time format. Use YYYY-MM-DD HH:MM AM/PM")
            return redirect(url_for("create_event"))

        # Localize to selected timezone and convert to UTC
        start_dt = tz.localize(start_local).astimezone(pytz.UTC)
        end_dt = tz.localize(end_local).astimezone(pytz.UTC)

        # Format for database (YYYY-MM-DDTHH:MM:SSZ)
        start_utc = start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_utc = end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Build unique event name
        unique_event_name = f"{name.replace(' ','-')}-{start_dt.strftime('%m-%d-%Y-%H%M')}"

        try:
            # Insert into database
            db = get_db()
            insert_query = f"""
            INSERT INTO events (unique_event_name, name, event_json, description, start_time, end_time)
            VALUES ('{unique_event_name}', '{name}', '{event_json}', '{description}', '{start_utc}', '{end_utc}')
            """
            
            db.db_insert(insert_query)
            
            # Log the event creation
            sql_calendar.log_message_with_timestamp(f"Event created via web interface: {name}")
            
            flash(f"Event '{name}' created successfully!")
            return redirect(url_for("index"))
            
        except Exception as e:
            flash(f"Error creating event: {e}")
            return redirect(url_for("create_event"))

    # GET request
    event_files = load_event_files()
    return render_template("create_event.html", event_files=event_files)

@app.route("/create_json_event", methods=["GET", "POST"])
@login_required
def create_json_event():
    if request.method == "POST":
        # Basic fields
        name = request.form.get("name")
        description = request.form.get("description")
        is_aggregate = request.form.get("is_aggregate") == "true"
        score_text = request.form.get("score_text")
        aggregate_objective = request.form.get("aggregate_objective")

        # Sidebar fields
        sidebar = {
            "displayName": request.form.get("sidebar_display"),
            "color": request.form.get("sidebar_color"),
            "bold": request.form.get("sidebar_bold") == "true",
            "duration": int(request.form.get("sidebar_duration") or 15),
        }

        # Reward fields
        reward_cmd = request.form.get("reward_cmd")
        reward_name = request.form.get("reward_name")

        # Collect setup commands
        setup_commands = []
        aggregate_list = []

        if is_aggregate:
            # Extra setup commands for aggregate
            obj_names = request.form.getlist("setup_obj_name[]")
            actions = request.form.getlist("setup_action[]")
            items = request.form.getlist("setup_item[]")

            for obj_name, action, item in zip(obj_names, actions, items):
                if action == "custom":
                    cmd = f"scoreboard objectives add {obj_name} {item}"
                else:
                    cmd = f"scoreboard objectives add {obj_name} minecraft.{action}:minecraft.{item}"
                setup_commands.append(cmd)
                aggregate_list.append(obj_name)

            # Add dummy aggregate objective at the end
            setup_commands.append(f"scoreboard objectives add {aggregate_objective} dummy \"{aggregate_objective}\"")
        else:
            # Non-aggregate has exactly one setup objective
            obj_names = request.form.getlist("setup_obj_name[]")
            actions = request.form.getlist("setup_action[]")
            items = request.form.getlist("setup_item[]")

            if obj_names and actions and items:
                obj_name = obj_names[0]
                action = actions[0]
                item = items[0]
                if action == "custom":
                    cmd = f"scoreboard objectives add {obj_name} {item}"
                else:
                    cmd = f"scoreboard objectives add {obj_name} minecraft.{action}:minecraft.{item}"
                setup_commands.append(cmd)

        # Cleanup commands = objectives to remove
        cleanup_commands = []
        if is_aggregate:
            cleanup_commands.extend(aggregate_list)
            cleanup_commands.append(aggregate_objective)
        else:
            cleanup_commands.append(aggregate_objective)

        # Build final event JSON
        event_json = {
            "unique_event_name": f"{name.replace(' ', '_')}",  # Add this field
            "name": name,
            "description": description,
            "is_aggregate": is_aggregate,
            "score_text": score_text,
            "aggregate_objective": aggregate_objective,
            "commands": {
                "setup": setup_commands,
                "aggregate": aggregate_list if is_aggregate else [],
                "cleanup": cleanup_commands,
            },
            "sidebar": sidebar,
            "reward_cmd": reward_cmd,
            "reward_name": reward_name,
        }

        # Ensure path exists
        os.makedirs(EVENTS_JSON_PATH, exist_ok=True)

        # Save as CamelCase file
        filename = "".join(word.capitalize() for word in name.split()) + ".json"
        filepath = os.path.join(EVENTS_JSON_PATH, filename)

        with open(filepath, "w") as f:
            json.dump(event_json, f, indent=2)

        flash(f"Event JSON '{name}' saved to {filepath}")
        return redirect(url_for("index"))

    # GET method
    return render_template("create_json_event.html")

@app.route("/api/event_handler/start", methods=["POST"])
@login_required
def api_start_event_handler():
    success = start_event_handler()
    return jsonify({"success": success, "status": "Running" if is_event_handler_running() else "Not Running"})

@app.route("/api/event_handler_status")
@login_required
def api_event_handler_status():
    running = is_event_handler_running()
    return jsonify({"status": "Running" if running else "Not Running"})

@app.route("/api/event_handler/stop", methods=["POST"])
@login_required
def api_stop_event_handler():
    success = stop_event_handler()
    return jsonify({"success": success, "status": "Running" if is_event_handler_running() else "Not Running"})

@app.route("/api/event_files")
@login_required
def api_event_files():
    files = load_event_files()
    return jsonify(files)

@app.route("/api/logs")
@login_required
def api_logs():
    """Return database logs instead of file logs"""
    logs = load_logs_from_db()
    return jsonify(logs)

@app.route("/api/event_json_content/<filename>")
@login_required
def api_event_json_content(filename):
    path = os.path.join(EVENTS_JSON_PATH, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            # Return pretty-printed JSON
            data = json.load(f)
            return json.dumps(data, indent=2)
    return "", 404

# Keep this for backward compatibility, but note it's now deprecated
@app.route("/api/log_content/<filename>")
@login_required
def api_log_content(filename):
    """Legacy endpoint - now redirects to database logs"""
    if filename == "handler_logs.txt":
        logs = load_logs_from_db()
        log_text = "\n".join([f"{log['timestamp']}: [{log['log_level']}] {log['message']}" for log in logs])
        return log_text
    
    # For other files, still check filesystem
    path = os.path.join(LOGS_PATH, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return "", 404

if __name__ == "__main__":
    # Initialize database only if it doesn't exist
    try:
        db = get_db()
        
        # Check if database file exists and has tables
        if not os.path.exists(DATABASE_PATH):
            print("Database file doesn't exist, creating new database...")
            db.initialize_db()
            print("Database initialized successfully")
        else:
            # Check if tables exist
            info = db.db_info()
            if not info or not info.get('tables'):
                print("Database exists but has no tables, initializing...")
                db.initialize_db()
                print("Database initialized successfully")
            else:
                print(f"Database already exists with {len(info['tables'])} tables")
                
    except Exception as e:
        print(f"Error with database: {e}")
    
    app.run(host="0.0.0.0", port=8080, debug=True)