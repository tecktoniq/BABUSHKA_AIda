import sqlite3
import os
from datetime import datetime

os.makedirs("data_db", exist_ok=True)
DB_PATH = "data_db/babushka_aida.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        birthdate TEXT,
        zodiac TEXT,
        soul_card INTEGER,
        trial_left INTEGER DEFAULT 3,
        registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_banned INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        started_at TEXT,
        expires_at TEXT,
        bonus_days INTEGER DEFAULT 0
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        topic TEXT,
        question TEXT,
        card1 TEXT,
        card2 TEXT,
        card3 TEXT,
        verdict TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        bonus_days INTEGER DEFAULT 7,
        rewarded_at TEXT,
        reward_payment_type TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    ensure_column(c, "referrals", "rewarded_at", "TEXT")
    ensure_column(c, "referrals", "reward_payment_type", "TEXT")
    ensure_column(c, "users", "daily_horoscope_enabled", "INTEGER DEFAULT 0")
    ensure_column(c, "users", "last_horoscope_sent", "TEXT")

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")


def ensure_column(cursor, table, column, definition):
    columns = [row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

# --- USERS ---

def get_user(user_id):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return user

def create_user(user_id, username):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user_id, username)
    )
    conn.commit()
    conn.close()

def update_user(user_id, **kwargs):
    conn = get_conn()
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    conn.execute(f"UPDATE users SET {fields} WHERE user_id=?", values)
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_conn()
    users = conn.execute("SELECT * FROM users WHERE is_banned=0").fetchall()
    conn.close()
    return users

def get_paying_users():
    conn = get_conn()
    now = datetime.now().isoformat()
    users = conn.execute("""
        SELECT u.* FROM users u
        JOIN subscriptions s ON u.user_id = s.user_id
        WHERE s.expires_at > ? AND u.is_banned=0
    """, (now,)).fetchall()
    conn.close()
    return users


def set_daily_horoscope_enabled(user_id, enabled):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET daily_horoscope_enabled=? WHERE user_id=?",
        (1 if enabled else 0, user_id)
    )
    conn.commit()
    conn.close()


def get_daily_horoscope_users(today):
    conn = get_conn()
    now = datetime.now().isoformat()
    users = conn.execute("""
        SELECT DISTINCT u.* FROM users u
        JOIN subscriptions s ON u.user_id = s.user_id
        WHERE s.expires_at > ?
          AND u.is_banned=0
          AND u.daily_horoscope_enabled=1
          AND u.name IS NOT NULL
          AND u.birthdate IS NOT NULL
          AND (u.last_horoscope_sent IS NULL OR u.last_horoscope_sent<>?)
    """, (now, today)).fetchall()
    conn.close()
    return users


def mark_daily_horoscope_sent(user_id, today):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET last_horoscope_sent=? WHERE user_id=?",
        (today, user_id)
    )
    conn.commit()
    conn.close()

# --- SUBSCRIPTIONS ---

def is_subscribed(user_id):
    if user_id == int(os.getenv("ADMIN_ID", 0)):
        return True
    conn = get_conn()
    now = datetime.now().isoformat()
    sub = conn.execute(
        "SELECT * FROM subscriptions WHERE user_id=? AND expires_at>?",
        (user_id, now)
    ).fetchone()
    conn.close()
    return sub is not None

def add_subscription(user_id, days, sub_type="paid"):
    conn = get_conn()
    now = datetime.now()
    from datetime import timedelta
    expires = (now + timedelta(days=days)).isoformat()
    cursor = conn.execute(
        "INSERT INTO subscriptions (user_id, type, started_at, expires_at) VALUES (?, ?, ?, ?)",
        (user_id, sub_type, now.isoformat(), expires)
    )
    subscription_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return subscription_id

def add_bonus_days(user_id, days):
    conn = get_conn()
    now = datetime.now().isoformat()
    sub = conn.execute(
        "SELECT * FROM subscriptions WHERE user_id=? AND expires_at>?",
        (user_id, now)
    ).fetchone()
    if sub:
        from datetime import timedelta, datetime as dt
        new_expires = (dt.fromisoformat(sub["expires_at"]) + timedelta(days=days)).isoformat()
        conn.execute(
            "UPDATE subscriptions SET expires_at=? WHERE id=?",
            (new_expires, sub["id"])
        )
    else:
        add_subscription(user_id, days, sub_type="bonus")
    conn.commit()
    conn.close()

# --- TRIALS ---

def use_trial(user_id):
    conn = get_conn()
    user = conn.execute("SELECT trial_left FROM users WHERE user_id=?", (user_id,)).fetchone()
    if user and user["trial_left"] > 0:
        conn.execute("UPDATE users SET trial_left=trial_left-1 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def has_trial(user_id):
    conn = get_conn()
    user = conn.execute("SELECT trial_left FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return user and user["trial_left"] > 0

# --- READINGS ---

def save_reading(user_id, topic, question, card1, card2, card3, verdict):
    conn = get_conn()
    conn.execute(
        "INSERT INTO readings (user_id, topic, question, card1, card2, card3, verdict) VALUES (?,?,?,?,?,?,?)",
        (user_id, topic, question, card1, card2, card3, verdict)
    )
    conn.commit()
    conn.close()

def get_last_readings(user_id, limit=10):
    conn = get_conn()
    readings = conn.execute(
        "SELECT * FROM readings WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return readings

# --- REFERRALS ---

def add_referral(referrer_id, referred_id):
    """Записать реферала без начисления бонуса.

    Бонус начисляется только после первой успешной оплаты приглашённого.
    """
    if referrer_id == referred_id:
        return False
    conn = get_conn()
    exists = conn.execute(
        "SELECT * FROM referrals WHERE referred_id=?", (referred_id,)
    ).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
            (referrer_id, referred_id)
        )
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def reward_referrer_after_payment(referred_id, payment_type):
    """Начислить 7 дней пригласившему после первой оплаты Stars приглашённым."""
    conn = get_conn()
    referral = conn.execute(
        "SELECT * FROM referrals WHERE referred_id=? AND rewarded_at IS NULL",
        (referred_id,)
    ).fetchone()
    if not referral:
        conn.close()
        return None

    rewarded_at = datetime.now().isoformat()
    conn.execute(
        "UPDATE referrals SET rewarded_at=?, reward_payment_type=? WHERE id=?",
        (rewarded_at, payment_type, referral["id"])
    )
    conn.commit()
    conn.close()

    add_bonus_days(referral["referrer_id"], referral["bonus_days"])
    return {
        "referrer_id": referral["referrer_id"],
        "bonus_days": referral["bonus_days"],
    }

# --- STATS ---

def get_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    now = datetime.now().isoformat()
    paying = conn.execute(
        "SELECT COUNT(DISTINCT user_id) as c FROM subscriptions WHERE expires_at>?", (now,)
    ).fetchone()["c"]
    readings = conn.execute("SELECT COUNT(*) as c FROM readings").fetchone()["c"]
    conn.close()
    return {"total": total, "paying": paying, "readings": readings}
