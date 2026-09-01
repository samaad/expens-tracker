"""SQLite data layer for Spendly."""

import sqlite3
from datetime import datetime
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent.parent / "expense_tracker.db"

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    amount      REAL NOT NULL,
    category    TEXT NOT NULL,
    date        TEXT NOT NULL,
    description TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

# (amount, category, day_of_month, description) — amounts in AED.
# Day numbers stay within 1–28 so every date is valid in any month.
SAMPLE_EXPENSES = [
    (42.50, "Food", 3, "Lunch at the office cafe"),
    (120.00, "Transport", 5, "Metro card top-up"),
    (385.75, "Bills", 8, "DEWA electricity bill"),
    (210.00, "Health", 11, "Pharmacy — cold medicine"),
    (95.00, "Entertainment", 14, "Cinema tickets"),
    (649.99, "Shopping", 18, "Running shoes"),
    (150.00, "Other", 22, "Gift for a colleague"),
    (78.25, "Food", 26, "Weekend groceries"),
]


def get_db():
    """Return a SQLite connection with dict-like rows and FK enforcement on."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the tables if they do not exist. Safe to call repeatedly."""
    conn = get_db()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def seed_db():
    """Insert the demo user and sample expenses once. No-op if users exist."""
    conn = get_db()
    try:
        if conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"] > 0:
            return

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cursor.lastrowid

        today = datetime.now()
        rows = [
            (user_id, amount, category, today.strftime(f"%Y-%m-{day:02d}"), description)
            for amount, category, day, description in SAMPLE_EXPENSES
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()
