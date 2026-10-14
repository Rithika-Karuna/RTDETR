"""
Database service for the Railway Track Alert System.
Uses SQLite for event history, alert logs, and configuration persistence.
"""
import sqlite3
import json
import os
import threading
from datetime import datetime
from typing import Optional

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "events.db")

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Get a thread-local SQLite connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        os.makedirs(DB_DIR, exist_ok=True)
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


def init_db():
    """Initialize database tables."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'DETECTED',
            risk_level TEXT NOT NULL DEFAULT 'LOW',
            risk_score REAL DEFAULT 0,
            object_type TEXT,
            object_count INTEGER DEFAULT 1,
            confidence REAL,
            zone TEXT,
            track_ids TEXT,
            reason TEXT,
            gps_latitude REAL,
            gps_longitude REAL,
            location_name TEXT,
            nearest_station TEXT,
            railway_zone TEXT,
            division TEXT,
            train_number TEXT,
            train_name TEXT,
            train_source TEXT,
            train_destination TEXT,
            train_speed REAL,
            train_distance_km REAL,
            tti_seconds REAL,
            evidence_path TEXT,
            first_detected_at TEXT NOT NULL,
            alert_sent_at TEXT,
            resolved_at TEXT,
            updated_at TEXT NOT NULL,
            metadata TEXT
        );

        CREATE TABLE IF NOT EXISTS alert_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            recipient TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING',
            sent_at TEXT,
            error_message TEXT,
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        );

        CREATE TABLE IF NOT EXISTS risk_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            risk_score REAL,
            risk_level TEXT,
            timestamp TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        );

        CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
        CREATE INDEX IF NOT EXISTS idx_events_risk ON events(risk_level);
        CREATE INDEX IF NOT EXISTS idx_events_detected ON events(first_detected_at);
        CREATE INDEX IF NOT EXISTS idx_alert_log_event ON alert_log(event_id);
    """)
    conn.commit()


def insert_event(event: dict) -> str:
    """Insert a new event record. Returns the event_id."""
    conn = _get_conn()
    now = datetime.utcnow().isoformat()
    event_id = event.get("event_id", f"EVT-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    
    conn.execute("""
        INSERT OR REPLACE INTO events (
            event_id, status, risk_level, risk_score, object_type, object_count,
            confidence, zone, track_ids, reason, gps_latitude, gps_longitude,
            location_name, nearest_station, railway_zone, division,
            train_number, train_name, train_source, train_destination,
            train_speed, train_distance_km, tti_seconds, evidence_path,
            first_detected_at, alert_sent_at, resolved_at, updated_at, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        event.get("status", "DETECTED"),
        event.get("risk_level", "LOW"),
        event.get("risk_score", 0),
        event.get("object_type"),
        event.get("object_count", 1),
        event.get("confidence"),
        event.get("zone"),
        json.dumps(event.get("track_ids", [])),
        event.get("reason"),
        event.get("gps_latitude"),
        event.get("gps_longitude"),
        event.get("location_name"),
        event.get("nearest_station"),
        event.get("railway_zone"),
        event.get("division"),
        event.get("train_number"),
        event.get("train_name"),
        event.get("train_source"),
        event.get("train_destination"),
        event.get("train_speed"),
        event.get("train_distance_km"),
        event.get("tti_seconds"),
        event.get("evidence_path"),
        event.get("first_detected_at", now),
        event.get("alert_sent_at"),
        event.get("resolved_at"),
        now,
        json.dumps(event.get("metadata", {}))
    ))
    conn.commit()
    return event_id


def update_event(event_id: str, updates: dict):
    """Update an existing event."""
    conn = _get_conn()
    now = datetime.utcnow().isoformat()
    updates["updated_at"] = now
    
    set_clauses = []
    values = []
    for key, val in updates.items():
        if key == "event_id":
            continue
        if isinstance(val, (dict, list)):
            val = json.dumps(val)
        set_clauses.append(f"{key} = ?")
        values.append(val)
    
    values.append(event_id)
    conn.execute(f"UPDATE events SET {', '.join(set_clauses)} WHERE event_id = ?", values)
    conn.commit()


def get_event(event_id: str) -> Optional[dict]:
    """Get a single event by ID."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
    if row:
        return dict(row)
    return None


def get_active_events() -> list:
    """Get all non-resolved events."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM events WHERE status NOT IN ('RESOLVED') ORDER BY updated_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_events(limit: int = 100, offset: int = 0, filters: Optional[dict] = None) -> list:
    """Get events with optional filtering."""
    conn = _get_conn()
    where_clauses = []
    values = []
    
    if filters:
        if filters.get("risk_level"):
            where_clauses.append("risk_level = ?")
            values.append(filters["risk_level"])
        if filters.get("status"):
            where_clauses.append("status = ?")
            values.append(filters["status"])
        if filters.get("object_type"):
            where_clauses.append("object_type LIKE ?")
            values.append(f"%{filters['object_type']}%")
        if filters.get("date_from"):
            where_clauses.append("first_detected_at >= ?")
            values.append(filters["date_from"])
        if filters.get("date_to"):
            where_clauses.append("first_detected_at <= ?")
            values.append(filters["date_to"])
    
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    values.extend([limit, offset])
    
    rows = conn.execute(
        f"SELECT * FROM events {where_sql} ORDER BY first_detected_at DESC LIMIT ? OFFSET ?",
        values
    ).fetchall()
    return [dict(r) for r in rows]


def get_event_count(filters: Optional[dict] = None) -> int:
    """Get total event count with optional filters."""
    conn = _get_conn()
    where_clauses = []
    values = []
    if filters:
        if filters.get("risk_level"):
            where_clauses.append("risk_level = ?")
            values.append(filters["risk_level"])
        if filters.get("status"):
            where_clauses.append("status = ?")
            values.append(filters["status"])
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    row = conn.execute(f"SELECT COUNT(*) as cnt FROM events {where_sql}", values).fetchone()
    return row["cnt"] if row else 0


def insert_alert_log(event_id: str, channel: str, recipient: str, status: str = "PENDING"):
    """Log a notification attempt."""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO alert_log (event_id, channel, recipient, status, sent_at) VALUES (?, ?, ?, ?, ?)",
        (event_id, channel, recipient, status, datetime.utcnow().isoformat())
    )
    conn.commit()


def update_alert_log(log_id: int, status: str, error_message: str = None):
    """Update a notification log entry."""
    conn = _get_conn()
    conn.execute(
        "UPDATE alert_log SET status = ?, error_message = ? WHERE id = ?",
        (status, error_message, log_id)
    )
    conn.commit()


def get_alert_logs(event_id: str) -> list:
    """Get all notification logs for an event."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM alert_log WHERE event_id = ? ORDER BY sent_at DESC", (event_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def insert_risk_history(event_id: str, risk_score: float, risk_level: str, details: dict = None):
    """Record a risk score change."""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO risk_history (event_id, risk_score, risk_level, timestamp, details) VALUES (?, ?, ?, ?, ?)",
        (event_id, risk_score, risk_level, datetime.utcnow().isoformat(), json.dumps(details or {}))
    )
    conn.commit()


# Initialize on import
init_db()
