-- Initial database schema - only creates tables if they don't exist
-- Does NOT drop existing tables
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_event_name TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    event_json TEXT,
    description TEXT,
    start_time TEXT NOT NULL,  -- UTC ISO8601 format
    end_time TEXT NOT NULL,    -- UTC ISO8601 format
    event_in_progress INTEGER DEFAULT 0,
    event_started INTEGER DEFAULT 0,
    event_over INTEGER DEFAULT 0,
    last_scoreboard_time TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TRIGGER IF NOT EXISTS enforce_events_times_insert
BEFORE INSERT ON events
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.start_time IS NOT NULL
             AND NEW.start_time NOT LIKE '____-__-__T__:__:__Z'
        THEN RAISE (ABORT, 'start_time must be UTC in YYYY-MM-DDTHH:MM:SSZ format')
    END;
    SELECT CASE
        WHEN NEW.end_time IS NOT NULL
             AND NEW.end_time NOT LIKE '____-__-__T__:__:__Z'
        THEN RAISE (ABORT, 'end_time must be UTC in YYYY-MM-DDTHH:MM:SSZ format')
    END;
END;

CREATE TRIGGER IF NOT EXISTS enforce_events_times_update
BEFORE UPDATE ON events
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.start_time IS NOT NULL
             AND NEW.start_time NOT LIKE '____-__-__T__:__:__Z'
        THEN RAISE (ABORT, 'start_time must be UTC in YYYY-MM-DDTHH:MM:SSZ format')
    END;
    SELECT CASE
        WHEN NEW.end_time IS NOT NULL
             AND NEW.end_time NOT LIKE '____-__-__T__:__:__Z'
        THEN RAISE (ABORT, 'end_time must be UTC in YYYY-MM-DDTHH:MM:SSZ format')
    END;
END;

CREATE TABLE IF NOT EXISTS event_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL,
    sent_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE(event_id, notification_type)
);

CREATE TRIGGER IF NOT EXISTS enforce_notifications_insert
BEFORE INSERT ON event_notifications
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.sent_at IS NOT NULL
             AND NEW.sent_at NOT LIKE '____-__-__T__:__:__Z'
        THEN RAISE (ABORT, 'sent_at must be UTC in YYYY-MM-DDTHH:MM:SSZ format')
    END;
END;

CREATE TRIGGER IF NOT EXISTS enforce_notifications_update
BEFORE UPDATE ON event_notifications
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.sent_at IS NOT NULL
             AND NEW.sent_at NOT LIKE '____-__-__T__:__:__Z'
        THEN RAISE (ABORT, 'sent_at must be UTC in YYYY-MM-DDTHH:MM:SSZ format')
    END;
END;

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    message TEXT NOT NULL,
    log_level TEXT DEFAULT 'INFO'
);

CREATE TRIGGER IF NOT EXISTS enforce_logs_insert
BEFORE INSERT ON logs
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.timestamp IS NOT NULL
             AND NEW.timestamp NOT LIKE '____-__-__T__:__:__Z'
        THEN RAISE (ABORT, 'timestamp must be UTC in YYYY-MM-DDTHH:MM:SSZ format')
    END;
END;

CREATE TRIGGER IF NOT EXISTS enforce_logs_update
BEFORE UPDATE ON logs
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.timestamp IS NOT NULL
             AND NEW.timestamp NOT LIKE '____-__-__T__:__:__Z'
        THEN RAISE (ABORT, 'timestamp must be UTC in YYYY-MM-DDTHH:MM:SSZ format')
    END;
END;

CREATE TABLE IF NOT EXISTS event_winners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    final_score INTEGER,
    was_online BOOLEAN DEFAULT TRUE,
    rewarded_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TRIGGER IF NOT EXISTS enforce_winners_insert
BEFORE INSERT ON event_winners
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.rewarded_at IS NOT NULL
             AND NEW.rewarded_at NOT LIKE '____-__-__T__:__:__Z'
        THEN RAISE (ABORT, 'rewarded_at must be UTC in YYYY-MM-DDTHH:MM:SSZ format')
    END;
END;

CREATE TRIGGER IF NOT EXISTS enforce_winners_update
BEFORE UPDATE ON event_winners
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.rewarded_at IS NOT NULL
             AND NEW.rewarded_at NOT LIKE '____-__-__T__:__:__Z'
        THEN RAISE (ABORT, 'rewarded_at must be UTC in YYYY-MM-DDTHH:MM:SSZ format')
    END;
END;