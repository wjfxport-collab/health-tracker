from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Text, Float, Integer, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships with cascading delete
    entries: Mapped[List["Entry"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Entry.date)"
    )
    goals: Mapped[Optional["Goal"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    webauthn_credentials: Mapped[List["WebAuthnCredential"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    scale_upload_jobs: Mapped[List["ScaleUploadJob"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(ScaleUploadJob.id)"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Entry(Base):
    __tablename__ = "entries"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_entry_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        default=1,
        index=True
    )
    date: Mapped[str] = mapped_column(String(10), nullable=False) # YYYY-MM-DD
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="entries")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date,
            "weight": self.weight,
            "steps": self.steps,
            "notes": self.notes or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_goal"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        default=1,
        unique=True,
        index=True
    )
    daily_steps_goal: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    target_weight: Mapped[float] = mapped_column(Float, default=165.0, nullable=False)
    starting_weight: Mapped[float] = mapped_column(Float, default=185.0, nullable=False)
    weight_unit: Mapped[str] = mapped_column(String(10), default="lbs", nullable=False)
    gemini_api_key: Mapped[str] = mapped_column(Text, default="", nullable=False) # Encrypted at rest
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="goals")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "daily_steps_goal": self.daily_steps_goal,
            "target_weight": self.target_weight,
            "starting_weight": self.starting_weight,
            "weight_unit": self.weight_unit,
            "gemini_api_key": self.gemini_api_key,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class WebAuthnCredential(Base):
    __tablename__ = "webauthn_credentials"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    credential_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transports: Mapped[str] = mapped_column(String(64), default='["internal"]', nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), default="Biometric Device", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="webauthn_credentials")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "credential_id": self.credential_id,
            "nickname": self.nickname,
            "sign_count": self.sign_count,
            "transports": self.transports,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ScaleUploadJob(Base):
    __tablename__ = "scale_upload_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="processing", nullable=False) # processing, completed, failed
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(10), default="lbs", nullable=False)
    date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dismissed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="scale_upload_jobs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "weight": self.weight,
            "unit": self.unit,
            "date": self.date,
            "time": self.time,
            "error": self.error,
            "notes": self.notes,
            "dismissed": bool(self.dismissed),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
