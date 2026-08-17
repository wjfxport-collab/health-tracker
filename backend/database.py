import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracker.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. WebAuthn / Passkey Credentials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS webauthn_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            credential_id TEXT NOT NULL UNIQUE,
            public_key TEXT NOT NULL,
            sign_count INTEGER DEFAULT 0,
            transports TEXT DEFAULT '["internal"]',
            nickname TEXT DEFAULT 'Biometric Device',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 3. Scale Upload Background Jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scale_upload_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'processing', -- processing, completed, failed
            weight REAL,
            unit TEXT DEFAULT 'lbs',
            date TEXT,
            time TEXT,
            error TEXT,
            notes TEXT,
            dismissed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 4. Entries table (Daily weight & steps)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            date TEXT NOT NULL,
            weight REAL,
            steps INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 5. Goals and Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            daily_steps_goal INTEGER DEFAULT 10000,
            target_weight REAL DEFAULT 165.0,
            starting_weight REAL DEFAULT 185.0,
            weight_unit TEXT DEFAULT 'lbs',
            gemini_api_key TEXT DEFAULT '',
            ocr_engine TEXT DEFAULT 'gemini',
            local_llm_url TEXT DEFAULT '',
            local_llm_model TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Check for column migrations FIRST
    cursor.execute("PRAGMA table_info(entries)")
    entry_cols = [col['name'] for col in cursor.fetchall()]
    if 'user_id' not in entry_cols:
        cursor.execute("ALTER TABLE entries ADD COLUMN user_id INTEGER DEFAULT 1")

    cursor.execute("PRAGMA table_info(goals)")
    goal_cols = [col['name'] for col in cursor.fetchall()]
    if 'user_id' not in goal_cols:
        cursor.execute("ALTER TABLE goals ADD COLUMN user_id INTEGER DEFAULT 1")
    if 'gemini_api_key' not in goal_cols:
        cursor.execute("ALTER TABLE goals ADD COLUMN gemini_api_key TEXT DEFAULT ''")

    # Now create unique indices safely
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_date ON entries(user_id, date)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_goals ON goals(user_id)")

    # Ensure at least one default user exists for existing data
    cursor.execute('SELECT COUNT(*) as count FROM users')
    if cursor.fetchone()['count'] == 0:
        default_pwd_hash = generate_password_hash("password123", method='pbkdf2:sha256')
        cursor.execute('''
            INSERT INTO users (id, username, password_hash)
            VALUES (1, 'admin', ?)
        ''', (default_pwd_hash,))
        
        # Ensure default goals row exists for user 1
        cursor.execute('''
            INSERT OR IGNORE INTO goals (user_id, daily_steps_goal, target_weight, starting_weight, weight_unit)
            VALUES (1, 10000, 165.0, 185.0, 'lbs')
        ''')
    
    conn.commit()
    conn.close()

# --- User CRUD ---

def create_user(username, password_hash=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, created_at)
            VALUES (?, ?, ?)
        ''', (username.strip(), password_hash, now))
        conn.commit()
        user_id = cursor.lastrowid
        
        # Create default goals for this user
        cursor.execute('''
            INSERT INTO goals (user_id, daily_steps_goal, target_weight, starting_weight, weight_unit)
            VALUES (?, 10000, 165.0, 185.0, 'lbs')
        ''', (user_id,))
        conn.commit()
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash, created_at FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash, created_at FROM users WHERE LOWER(username) = LOWER(?)', (username.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# --- WebAuthn Credentials ---

def save_webauthn_credential(user_id, credential_id, public_key, sign_count=0, transports='["internal"]', nickname='Biometric Device'):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT INTO webauthn_credentials (user_id, credential_id, public_key, sign_count, transports, nickname, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(credential_id) DO UPDATE SET
            public_key = excluded.public_key,
            sign_count = excluded.sign_count,
            transports = excluded.transports,
            nickname = excluded.nickname
    ''', (user_id, credential_id, public_key, sign_count, str(transports), nickname, now))
    conn.commit()
    conn.close()

