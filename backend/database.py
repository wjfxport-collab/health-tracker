import os
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, select, update, delete, desc, text
from sqlalchemy.orm import sessionmaker, Session
from werkzeug.security import generate_password_hash

from config import settings
import secrets_vault
from models import Base, User, Entry, Goal, WebAuthnCredential, ScaleUploadJob, MetricDefinition, MetricEntry
from plugin_engine import plugin_engine

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
    Safely migrate legacy SQLite table constraints while preserving 100% of existing data.
    """
    if not os.path.exists(settings.DB_PATH):
        return

    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='entries'")
    row = cursor.fetchone()
    if row and row[0] and ("date TEXT NOT NULL UNIQUE" in row[0] or "date TEXT UNIQUE" in row[0]):
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

def sync_plugins_to_database():
    """
    Sync all discovered component manifests from the plugins/ directory
    into the database MetricDefinition table.
    """
    plugins = plugin_engine.reload_plugins()
    with get_session() as session:
        for plugin_id, manifest in plugins.items():
            existing = session.get(MetricDefinition, plugin_id)
            manifest_str = json.dumps(manifest)
            if not existing:
                metric_def = MetricDefinition(
                    id=plugin_id,
                    name=manifest.get("name", plugin_id.title()),
                    category=manifest.get("category", "health"),
                    manifest_json=manifest_str,
                    is_active=True
                )
                session.add(metric_def)
            else:
                existing.name = manifest.get("name", plugin_id.title())
                existing.category = manifest.get("category", "health")
                existing.manifest_json = manifest_str

def init_db():
    """
    Initialize database tables via SQLAlchemy declarative metadata,
    run constraint migrations, seed admin account, and sync plugins.
    """
    _migrate_legacy_sqlite_constraints()
    Base.metadata.create_all(bind=engine)
    sync_plugins_to_database()

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
# METRIC DEFINITIONS & DYNAMIC PLUGINS
# ==========================================

def get_all_active_metric_definitions() -> List[Dict[str, Any]]:
    with get_session() as session:
        defs = session.scalars(
            select(MetricDefinition).where(MetricDefinition.is_active == True)
        ).all()
        return [d.to_dict() for d in defs]

def get_metric_definition(metric_id: str) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        d = session.get(MetricDefinition, metric_id)
        return d.to_dict() if d else None

# ==========================================
# DYNAMIC METRIC ENTRIES CRUD
# ==========================================

def upsert_metric_entry(
    user_id: int,
    metric_id: str,
    date_str: str,
    payload: Dict[str, Any],
    notes: str = ""
) -> Dict[str, Any]:
    """
    Create or update a generic MetricEntry for any metric plugin.
    Maintains 100% two-way sync with the legacy Entry model for weight and steps.
    """
    payload_str = json.dumps(payload)
    now = datetime.now(timezone.utc)

    with get_session() as session:
        # For single-day unique metrics like weight and steps, find existing by (user_id, metric_id, date)
        # For equipment sessions (camera_log), multiple sessions per day are permitted if distinct time
        entry = None
        if metric_id in ("weight", "steps"):
            entry = session.scalars(
                select(MetricEntry).where(
                    MetricEntry.user_id == user_id,
                    MetricEntry.metric_id == metric_id,
                    MetricEntry.date == date_str
                )
            ).first()

        if entry:
            entry.payload_json = payload_str
            entry.notes = notes or ""
            entry.updated_at = now
        else:
            entry = MetricEntry(
                user_id=user_id,
                metric_id=metric_id,
                date=date_str,
                payload_json=payload_str,
                notes=notes or "",
                created_at=now,
                updated_at=now
            )
            session.add(entry)

        # Backward compatibility bridge: sync weight and steps to legacy Entry table
        if metric_id == "weight" and "weight" in payload:
            w_val = float(payload["weight"]) if payload["weight"] is not None else None
            legacy_entry = session.scalars(
                select(Entry).where(Entry.user_id == user_id, Entry.date == date_str)
            ).first()
            if legacy_entry:
                legacy_entry.weight = w_val
                if notes:
                    legacy_entry.notes = notes
            else:
                session.add(Entry(user_id=user_id, date=date_str, weight=w_val, steps=None, notes=notes or ""))

        elif metric_id == "steps" and "steps" in payload:
            s_val = int(payload["steps"]) if payload["steps"] is not None else None
            legacy_entry = session.scalars(
                select(Entry).where(Entry.user_id == user_id, Entry.date == date_str)
            ).first()
            if legacy_entry:
                legacy_entry.steps = s_val
                if notes:
                    legacy_entry.notes = notes
            else:
                session.add(Entry(user_id=user_id, date=date_str, weight=None, steps=s_val, notes=notes or ""))

        session.flush()
        return entry.to_dict()

def get_metric_entries(
    user_id: int,
    metric_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict[str, Any]]:
    with get_session() as session:
        query = select(MetricEntry).where(MetricEntry.user_id == user_id)
        if metric_id:
            query = query.where(MetricEntry.metric_id == metric_id)
        if date_from:
            query = query.where(MetricEntry.date >= date_from)
        if date_to:
            query = query.where(MetricEntry.date <= date_to)

        query = query.order_by(desc(MetricEntry.date), desc(MetricEntry.id))
        entries = session.scalars(query).all()
        return [e.to_dict() for e in entries]

def get_metric_entry_by_id(entry_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        e = session.scalars(
            select(MetricEntry).where(MetricEntry.id == entry_id, MetricEntry.user_id == user_id)
        ).first()
        return e.to_dict() if e else None

def update_metric_entry(
    user_id: int,
    entry_id: int,
    date_str: str,
    payload: Dict[str, Any],
    notes: str = ""
) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        entry = session.scalars(
            select(MetricEntry).where(MetricEntry.id == entry_id, MetricEntry.user_id == user_id)
        ).first()
        if not entry:
            return None

        entry.date = date_str
        entry.payload_json = json.dumps(payload)
        entry.notes = notes or ""
        entry.updated_at = datetime.now(timezone.utc)
        session.flush()
        return entry.to_dict()

def delete_metric_entry(user_id: int, entry_id: int) -> bool:
    with get_session() as session:
        entry = session.scalars(
            select(MetricEntry).where(MetricEntry.id == entry_id, MetricEntry.user_id == user_id)
        ).first()
        if entry:
            session.delete(entry)
            return True
        return False

# ==========================================
# USERS CRUD
# ==========================================

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        user = session.get(User, user_id)
        return user.to_dict() if user else None

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    if not username:
        return None
    with get_session() as session:
        user = session.scalars(
            select(User).where(User.username == username.strip())
        ).first()
        if user:
            res = user.to_dict()
            res["password_hash"] = user.password_hash
            return res
        return None

def create_user(username: str, password_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        clean_user = username.strip()
        existing = session.scalars(select(User).where(User.username == clean_user)).first()
        if existing:
            return None

        new_user = User(username=clean_user, password_hash=password_hash)
        session.add(new_user)
        session.flush()

        goals = Goal(
            user_id=new_user.id,
            daily_steps_goal=10000,
            target_weight=165.0,
            starting_weight=185.0,
            weight_unit="lbs",
            gemini_api_key=""
        )
        session.add(goals)
        session.flush()

        return new_user.to_dict()

# ==========================================
# WEBAUTHN / PASSKEY CREDENTIALS
# ==========================================

def save_webauthn_credential(user_id: int, credential_id: str, public_key: str, nickname: str = "Biometric Device") -> Dict[str, Any]:
    with get_session() as session:
        existing = session.scalars(select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id)).first()
        if existing:
            existing.user_id = user_id
            existing.public_key = public_key
            existing.nickname = nickname
            session.flush()
            return existing.to_dict()

        cred = WebAuthnCredential(
            user_id=user_id,
            credential_id=credential_id,
            public_key=public_key,
            nickname=nickname
        )
        session.add(cred)
        session.flush()
        return cred.to_dict()

def get_webauthn_credentials_for_user(user_id: int) -> List[Dict[str, Any]]:
    with get_session() as session:
        creds = session.scalars(
            select(WebAuthnCredential).where(WebAuthnCredential.user_id == user_id).order_by(desc(WebAuthnCredential.created_at))
        ).all()
        return [c.to_dict() for c in creds]

def get_webauthn_credential_by_id(credential_id: str) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        cred = session.scalars(
            select(WebAuthnCredential).where(WebAuthnCredential.credential_id == credential_id)
        ).first()
        if cred:
            user = session.get(User, cred.user_id)
            res = cred.to_dict()
            res["username"] = user.username if user else ""
            return res
        return None

def delete_webauthn_credential(cred_id: int, user_id: int) -> bool:
    with get_session() as session:
        cred = session.scalars(
            select(WebAuthnCredential).where(WebAuthnCredential.id == cred_id, WebAuthnCredential.user_id == user_id)
        ).first()
        if cred:
            session.delete(cred)
            return True
        return False

# ==========================================
# ASYNC SCALE UPLOAD JOBS
# ==========================================

def create_scale_upload_job(user_id: int) -> int:
    with get_session() as session:
        job = ScaleUploadJob(user_id=user_id, status="processing")
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
) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        job = session.get(ScaleUploadJob, job_id)
        if not job:
            return None

        job.status = status
        if weight is not None:
            job.weight = weight
        if unit:
            job.unit = unit
        if date:
            job.date = date
        if time:
            job.time = time
        if error is not None:
            job.error = error
        if notes is not None:
            job.notes = notes

        session.flush()
        return job.to_dict()

def get_active_scale_upload_jobs(user_id: int) -> List[Dict[str, Any]]:
    with get_session() as session:
        jobs = session.scalars(
            select(ScaleUploadJob).where(
                ScaleUploadJob.user_id == user_id,
                ScaleUploadJob.dismissed == 0
            ).order_by(desc(ScaleUploadJob.id))
        ).all()
        return [j.to_dict() for j in jobs]

def dismiss_scale_upload_job(job_id: int, user_id: int) -> bool:
    with get_session() as session:
        job = session.scalars(
            select(ScaleUploadJob).where(ScaleUploadJob.id == job_id, ScaleUploadJob.user_id == user_id)
        ).first()
        if job:
            job.dismissed = 1
            return True
        return False

# ==========================================
# LEGACY ENTRIES CRUD (Backward Compatibility)
# ==========================================

def get_all_entries(user_id: int) -> List[Dict[str, Any]]:
    with get_session() as session:
        entries = session.scalars(
            select(Entry).where(Entry.user_id == user_id).order_by(desc(Entry.date))
        ).all()
        return [e.to_dict() for e in entries]

def get_entry_by_date(user_id: int, date_str: str) -> Optional[Dict[str, Any]]:
    with get_session() as session:
        entry = session.scalars(
            select(Entry).where(Entry.user_id == user_id, Entry.date == date_str)
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
            select(Entry).where(Entry.user_id == user_id, Entry.date == date_str)
        ).first()

        now = datetime.now(timezone.utc)
        if entry:
            if weight is not None:
                entry.weight = weight
            if steps is not None:
                entry.steps = steps
            if notes is not None and notes != "":
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
        res = entry.to_dict()

    # Sync to MetricEntry store
    if weight is not None:
        upsert_metric_entry(user_id, "weight", date_str, {"weight": weight}, notes=notes)
    if steps is not None:
        upsert_metric_entry(user_id, "steps", date_str, {"steps": steps}, notes=notes)

    return res

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
            select(Entry).where(Entry.id == entry_id, Entry.user_id == user_id)
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
            select(Entry).where(Entry.id == entry_id, Entry.user_id == user_id)
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
        goals = session.scalars(select(Goal).where(Goal.user_id == user_id)).first()

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
        goals = session.scalars(select(Goal).where(Goal.user_id == user_id)).first()
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
