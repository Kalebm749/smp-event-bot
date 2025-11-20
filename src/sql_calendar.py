#!/usr/bin/python3.12
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from database_manager import db_manager

# --- Config ---
load_dotenv()
DATABASE_FILE = os.getenv("DATABASE_FILE")
DATABASE_DIR = os.getenv("DATABASE_DIR")
DATABASE_SCHEMA= os.getenv("DATABASE_SCHEMA")

# Database Paths
SCHEMA_PATH = f"{DATABASE_DIR}{DATABASE_SCHEMA}"
DATABASE_PATH = f"{DATABASE_DIR}{DATABASE_FILE}"

# === QUERY FUNCTIONS ===

def find_missing_24h_notif():
    """Find events needing 24h notifications"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    missing_24_query = """
    SELECT e.*
    FROM events e
    LEFT JOIN event_notifications n
        ON e.id = n.event_id
        AND n.notification_type = '24h'
    WHERE e.start_time > strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '+30 minutes')
    AND e.start_time <= strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '+1 day')
    AND n.id IS NULL
    AND e.event_over = 0;
    """
    
    return db.db_query(missing_24_query)

def find_missing_30m_notif():
    """Find events needing 30min notifications"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    missing_30_query = """
    SELECT e.*
    FROM events e
    LEFT JOIN event_notifications n
        ON e.id = n.event_id
        AND n.notification_type = '30min'
    WHERE e.start_time > strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    AND e.start_time <= strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '+30 minutes')
    AND e.event_over = 0
    AND n.id IS NULL;
    """

    return db.db_query(missing_30_query)

def find_missing_now_notif():
    """Find events needing start notifications"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    missing_start_now_notif_query = """
    SELECT e.*
    FROM events e
    LEFT JOIN event_notifications n
        ON e.id = n.event_id
        AND n.notification_type = 'start'
    WHERE e.start_time <= strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    AND e.event_started = 1
    AND e.event_over = 0
    AND n.id IS NULL;
    """

    return db.db_query(missing_start_now_notif_query)

def events_needing_started():
    """Find events that need to be started"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    events_needing_started_query = """
    SELECT *
    FROM events
    WHERE start_time <= strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    AND event_started = 0
    AND event_over = 0;
    """

    return db.db_query(events_needing_started_query)

def events_needing_ending():
    """Find events that need to be ended"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    events_needing_ending_query = """
    SELECT *
    FROM events
    WHERE event_in_progress = 1
    AND end_time < strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    AND event_over = 0;
    """

    return db.db_query(events_needing_ending_query)

def events_needing_scoreboard_display():
    """Find events in progress that need scoreboard display"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    events_need_display_query = """
    SELECT *
    FROM events
    WHERE event_in_progress = 1
    AND (last_scoreboard_time IS NULL 
         OR last_scoreboard_time <= strftime('%Y-%m-%dT%H:%M:%SZ', datetime('now', '-15 minutes')));
    """

    return db.db_query(events_need_display_query)

# === UPDATE FUNCTIONS ===

def start_event_by_id(event_id):
    """Mark event as started"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    start_event_query = """
    UPDATE events
    SET event_in_progress = 1,
        event_started = 1
    WHERE id = ?;
    """

    return db.db_query_with_params(start_event_query, (event_id,))

def end_event_by_id(event_id):
    """Mark event as ended"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    end_event_query = """
    UPDATE events
    SET event_in_progress = 0,
        event_over = 1
    WHERE id = ?;
    """

    return db.db_query_with_params(end_event_query, (event_id,))

def update_scoreboard_display_time(event_id):
    """Update the last scoreboard display time"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)
    
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    update_query = """
    UPDATE events
    SET last_scoreboard_time = ?
    WHERE id = ?;
    """
    
    return db.db_query_with_params(update_query, (current_time, event_id))

# === NOTIFICATION FUNCTIONS ===

def send_24h_notification(event_id):
    """Mark 24h notification as sent"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    query = """
    INSERT INTO event_notifications (event_id, notification_type)
    VALUES (?, '24h');
    """

    return db.db_query_with_params(query, (event_id,))

def send_30min_notification(event_id):
    """Mark 30min notification as sent"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    query = """
    INSERT INTO event_notifications (event_id, notification_type)
    VALUES (?, '30min');
    """

    return db.db_query_with_params(query, (event_id,))

def send_start_notification(event_id):
    """Mark start notification as sent"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    query = """
    INSERT INTO event_notifications (event_id, notification_type)
    VALUES (?, 'start');
    """

    return db.db_query_with_params(query, (event_id,))

def send_end_notification(event_id):
    """Mark end notification as sent"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)

    query = """
    INSERT INTO event_notifications (event_id, notification_type)
    VALUES (?, 'end');
    """

    return db.db_query_with_params(query, (event_id,))

# === HELPER FUNCTIONS ===

def get_event_by_id(event_id):
    """Get a single event by ID"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)
    
    query = """
    SELECT * FROM events WHERE id = ?;
    """
    
    result = db.db_query_with_params(query, (event_id,))
    return result[0] if result else None

def insert_event(unique_name, name, event_json, description, start_time, end_time):
    """Insert a new event"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)
    
    query = """
    INSERT INTO events (unique_event_name, name, event_json, description, start_time, end_time)
    VALUES (?, ?, ?, ?, ?, ?);
    """
    
    return db.db_query_with_params(query, (unique_name, name, event_json, description, start_time, end_time))

def log_message(message, level="INFO"):
    """Add a simple log entry with current timestamp"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)
    
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    query = """
    INSERT INTO logs (timestamp, message, log_level)
    VALUES (?, ?, ?);
    """
    
    return db.db_query_with_params(query, (timestamp, message, level))

def log_message_with_timestamp(message, level="INFO", timestamp=None):
    """Add a log entry with custom timestamp in UTC format"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)
    
    if not timestamp:
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    query = """
    INSERT INTO logs (timestamp, message, log_level)
    VALUES (?, ?, ?);
    """
    
    return db.db_query_with_params(query, (timestamp, message, level))

def update_scoreboard_time(event_id, timestamp):
    """Update the last scoreboard display time for an event"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)
    
    query = """
    UPDATE events
    SET last_scoreboard_time = ?
    WHERE id = ?;
    """
    
    result = db.db_query_with_params(query, (timestamp, event_id))
    return result

def get_event_id_by_unique_name(unique_name):
    """Get event ID by unique event name"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)
    
    query = """
    SELECT id FROM events WHERE unique_event_name = ?;
    """
    
    result = db.db_query_with_params(query, (unique_name,))
    return result[0][0] if result else None

def insert_winner(event_id, player_name, final_score, was_online):
    """Insert a winner into the event_winners table"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)
    
    # Format timestamp for rewarded_at field
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    query = """
    INSERT INTO event_winners (event_id, player_name, final_score, was_online, rewarded_at)
    VALUES (?, ?, ?, ?, ?);
    """
    
    return db.db_query_with_params(query, (event_id, player_name, final_score, 1 if was_online else 0, timestamp))

def get_event_winners(event_id):
    """Get all winners for a specific event"""
    db = db_manager(DATABASE_PATH, SCHEMA_PATH)
    
    query = """
    SELECT * FROM event_winners WHERE event_id = ?;
    """
    
    return db.db_query_with_params(query, (event_id,))