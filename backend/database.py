import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, select, update, delete, desc, text
from sqlalchemy.orm import sessionmaker, Session
from werkzeug.security import generate_password_hash

from config import settings
import secrets_vault
from models import Base, User, Entry, Goal, WebAuthnCredential, ScaleUploadJob

# Initialize SQLAlchemy 2.0 Engine and Session Factory
DB_URL = f"sqlite:///{settings.DB_PATH}"
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

@contextmanager
def get_session() -> Session:
    """Provide a transactional scope around a series of operations."""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def _migrate_legacy_sqlite_constraints():
    """
    Safely migrate legacy SQLite table constraints (e.g. single-column UNIQUE(date)
    to composite UNIQUE(user_id, date)) while preserving 100% of existing data.
    """
    if not os.path.exists(settings.DB_PATH):
        return

    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()
    
    # Check entries table definition
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='entries'")
    row = cursor.fetchone()
    if row and row[0] and ("date TEXT NOT NULL UNIQUE" in row[0] or "date TEXT UNIQUE" in row[0]):
        # Recreate entries table with composite unique constraint
        cursor.execute("ALTER TABLE entries RENAME TO entries_old")
        cursor.execute('''
            CREATE TABLE entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                date TEXT NOT NULL,
                weight REAL,
                steps INTEGER,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            INSERT INTO entries (id, user_id, date, weight, steps, notes, created_at, updated_at)
            SELECT id, COALESCE(user_id, 1), date, weight, steps, COALESCE(notes, ''), created_at, updated_at
            FROM entries_old
        ''')
        cursor.execute("DROP TABLE entries_old")
        conn.commit()

    conn.close()

def init_db():
    """
    Initialize database tables via SQLAlchemy declarative metadata,
    run constraint migrations, and ensure default seeds exist.
    """
    _migrate_legacy_sqlite_constraints()
    Base.metadata.create_all(bind=engine)

    with get_session() as session:
        # Check if default admin user exists
        admin_user = session.scalars(select(User).where(User.username == "admin")).first()
        if not admin_user:
            default_pwd_hash = generate_password_hash("password123", method="pbkdf2:sha256")
            admin_user = User(
                username="admin",
                password_hash=default_pwd_hash
            )
            session.add(admin_user)
            session.flush()

            admin_goals = Goal(
                user_id=admin_user.id,
                daily_steps_goal=10000,
                target_weight=165.0,
                starting_weight=185.0,
                weight_unit="lbs",
                gemini_api_key=""
            )
            session.add(admin_goals)

# ==========================================
# USER CRUD (SQLAlchemy 2.0 ORM)
# ==========================================

def create_user(username: str, password_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
    clean_username = username.strip()
    with get_session() as session:
        existing = session.scalars(select(User).where(User.username == clean_username)).first()
        if existing:
            return None

        user = User(username=clean_username, password_hash=password_hash)
        session.add(user)
        session.flush()

        goals = Goal(
            user_id=user.id,
            daily_steps_goal=10000,
            target_weight=165.0,
            starting_weight=185.0,
            weight_unit="lbs",
            gemini_api_key=""
        )
        session.add(goals)
        session.flush()

        return user.to_dict()

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            return None
        res = user.to_dict()
        res["password_hash"] = user.password_hash
        return res

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    clean_username = username.strip()
    with get_session() as session:
        user = session.scalars(
            select(User).where(User.username.ilike(clean_username))
        ).first()
        if not user:
            return None
        res = user.to_dict()
        res["password_hash"] = user.password_hash
        return res

# ==========================================
# WEBAUTHN PASSKEYS (SQLAlchemy 2.0 ORM)
# ==========================================

def save_webauthn_credential(
    user_id: int,
    credential_id: str,
    public_key: str,
    sign_count: int = 0,
    transports: str = '["internal"]',
    nickname: str = "Biometric Device"
) -> Dict[str, Any]:
    with get_session() as session:
        cred = session.scalars(
            select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id)
        ).first()

        if cred:
            cred.user_id = user_id
            cred.public_key = public_key
            cred.sign_count = sign_count
            cred.transports = str(transports)
            cred.nickname = nickname
        else:
            cred = WebAuthnCredential(
                user_id=user_id,
                credential_id=credential_id,
                public_key=public_key,
                sign_count=sign_count,
                transports=str(transports),
                nickname=nickname
            )
            session.add(cred)

        session.flush()
        return cred.to_dict()

