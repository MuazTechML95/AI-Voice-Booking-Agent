"""
modules/database.py
---------------------
Persistence layer for appointments.

Backend selection:
    - If DATABASE_URL is set in .env  -> PostgreSQL
    - Otherwise                       -> local SQLite file (as before)

Table schema:
    appointments
        id                  PRIMARY KEY (auto-increment)
        business_type       TEXT
        full_name           TEXT
        phone               TEXT
        appointment_date    TEXT
        appointment_time    TEXT
        purpose             TEXT
        category            TEXT
        status              TEXT  ('CONFIRMED' / 'CANCELLED')
        created_at          TEXT

The table is created automatically the first time this module is
imported, so the app works on a fresh checkout with zero manual setup.
"""

import os
import sqlite3
from contextlib import contextmanager

from dotenv import load_dotenv

from modules.utils import DB_PATH, ensure_dirs, now_iso, get_logger

# Load .env here too: this module runs init_db() at import time, which can
# happen before the app calls load_dotenv().
load_dotenv()

logger = get_logger(__name__)

_schema_ready = False


def _is_postgres() -> bool:
    return bool(os.environ.get("DATABASE_URL", "").strip())


def _connect():
    """Open a raw connection to the active backend (never logs credentials)."""
    if _is_postgres():
        import psycopg2
        from psycopg2.extras import RealDictCursor

        return psycopg2.connect(
            os.environ["DATABASE_URL"].strip(),
            cursor_factory=RealDictCursor,
            connect_timeout=10,
        )
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _execute(conn, sql: str, params: tuple = ()):
    """Run a statement on either backend. SQL is written with '?' placeholders."""
    if _is_postgres():
        cursor = conn.cursor()
        cursor.execute(sql.replace("?", "%s"), params)
        return cursor
    return conn.execute(sql, params)


@contextmanager
def get_connection():
    """Context-managed connection so callers never forget to commit/close."""
    if not _schema_ready:
        init_db()
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create the appointments table if it doesn't already exist."""
    global _schema_ready
    id_column = (
        "id SERIAL PRIMARY KEY" if _is_postgres()
        else "id INTEGER PRIMARY KEY AUTOINCREMENT"
    )
    conn = _connect()
    try:
        _execute(
            conn,
            f"""
            CREATE TABLE IF NOT EXISTS appointments (
                {id_column},
                business_type     TEXT NOT NULL,
                full_name         TEXT NOT NULL,
                phone             TEXT NOT NULL,
                appointment_date  TEXT NOT NULL,
                appointment_time  TEXT NOT NULL,
                purpose           TEXT,
                category          TEXT,
                status            TEXT NOT NULL DEFAULT 'CONFIRMED',
                created_at        TEXT NOT NULL
            )
            """,
        )
        conn.commit()
    finally:
        conn.close()
    _schema_ready = True
    logger.info("Database ready (%s)", "PostgreSQL" if _is_postgres() else DB_PATH)


def insert_appointment(data: dict) -> int:
    """
    Insert a new appointment row and return its generated id.

    `data` is expected to contain: business_type, full_name, phone,
    appointment_date, appointment_time, purpose, category(optional).
    """
    with get_connection() as conn:
        cursor = _execute(
            conn,
            """
            INSERT INTO appointments
                (business_type, full_name, phone, appointment_date,
                 appointment_time, purpose, category, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """ + (" RETURNING id" if _is_postgres() else ""),
            (
                data.get("business_type"),
                data.get("full_name"),
                data.get("phone"),
                data.get("appointment_date"),
                data.get("appointment_time"),
                data.get("purpose"),
                data.get("category"),
                "CONFIRMED",
                now_iso(),
            ),
        )
        if _is_postgres():
            return cursor.fetchone()["id"]
        return cursor.lastrowid


def update_appointment(appointment_id: int, appointment_date: str, appointment_time: str) -> bool:
    """Reschedule an existing appointment to a new date/time. Returns True if a row was updated."""
    with get_connection() as conn:
        cursor = _execute(
            conn,
            """
            UPDATE appointments
            SET appointment_date = ?, appointment_time = ?
            WHERE id = ? AND status = 'CONFIRMED'
            """,
            (appointment_date, appointment_time, appointment_id),
        )
        return cursor.rowcount > 0


def cancel_appointment(appointment_id: int) -> bool:
    """Mark an appointment as CANCELLED rather than deleting it, to preserve history."""
    with get_connection() as conn:
        cursor = _execute(
            conn,
            "UPDATE appointments SET status = 'CANCELLED' WHERE id = ?",
            (appointment_id,),
        )
        return cursor.rowcount > 0


def get_appointment(appointment_id: int):
    """Fetch a single appointment by id, or None if it doesn't exist."""
    with get_connection() as conn:
        row = _execute(
            conn, "SELECT * FROM appointments WHERE id = ?", (appointment_id,)
        ).fetchone()
        return dict(row) if row else None


def list_appointments(business_type: str = None) -> list:
    """Return all appointments, most recent first, optionally filtered by business type."""
    with get_connection() as conn:
        if business_type:
            rows = _execute(
                conn,
                "SELECT * FROM appointments WHERE business_type = ? ORDER BY created_at DESC",
                (business_type,),
            ).fetchall()
        else:
            rows = _execute(
                conn, "SELECT * FROM appointments ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]


def get_metrics(business_type: str = None) -> dict:
    """Aggregate counts used by the dashboard metrics section of the UI."""
    rows = list_appointments(business_type)
    total = len(rows)
    confirmed = sum(1 for r in rows if r["status"] == "CONFIRMED")
    cancelled = sum(1 for r in rows if r["status"] == "CANCELLED")
    return {"total": total, "confirmed": confirmed, "cancelled": cancelled}


# Initialise the database as soon as this module is imported, so the
# app "just works" on a fresh clone without a separate setup step.
try:
    init_db()
except Exception as exc:  # noqa: BLE001 - app must still load; errors surface per-action
    logger.error("Database initialisation failed: %s", type(exc).__name__)