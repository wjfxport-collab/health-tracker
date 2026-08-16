import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracker.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            weight REAL,
            steps INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Goals and AI settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            daily_steps_goal INTEGER DEFAULT 10000,
            target_weight REAL DEFAULT 165.0,
            starting_weight REAL DEFAULT 185.0,
            weight_unit TEXT DEFAULT 'lbs',
            gemini_api_key TEXT DEFAULT '',
            ocr_engine TEXT DEFAULT 'gemini',
            local_llm_url TEXT DEFAULT 'http://192.168.4.27:11434',
            local_llm_model TEXT DEFAULT 'gemma-4-12b',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check for column migrations on existing tables
    cursor.execute("PRAGMA table_info(goals)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'gemini_api_key' not in columns:
        cursor.execute("ALTER TABLE goals ADD COLUMN gemini_api_key TEXT DEFAULT ''")
    if 'ocr_engine' not in columns:
        cursor.execute("ALTER TABLE goals ADD COLUMN ocr_engine TEXT DEFAULT 'gemini'")
    if 'local_llm_url' not in columns:
        cursor.execute("ALTER TABLE goals ADD COLUMN local_llm_url TEXT DEFAULT 'http://192.168.4.27:11434'")
    if 'local_llm_model' not in columns:
        cursor.execute("ALTER TABLE goals ADD COLUMN local_llm_model TEXT DEFAULT 'gemma-4-12b'")
    
    # Ensure default goals row exists
    cursor.execute('SELECT COUNT(*) as count FROM goals')
    if cursor.fetchone()['count'] == 0:
        cursor.execute('''
            INSERT INTO goals (daily_steps_goal, target_weight, starting_weight, weight_unit, gemini_api_key, ocr_engine, local_llm_url, local_llm_model)
            VALUES (10000, 165.0, 185.0, 'lbs', '', 'gemini', 'http://192.168.4.27:11434', 'gemma-4-12b')
        ''')
    
    conn.commit()
    conn.close()

def get_all_entries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM entries ORDER BY date DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_entry_by_date(date_str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM entries WHERE date = ?', (date_str,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_entry_by_id(entry_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM entries WHERE id = ?', (entry_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_entry(date_str, weight=None, steps=None, notes=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute('''
        INSERT INTO entries (date, weight, steps, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            weight = COALESCE(excluded.weight, entries.weight),
            steps = COALESCE(excluded.steps, entries.steps),
            notes = COALESCE(excluded.notes, entries.notes),
            updated_at = excluded.updated_at
    ''', (date_str, weight, steps, notes, now, now))
    
    conn.commit()
    entry_id = cursor.lastrowid
    conn.close()
    return get_entry_by_date(date_str)

def update_entry(entry_id, date_str, weight=None, steps=None, notes=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute('''
        UPDATE entries
        SET date = ?, weight = ?, steps = ?, notes = ?, updated_at = ?
        WHERE id = ?
    ''', (date_str, weight, steps, notes, now, entry_id))
    
    conn.commit()
    conn.close()
    return get_entry_by_id(entry_id)

def delete_entry(entry_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM entries WHERE id = ?', (entry_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_goals():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM goals ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {
        'daily_steps_goal': 10000,
        'target_weight': 165.0,
        'starting_weight': 185.0,
        'weight_unit': 'lbs',
        'gemini_api_key': '',
        'ocr_engine': 'gemini',
        'local_llm_url': 'http://192.168.4.27:11434',
        'local_llm_model': 'gemma-4-12b'
    }

def update_goals(daily_steps_goal, target_weight, starting_weight, weight_unit='lbs', gemini_api_key='', ocr_engine='gemini', local_llm_url='http://192.168.4.27:11434', local_llm_model='gemma-4-12b'):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute('''
        UPDATE goals
        SET daily_steps_goal = ?, target_weight = ?, starting_weight = ?, weight_unit = ?, gemini_api_key = ?, ocr_engine = ?, local_llm_url = ?, local_llm_model = ?, updated_at = ?
        WHERE id = (SELECT id FROM goals ORDER BY id DESC LIMIT 1)
    ''', (daily_steps_goal, target_weight, starting_weight, weight_unit, gemini_api_key, ocr_engine, local_llm_url, local_llm_model, now))
    
    conn.commit()
    conn.close()
    return get_goals()
