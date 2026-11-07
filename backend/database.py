"""
CivicFix Database Layer (SQLite)
================================
Manages schemas, persistent storage, and transaction helpers for:
- Citizen & Admin Users with Email Authentication
- Session Tokens & OTP Verification
- Infrastructure Complaints & AI Classifications
- Status Updates & Audit Trails
"""

import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "backend" / "civicfix.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        salt TEXT,
        role TEXT DEFAULT 'citizen',
        otp_code TEXT,
        otp_expiry TIMESTAMP,
        is_verified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Check and add missing columns to users if old table exists
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [col["name"] for col in cursor.fetchall()]

    new_cols = {
        "password_hash": "TEXT",
        "salt": "TEXT",
        "otp_code": "TEXT",
        "otp_expiry": "TIMESTAMP",
        "is_verified": "INTEGER DEFAULT 0",
        "phone": "TEXT",
        "phone_otp_code": "TEXT",
        "phone_otp_expiry": "TIMESTAMP"
    }

    for col_name, col_type in new_cols.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")

    # Active Auth Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Complaints Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        user_email TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        confidence REAL NOT NULL,
        priority TEXT NOT NULL,
        recommendation TEXT,
        image_filename TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        address TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    );
    """)

    # Audit Trail Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        performed_by TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id)
    );
    """)

    conn.commit()
    conn.close()
    print(f"[Database] SQLite schema verified at {DB_PATH}")


if __name__ == "__main__":
    init_db()
