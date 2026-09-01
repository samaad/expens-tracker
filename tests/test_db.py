"""Tests for the Spendly SQLite data layer."""

import re
import sqlite3
from datetime import datetime

import pytest
from werkzeug.security import check_password_hash

from database import db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point the data layer at a throwaway database for every test."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    yield


def column_types(conn, table):
    return {row["name"]: row["type"] for row in conn.execute(f"PRAGMA table_info({table})")}


def test_init_db_is_idempotent():
    db.init_db()
    db.init_db()

    conn = db.get_db()
    try:
        tables = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    finally:
        conn.close()

    assert {"users", "expenses"} <= tables


def test_users_schema():
    db.init_db()

    conn = db.get_db()
    try:
        types = column_types(conn, "users")
        not_null = {row["name"] for row in conn.execute("PRAGMA table_info(users)") if row["notnull"]}
    finally:
        conn.close()

    assert types == {
        "id": "INTEGER",
        "name": "TEXT",
        "email": "TEXT",
        "password_hash": "TEXT",
        "created_at": "TEXT",
    }
    assert {"name", "email", "password_hash", "created_at"} <= not_null


def test_expenses_schema():
    db.init_db()

    conn = db.get_db()
    try:
        types = column_types(conn, "expenses")
        nullable = {
            row["name"] for row in conn.execute("PRAGMA table_info(expenses)") if not row["notnull"]
        }
        foreign_keys = list(conn.execute("PRAGMA foreign_key_list(expenses)"))
    finally:
        conn.close()

    assert types["amount"] == "REAL"
    assert types["user_id"] == "INTEGER"
    assert types["date"] == "TEXT"
    assert "description" in nullable
    assert len(foreign_keys) == 1
    assert foreign_keys[0]["table"] == "users"
    assert foreign_keys[0]["to"] == "id"


def test_get_db_returns_dict_like_rows_with_foreign_keys_on():
    db.init_db()
    db.seed_db()

    conn = db.get_db()
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        row = conn.execute("SELECT name, email FROM users").fetchone()
        assert row["name"] == "Demo User"
        assert row["email"] == "demo@spendly.com"
    finally:
        conn.close()


def test_seed_db_inserts_demo_user_and_eight_expenses():
    db.init_db()
    db.seed_db()

    conn = db.get_db()
    try:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 8

        categories = {row["category"] for row in conn.execute("SELECT category FROM expenses")}
        user_ids = {row["user_id"] for row in conn.execute("SELECT user_id FROM expenses")}
        demo_id = conn.execute("SELECT id FROM users").fetchone()["id"]
    finally:
        conn.close()

    assert categories == set(db.CATEGORIES)
    assert user_ids == {demo_id}


def test_seed_db_does_not_duplicate_on_repeat_runs():
    db.init_db()
    db.seed_db()
    db.seed_db()

    conn = db.get_db()
    try:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 8
    finally:
        conn.close()


def test_demo_password_is_hashed():
    db.init_db()
    db.seed_db()

    conn = db.get_db()
    try:
        password_hash = conn.execute("SELECT password_hash FROM users").fetchone()["password_hash"]
    finally:
        conn.close()

    assert password_hash != "demo123"
    assert check_password_hash(password_hash, "demo123")


def test_duplicate_email_violates_unique_constraint():
    db.init_db()
    db.seed_db()

    conn = db.get_db()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Impostor", "demo@spendly.com", "x"),
            )
    finally:
        conn.close()


def test_expense_with_unknown_user_violates_foreign_key():
    db.init_db()
    db.seed_db()

    conn = db.get_db()
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                (9999, 10.0, "Food", "2026-01-01"),
            )
    finally:
        conn.close()


def test_created_at_is_populated_by_default():
    db.init_db()
    db.seed_db()

    conn = db.get_db()
    try:
        user_created = conn.execute("SELECT created_at FROM users").fetchone()["created_at"]
        expense_created = [row["created_at"] for row in conn.execute("SELECT created_at FROM expenses")]
    finally:
        conn.close()

    stamp = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    assert re.fullmatch(stamp, user_created)
    assert len(expense_created) == 8
    assert all(value and re.fullmatch(stamp, value) for value in expense_created)


def test_seeded_expenses_have_descriptions():
    db.init_db()
    db.seed_db()

    conn = db.get_db()
    try:
        descriptions = [row["description"] for row in conn.execute("SELECT description FROM expenses")]
    finally:
        conn.close()

    assert len(descriptions) == 8
    assert all(value and value.strip() for value in descriptions)
    assert len(set(descriptions)) == 8


def test_seeded_amounts_are_floats():
    db.init_db()
    db.seed_db()

    conn = db.get_db()
    try:
        amounts = [row["amount"] for row in conn.execute("SELECT amount FROM expenses")]
    finally:
        conn.close()

    assert all(isinstance(value, float) for value in amounts)
    assert all(value > 0 for value in amounts)


def test_seeded_dates_fall_in_the_current_month():
    db.init_db()
    db.seed_db()

    conn = db.get_db()
    try:
        dates = [row["date"] for row in conn.execute("SELECT date FROM expenses")]
    finally:
        conn.close()

    current_month = datetime.now().strftime("%Y-%m")
    for date in dates:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)
        assert date.startswith(current_month)
