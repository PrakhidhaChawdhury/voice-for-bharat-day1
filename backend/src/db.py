import sqlite3
import json
from datetime import datetime

DB_FILE = "raksha_memory.db"

# Local dataset for Financial Services scheme lookups
DEFAULT_SCHEMES = {
    "pmjjby": {
        "name": "Pradhan Mantri Jeevan Jyoti Bima Yojana",
        "min_age": 18,
        "max_age": 50,
        "cost": "₹436 per year",
        "documents": ["Savings Bank Account", "Consent for Auto-debit"]
    },
    "pmsby": {
        "name": "Pradhan Mantri Suraksha Bima Yojana",
        "min_age": 18,
        "max_age": 70,
        "cost": "₹20 per year",
        "documents": ["Savings Bank Account", "Bank Linked Mobile"]
    },
    "cyber_claim": {
        "name": "National Cyber Crime Reporting Portal Guidance",
        "min_age": 18,
        "max_age": 100,
        "cost": "Free Government Helpline Service (1930)",
        "documents": ["Transaction Acknowledgement ID", "Complaint Reference Copy"]
    }
}

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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schemes (
            scheme_key TEXT PRIMARY KEY,
            name TEXT,
            min_age INTEGER,
            max_age INTEGER,
            cost TEXT,
            documents TEXT
        )
    """)
    
    # Day 7 Table (Ensuring it exists for your escalation tool)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            ticket_id TEXT PRIMARY KEY,
            caller_id TEXT,
            issue_summary TEXT,
            urgency TEXT,
            checks_completed TEXT,
            language TEXT,
            preferred_contact TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Day 8 Table: Call Analytics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            room_id TEXT PRIMARY KEY,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Populate default financial schemes dataset if empty
    cursor.execute("SELECT COUNT(*) FROM schemes")
    if cursor.fetchone()[0] == 0:
        for key, info in DEFAULT_SCHEMES.items():
            cursor.execute("""
                INSERT INTO schemes (scheme_key, name, min_age, max_age, cost, documents)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (key, info["name"], info["min_age"], info["max_age"], info["cost"], json.dumps(info["documents"], ensure_ascii=False)))
            
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

def get_scheme_info(scheme_key: str):
    """Retrieve official scheme requirements from local database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, min_age, max_age, cost, documents FROM schemes WHERE scheme_key = ?", (scheme_key.lower(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0],
            "min_age": row[1],
            "max_age": row[2],
            "cost": row[3],
            "documents": json.loads(row[4]) if row[4] else []
        }
    return None

def save_escalation(data: dict):
    """Day 7: Saves human escalation requests."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO escalations 
        (ticket_id, caller_id, issue_summary, urgency, checks_completed, language, preferred_contact, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("ticket_id"),
        data.get("caller_id"),
        data.get("issue_summary"),
        data.get("urgency"),
        data.get("checks_completed"),
        data.get("language", "Hinglish"),
        data.get("preferred_contact", "Phone"),
        data.get("status", "OPEN")
    ))
    conn.commit()
    conn.close()

# --- DAY 8 ANALYTICS FUNCTIONS ---

def log_call(room_id: str, status: str):
    """Logs or updates the success/fail status of a call."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO calls (room_id, status)
        VALUES (?, ?)
    """, (room_id, status))
    conn.commit()
    conn.close()

def get_call_stats():
    """Fetches total, successful, and failed calls for the dashboard."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM calls")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM calls WHERE status = 'success'")
    success = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM calls WHERE status = 'failed'")
    failed = cursor.fetchone()[0]
    
    conn.close()
    return {"total": total, "success": success, "failed": failed}

# Initialize DB when module loads
init_db()