def get_webauthn_credentials_for_user(user_id: int) -> List[Dict[str, Any]]:
    with get_session() as session:
        creds = session.scalars(
            select(WebAuthnCredential)
            .where(WebAuthnCredential.user_id == user_id)
            .order_by(desc(WebAuthnCredential.created_at))
        ).all()
        return [c.to_dict() for c in creds]

def get_webauthn_credential_by_id(credential_id: str) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        cred = session.scalars(
            select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id)
        ).first()
        if not cred:
            return None
        res = cred.to_dict()
        res["username"] = cred.user.username if cred.user else ""
        return res

def update_webauthn_sign_count(credential_id: str, sign_count: int) -> None:
    with get_session() as session:
        session.execute(
            update(WebAuthnCredential)
            .where(WebAuthnCredential.credential_id == credential_id)
            .values(sign_count=sign_count)
        )

def delete_webauthn_credential(cred_id: int, user_id: int) -> bool:
    with get_session() as session:
        cred = session.scalars(
            select(WebAuthnCredential).where(
                WebAuthnCredential.id == cred_id,
                WebAuthnCredential.user_id == user_id
            )
        ).first()
        if cred:
            session.delete(cred)
            return True
        return False

# ==========================================
# SCALE UPLOAD JOBS (SQLAlchemy 2.0 ORM)
# ==========================================

def create_scale_upload_job(user_id: int) -> int:
    with get_session() as session:
        job = ScaleUploadJob(
            user_id=user_id,
            status="processing"
        )
        session.add(job)
        session.flush()
        return job.id

def update_scale_upload_job(
    job_id: int,
    status: str,
    weight: Optional[float] = None,
    unit: str = "lbs",
    date: Optional[str] = None,
    time: Optional[str] = None,
    error: Optional[str] = None,
    notes: Optional[str] = None
) -> None:
    with get_session() as session:
        session.execute(
            update(ScaleUploadJob)
            .where(ScaleUploadJob.id == job_id)
            .values(
                status=status,
                weight=weight,
                unit=unit,
                date=date,
                time=time,
                error=error,
                notes=notes
            )
        )

def get_active_scale_upload_jobs(user_id: int) -> List[Dict[str, Any]]:
    with get_session() as session:
        jobs = session.scalars(
            select(ScaleUploadJob)
            .where(
                ScaleUploadJob.user_id == user_id,
                ScaleUploadJob.dismissed == 0
            )
            .order_by(desc(ScaleUploadJob.id))
            .limit(5)
        ).all()
        return [j.to_dict() for j in jobs]

def dismiss_scale_upload_job(job_id: int, user_id: int) -> None:
    with get_session() as session:
        session.execute(
            update(ScaleUploadJob)
            .where(
                ScaleUploadJob.id == job_id,
                ScaleUploadJob.user_id == user_id
            )
            .values(dismissed=1)
        )

# ==========================================
# ENTRIES CRUD (SQLAlchemy 2.0 ORM)
# ==========================================

def get_all_entries(user_id: int) -> List[Dict[str, Any]]:
    with get_session() as session:
        entries = session.scalars(
            select(Entry)
            .where(Entry.user_id == user_id)
            .order_by(desc(Entry.date))
        ).all()
        return [e.to_dict() for e in entries]

def get_entry_by_date(user_id: int, date_str: str) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        entry = session.scalars(
            select(Entry).where(
                Entry.user_id == user_id,
                Entry.date == date_str
            )
        ).first()
        return entry.to_dict() if entry else None

