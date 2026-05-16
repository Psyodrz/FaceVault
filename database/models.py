"""
FaceVault Models - SQLAlchemy ORM models and Pydantic schemas.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, Text, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel
from database.database import Base


# ─── SQLAlchemy ORM Models ───────────────────────────────────────

class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    label_id = Column(Integer, unique=True, nullable=False)
    image_count = Column(Integer, default=0)
    thumbnail = Column(Text, nullable=True)  # Base64 encoded thumbnail
    recognition_count = Column(Integer, default=0)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, nullable=False, index=True)
    person_name = Column(String(100), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(String(20), default="present")  # present, late, early_leave
    confidence = Column(Float, default=0.0)


class RecognitionEvent(Base):
    __tablename__ = "recognition_events"

    id = Column(Integer, primary_key=True, index=True)
    person_name = Column(String(100), nullable=True)
    is_known = Column(Boolean, default=False)
    confidence = Column(Float, default=0.0)
    emotion = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="admin") # super_admin, admin, visitor
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False) # LOGIN, DELETE_PERSON, ADD_PHOTO, etc.
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, server_default=func.now(), index=True)

class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer, nullable=False)
    face_count = Column(Integer, default=0)
    known_count = Column(Integer, default=0)
    unknown_count = Column(Integer, default=0)
    avg_confidence = Column(Float, default=0.0)
    emotions = Column(JSON, nullable=True)  # {"happy": 5, "sad": 2, ...}

class ThreatEvent(Base):
    __tablename__ = "threat_events"

    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String(20), nullable=False) # critical, warning, info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    zone = Column(String(100), nullable=True)
    status = Column(String(20), default="pending") # pending, acknowledged, resolved
    timestamp = Column(DateTime, server_default=func.now(), index=True)


# ─── Pydantic Schemas ────────────────────────────────────────────

class PersonCreate(BaseModel):
    name: str

class PersonResponse(BaseModel):
    id: int
    name: str
    label_id: int
    image_count: int
    thumbnail: Optional[str] = None
    recognition_count: int
    last_seen: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AttendanceResponse(BaseModel):
    id: int
    person_id: int
    person_name: str
    check_in: datetime
    check_out: Optional[datetime] = None
    date: date
    status: str
    confidence: float

    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    total_people: int
    total_recognitions: int
    today_detections: int
    avg_confidence: float
    hourly_data: list
    daily_data: list
    emotion_data: dict

class DetectionResult(BaseModel):
    face_count: int
    faces: list
    timestamp: str

class RecognitionResult(BaseModel):
    name: str
    confidence: float
    location: list

class AnonymizeRequest(BaseModel):
    blur_strength: int = 51
    mode: str = "blur"  # blur, pixelate, solid

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "visitor"

class AuditLogResponse(BaseModel):
    id: int
    username: str
    action: str
    details: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class CompareResult(BaseModel):
    similarity: float
    verified: bool
    threshold: float
