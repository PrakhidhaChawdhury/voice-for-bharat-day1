import sqlite3
import json
from datetime import datetime

DB_FILE = "raksha_memory.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, language_preference, facts, last_interaction FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0],
            "language_preference": row[1],
            "facts": json.loads(row[2]) if row[2] else {},
            "last_interaction": row[3]
        }
    return None

def save_user(user_id: str, name: str, language_preference: str, facts: dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    facts_json = json.dumps(facts, ensure_ascii=False)
    cursor.execute("""
        INSERT INTO users (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            language_preference=excluded.language_preference,
            facts=excluded.facts,
            last_interaction=excluded.last_interaction
    """, (user_id, name, language_preference, facts_json, now))
    conn.commit()
    conn.close()

# Initialize DB when module loads
init_db()