def get_entry_by_id(user_id: int, entry_id: int) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        entry = session.scalars(
            select(Entry).where(
                Entry.id == entry_id,
                Entry.user_id == user_id
            )
        ).first()
        return entry.to_dict() if entry else None

def upsert_entry(
    user_id: int,
    date_str: str,
    weight: Optional[float] = None,
    steps: Optional[int] = None,
    notes: str = ""
) -> Dict[str, Any]:
    with get_session() as session:
        entry = session.scalars(
            select(Entry).where(
                Entry.user_id == user_id,
                Entry.date == date_str
            )
        ).first()

        now = datetime.now(timezone.utc)
        if entry:
            if weight is not None:
                entry.weight = weight
            if steps is not None:
                entry.steps = steps
            if notes:
                entry.notes = notes
            entry.updated_at = now
        else:
            entry = Entry(
                user_id=user_id,
                date=date_str,
                weight=weight,
                steps=steps,
                notes=notes or "",
                created_at=now,
                updated_at=now
            )
            session.add(entry)

        session.flush()
        return entry.to_dict()

def update_entry(
    user_id: int,
    entry_id: int,
    date_str: str,
    weight: Optional[float] = None,
    steps: Optional[int] = None,
    notes: str = ""
) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        entry = session.scalars(
            select(Entry).where(
                Entry.id == entry_id,
                Entry.user_id == user_id
            )
        ).first()

        if not entry:
            return None

        entry.date = date_str
        if weight is not None:
            entry.weight = weight
        if steps is not None:
            entry.steps = steps
        if notes is not None:
            entry.notes = notes
        entry.updated_at = datetime.now(timezone.utc)
        
        session.flush()
        return entry.to_dict()

def delete_entry(user_id: int, entry_id: int) -> bool:
    with get_session() as session:
        entry = session.scalars(
            select(Entry).where(
                Entry.id == entry_id,
                Entry.user_id == user_id
            )
        ).first()
        if entry:
            session.delete(entry)
            return True
        return False

# ==========================================
# GOALS & SETTINGS WITH SECRETS VAULT
# ==========================================

def get_goals(user_id: int) -> Dict[str, Any]:
    with get_session() as session:
        goals = session.scalars(
            select(Goal).where(Goal.user_id == user_id)
        ).first()

        if not goals:
            goals = Goal(
                user_id=user_id,
                daily_steps_goal=10000,
                target_weight=165.0,
                starting_weight=185.0,
                weight_unit="lbs",
                gemini_api_key=""
            )
            session.add(goals)
            session.flush()

        res = goals.to_dict()
        raw_encrypted_key = res.get("gemini_api_key", "")
        res["gemini_api_key"] = secrets_vault.decrypt_secret(raw_encrypted_key)
        return res

def update_goals(
    user_id: int,
    daily_steps_goal: int,
    target_weight: float,
    starting_weight: float,
    weight_unit: str = "lbs",
    gemini_api_key: str = ""
) -> Dict[str, Any]:
    with get_session() as session:
        goals = session.scalars(
            select(Goal).where(Goal.user_id == user_id)
        ).first()

        encrypted_key = secrets_vault.encrypt_secret(gemini_api_key) if gemini_api_key else ""
        now = datetime.now(timezone.utc)

        if not goals:
            goals = Goal(
                user_id=user_id,
                daily_steps_goal=daily_steps_goal,
                target_weight=target_weight,
                starting_weight=starting_weight,
                weight_unit=weight_unit,
                gemini_api_key=encrypted_key,
                updated_at=now
            )
            session.add(goals)
        else:
            goals.daily_steps_goal = daily_steps_goal
            goals.target_weight = target_weight
            goals.starting_weight = starting_weight
            goals.weight_unit = weight_unit
            if gemini_api_key:
                goals.gemini_api_key = encrypted_key
            goals.updated_at = now

        session.flush()
        res = goals.to_dict()
        res["gemini_api_key"] = secrets_vault.decrypt_secret(res.get("gemini_api_key", ""))
        return res