def get_webauthn_credentials_for_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, credential_id, nickname, sign_count, transports, created_at FROM webauthn_credentials WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_webauthn_credential_by_id(credential_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT w.*, u.username FROM webauthn_credentials w JOIN users u ON w.user_id = u.id WHERE w.credential_id = ?', (credential_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_webauthn_sign_count(credential_id, sign_count):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE webauthn_credentials SET sign_count = ? WHERE credential_id = ?', (sign_count, credential_id))
    conn.commit()
    conn.close()

def delete_webauthn_credential(cred_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM webauthn_credentials WHERE id = ? AND user_id = ?', (cred_id, user_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# --- Scale Upload Background Jobs ---

def create_scale_upload_job(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT INTO scale_upload_jobs (user_id, status, created_at)
        VALUES (?, 'processing', ?)
    ''', (user_id, now))
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    return job_id

def update_scale_upload_job(job_id, status, weight=None, unit='lbs', date=None, time=None, error=None, notes=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE scale_upload_jobs
        SET status = ?, weight = ?, unit = ?, date = ?, time = ?, error = ?, notes = ?
        WHERE id = ?
    ''', (status, weight, unit, date, time, error, notes, job_id))
    conn.commit()
    conn.close()

def get_active_scale_upload_jobs(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM scale_upload_jobs
        WHERE user_id = ? AND dismissed = 0
        ORDER BY id DESC LIMIT 5
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def dismiss_scale_upload_job(job_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE scale_upload_jobs SET dismissed = 1 WHERE id = ? AND user_id = ?', (job_id, user_id))
    conn.commit()
    conn.close()

# --- User-Scoped Entries CRUD ---

def get_all_entries(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM entries WHERE user_id = ? ORDER BY date DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_entry_by_date(user_id, date_str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM entries WHERE user_id = ? AND date = ?', (user_id, date_str))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_entry_by_id(user_id, entry_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM entries WHERE user_id = ? AND id = ?', (user_id, entry_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_entry(user_id, date_str, weight=None, steps=None, notes=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute('''
        INSERT INTO entries (user_id, date, weight, steps, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, date) DO UPDATE SET
            weight = COALESCE(excluded.weight, entries.weight),
            steps = COALESCE(excluded.steps, entries.steps),
            notes = COALESCE(excluded.notes, entries.notes),
            updated_at = excluded.updated_at
    ''', (user_id, date_str, weight, steps, notes, now, now))
    
    conn.commit()
    conn.close()
    return get_entry_by_date(user_id, date_str)

def update_entry(user_id, entry_id, date_str, weight=None, steps=None, notes=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute('''
        UPDATE entries
        SET date = ?, weight = ?, steps = ?, notes = ?, updated_at = ?
        WHERE user_id = ? AND id = ?
    ''', (date_str, weight, steps, notes, now, user_id, entry_id))
    
    conn.commit()
    conn.close()
    return get_entry_by_id(user_id, entry_id)

def delete_entry(user_id, entry_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM entries WHERE user_id = ? AND id = ?', (user_id, entry_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# --- User-Scoped Goals & Settings ---

def get_goals(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM goals WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute('''
            INSERT INTO goals (user_id, daily_steps_goal, target_weight, starting_weight, weight_unit)
            VALUES (?, 10000, 165.0, 185.0, 'lbs')
        ''', (user_id,))
        conn.commit()
        cursor.execute('SELECT * FROM goals WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
    conn.close()
    return dict(row)

def update_goals(user_id, daily_steps_goal, target_weight, starting_weight, weight_unit='lbs', gemini_api_key=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute('''
        INSERT INTO goals (user_id, daily_steps_goal, target_weight, starting_weight, weight_unit, gemini_api_key, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            daily_steps_goal = excluded.daily_steps_goal,
            target_weight = excluded.target_weight,
            starting_weight = excluded.starting_weight,
            weight_unit = excluded.weight_unit,
            gemini_api_key = CASE WHEN excluded.gemini_api_key != '' THEN excluded.gemini_api_key ELSE goals.gemini_api_key END,
            updated_at = excluded.updated_at
    ''', (user_id, daily_steps_goal, target_weight, starting_weight, weight_unit, gemini_api_key, now))
    
    conn.commit()
    conn.close()
    return get_goals(user_id)
