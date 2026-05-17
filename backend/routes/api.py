"""
FaceVault API Routes - Detection, Recognition, Attendance, Analysis, Liveness, Anonymizer.
All routes consolidated into a single file for simplicity.
"""

import cv2
import numpy as np
import base64
import json
import uuid
import io
from datetime import datetime, date, timedelta
from typing import Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
import pandas as pd
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from database.database import get_db, SessionLocal
from database.models import Person, AttendanceLog, RecognitionEvent, AnalyticsSnapshot, User, ThreatEvent, AuditLog
from fastapi import Request

def log_audit(db: Session, user: User, action: str, details: str = None, request: Request = None):
    ip = request.client.host if request else None
    audit = AuditLog(
        user_id=user.id,
        username=user.username,
        action=action,
        details=details,
        ip_address=ip
    )
    db.add(audit)
    db.commit()
from backend.auth import get_current_user, get_current_active_admin, get_current_super_admin, verify_password, create_access_token

router = APIRouter()

# ─── HEALTH (Railway / load balancers) ───────────────────────

@router.get("/api/health")
async def health_check():
    try:
        import websockets  # noqa: F401
        ws_ready = True
    except ImportError:
        ws_ready = False
    return {"status": "ok", "service": "facevault-api", "websockets": ws_ready}

# ─── AUTHENTICATION ──────────────────────────────────────────

@router.post("/api/auth/login")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=60*24*7)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    log_audit(db, user, "LOGIN", "User logged into system", request)
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "username": user.username, "role": user.role}}

@router.get("/api/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_admin)):
    return {"id": current_user.id, "username": current_user.username, "role": current_user.role}


# ─── Engine singletons (initialized in main.py lifespan) ───
_face_engine = None
_liveness_engine = None
_anonymizer_engine = None
_analysis_engine = None

def set_engines(face, liveness, anonymizer, analysis):
    global _face_engine, _liveness_engine, _anonymizer_engine, _analysis_engine
    _face_engine = face
    _liveness_engine = liveness
    _anonymizer_engine = anonymizer
    _analysis_engine = analysis


# ─── Utility ─────────────────────────────────────────────────

def decode_base64_image(b64_str: str):
    img_data = base64.b64decode(b64_str)
    nparr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


# ─── PEOPLE / ENROLLMENT ────────────────────────────────────

@router.get("/api/people")
def list_people(db: Session = Depends(get_db)):
    people = db.query(Person).order_by(Person.name).all()
    return [
        {
            "id": p.id, "name": p.name, "label_id": p.label_id,
            "image_count": p.image_count, "thumbnail": p.thumbnail,
            "recognition_count": p.recognition_count,
            "last_seen": p.last_seen.isoformat() if p.last_seen else None,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in people
    ]

@router.post("/api/people")
async def enroll_person(
    name: str = Form(...),
    images: list[UploadFile] = File(default=[]),
    snapshots: str = Form(default="[]"),
    db: Session = Depends(get_db)
):
    if not name or not name.strip():
        raise HTTPException(400, "Name is required")
    name = name.strip()

    existing = db.query(Person).filter(Person.name == name).first()
    if existing:
        raise HTTPException(400, f"'{name}' already exists")

    frames = []
    # Process uploaded files
    for img_file in images:
        data = await img_file.read()
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is not None:
            frames.append(frame)

    # Process base64 snapshots from webcam
    try:
        snap_list = json.loads(snapshots)
        for b64 in snap_list:
            if b64:
                clean = b64.split(",")[-1] if "," in b64 else b64
                frame = decode_base64_image(clean)
                if frame is not None:
                    frames.append(frame)
    except Exception:
        pass

    if not frames:
        raise HTTPException(400, "No valid images provided")

    result = _face_engine.enroll_person(name, frames)

    if not result["success"]:
        raise HTTPException(400, result.get("error", "Enrollment failed"))

    person = Person(
        name=name,
        label_id=result["label_id"],
        image_count=result["image_count"],
        thumbnail=result.get("thumbnail")
    )
    db.add(person)
    db.commit()
    db.refresh(person)

    return {"success": True, "person": {"id": person.id, "name": person.name, "image_count": person.image_count}}

@router.post("/api/people/{person_id}/photos")
async def add_person_photos(
    person_id: int, 
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Incremental enrollment - add photos to an existing person."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(404, "Person not found")

    frames = []
    for img_file in images:
        data = await img_file.read()
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is not None:
            frames.append(frame)

    if not frames:
        raise HTTPException(400, "No valid images provided")

    # Use the specific add_photos method for incremental enrollment
    result = _face_engine.add_photos(person.name, frames)

    if not result["success"]:
        raise HTTPException(400, result.get("error", "Incremental enrollment failed"))

    # Update count in DB
    person.image_count = result["total_features"]
    db.commit()
    db.refresh(person)

    return {"success": True, "person": {"id": person.id, "name": person.name, "image_count": person.image_count}}


@router.delete("/api/people/{person_id}")
def remove_person(request: Request, person_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_super_admin)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(404, "Person not found")
    
    name = person.name
    _face_engine.remove_person(name)
    db.delete(person)
    db.commit()
    
    log_audit(db, current_user, "DELETE_PERSON", f"Removed personnel: {name}", request)
    return {"success": True}

@router.post("/api/people/{person_id}/photos")
async def add_person_photos(
    person_id: int,
    images: list[UploadFile] = File(default=[]),
    snapshots: str = Form(default="[]"),
    db: Session = Depends(get_db)
):
    """Add more photos to an existing enrolled person for better recognition."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(404, "Person not found")

    frames = []
    for img_file in images:
        data = await img_file.read()
        nparr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is not None:
            frames.append(frame)

    try:
        snap_list = json.loads(snapshots)
        for b64 in snap_list:
            if b64:
                clean = b64.split(",")[-1] if "," in b64 else b64
                frame = decode_base64_image(clean)
                if frame is not None:
                    frames.append(frame)
    except Exception:
        pass

    if not frames:
        raise HTTPException(400, "No valid images provided")

    result = _face_engine.add_photos(person.name, frames)

    if not result["success"]:
        raise HTTPException(400, result.get("error", "Failed to add photos"))

    person.image_count = person.image_count + result["new_images"]
    db.commit()

    return {
        "success": True,
        "person": {"id": person.id, "name": person.name, "image_count": person.image_count},
        "new_features": result["new_features"],
        "total_features": result["total_features"]
    }


# ─── DETECTION WEBSOCKET ────────────────────────────────────

@router.websocket("/ws/detect")
async def ws_detect(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            frame = _face_engine.decode_frame(data)
            if frame is None:
                continue
            faces = _face_engine.detect_faces(frame, detect_eyes=True)
            await websocket.send_json({"faces": faces, "count": len(faces)})
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# ─── RECOGNITION WEBSOCKET ──────────────────────────────────

@router.websocket("/ws/recognize")
async def ws_recognize(websocket: WebSocket):
    await websocket.accept()
    db = SessionLocal()
    frame_count = 0
    unknown_streak = 0
    last_threat_time = datetime.min
    checked_in_today = set()  # Track who's already checked in today

    try:
        # Load existing check-ins for today
        today = date.today()
        existing = db.query(AttendanceLog).filter(AttendanceLog.date == today).all()
        for log in existing:
            checked_in_today.add(log.person_name)

        print("[WS] Client connected to /ws/recognize")
        while True:
            data = await websocket.receive_bytes()
            frame = _face_engine.decode_frame(data)
            if frame is None:
                continue

            results = _face_engine.recognize_faces(frame)
            frame_count += 1
            
            if frame_count % 30 == 0:
                print(f"[WS] Frame decoded: {frame.shape}, faces found: {len(results)}")

            # Update DB every 30 frames for known faces
            if frame_count % 30 == 0:
                for r in results:
                    if r["name"] != "Unknown":
                        person = db.query(Person).filter(Person.name == r["name"]).first()
                        if person:
                            person.recognition_count += 1
                            person.last_seen = datetime.now()
                db.commit()

            # Auto-attendance: create check-in for recognized people (once per day)
            for r in results:
                if r["name"] != "Unknown" and r["confidence"] > 50 and r["name"] not in checked_in_today:
                    person = db.query(Person).filter(Person.name == r["name"]).first()
                    if person:
                        log = AttendanceLog(
                            person_id=person.id,
                            person_name=r["name"],
                            check_in=datetime.now(),
                            date=date.today(),
                            status="present",
                            confidence=r["confidence"]
                        )
                        db.add(log)
                        db.commit()
                        checked_in_today.add(r["name"])
                        print(f"[WS] Auto check-in: {r['name']} (confidence: {r['confidence']}%)")

            # Auto-log unknown faces as threat events (throttled)
            has_unknown = any(r["name"] == "Unknown" for r in results)
            if has_unknown:
                unknown_streak += 1
            else:
                unknown_streak = 0

            now = datetime.now()
            if unknown_streak >= 60 and (now - last_threat_time).total_seconds() > 30:
                threat = ThreatEvent(
                    severity="warning",
                    title="Unknown Face Detected",
                    description="Unidentified person detected in camera feed for an extended period.",
                    zone="Live Monitor",
                    status="pending"
                )
                db.add(threat)
                db.commit()
                last_threat_time = now
                unknown_streak = 0
                print("[WS] Threat event created: Unknown face detected")

            if frame_count % 30 == 0:
                print(f"[WS] Processed {frame_count} frames, last results: {len(results)} faces")

            await websocket.send_json({"faces": results, "count": len(results)})
    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Error: {e}")
    finally:
        db.close()


# ─── ATTENDANCE ──────────────────────────────────────────────

@router.websocket("/ws/attendance")
async def ws_attendance(websocket: WebSocket):
    await websocket.accept()
    db = SessionLocal()
    checked_in_today = set()
    today = date.today()

    try:
        # Load existing check-ins for today
        existing = db.query(AttendanceLog).filter(AttendanceLog.date == today).all()
        for log in existing:
            if not log.check_out:
                checked_in_today.add(log.person_name)

        while True:
            data = await websocket.receive_bytes()
            frame = _face_engine.decode_frame(data)
            if frame is None:
                continue

            results = _face_engine.recognize_faces(frame)
            events = []

            for r in results:
                if r["name"] != "Unknown" and r["confidence"] > 50:
                    name = r["name"]
                    if name not in checked_in_today:
                        # Auto check-in
                        person = db.query(Person).filter(Person.name == name).first()
                        log = AttendanceLog(
                            person_id=person.id if person else 0,
                            person_name=name,
                            check_in=datetime.now(),
                            date=today,
                            status="present",
                            confidence=r["confidence"]
                        )
                        db.add(log)
                        db.commit()
                        checked_in_today.add(name)
                        events.append({"type": "check_in", "name": name, "time": datetime.now().strftime("%H:%M:%S")})

            await websocket.send_json({"faces": results, "count": len(results), "events": events, "checked_in": list(checked_in_today)})
    except WebSocketDisconnect:
        pass
    finally:
        db.close()


# ─── ATTENDANCE (REST) ───────────────────────────────────────

@router.get("/api/attendance")
def get_attendance(date_str: Optional[str] = None, db: Session = Depends(get_db)):
    target = date.fromisoformat(date_str) if date_str else date.today()
    logs = db.query(AttendanceLog).filter(AttendanceLog.date == target).order_by(AttendanceLog.check_in).all()
    return [
        {
            "id": l.id, "person_name": l.person_name,
            "check_in": l.check_in.strftime("%H:%M:%S"),
            "check_out": l.check_out.strftime("%H:%M:%S") if l.check_out else None,
            "status": l.status, "confidence": l.confidence
        }
        for l in logs
    ]

@router.post("/api/attendance/checkout/{person_name}")
def checkout_person(person_name: str, db: Session = Depends(get_db)):
    today = date.today()
    log = db.query(AttendanceLog).filter(
        AttendanceLog.person_name == person_name,
        AttendanceLog.date == today,
        AttendanceLog.check_out == None
    ).first()
    if not log:
        raise HTTPException(404, "No active check-in found")
    log.check_out = datetime.now()
    db.commit()
    return {"success": True, "check_out": log.check_out.strftime("%H:%M:%S")}


# ─── ANALYTICS ───────────────────────────────────────────────

@router.get("/api/analytics")
def get_analytics(days: int = 7, db: Session = Depends(get_db)):
    total_people = db.query(Person).count()
    total_recognitions = db.query(Person).with_entities(
        Person.recognition_count
    ).all()
    total_rec = sum(r[0] for r in total_recognitions)

    today = date.today()
    today_logs = db.query(AttendanceLog).filter(AttendanceLog.date == today).count()

    # Active (pending) threats count
    active_alerts = db.query(ThreatEvent).filter(ThreatEvent.status == "pending").count()

    # Daily data — real attendance + threat counts per day
    daily = []
    for i in range(days):
        d = today - timedelta(days=i)
        att_count = db.query(AttendanceLog).filter(AttendanceLog.date == d).count()
        threat_count = db.query(ThreatEvent).filter(
            ThreatEvent.timestamp >= datetime.combine(d, datetime.min.time()),
            ThreatEvent.timestamp < datetime.combine(d + timedelta(days=1), datetime.min.time())
        ).count()
        daily.append({"date": d.isoformat(), "count": att_count, "threats": threat_count})
    daily.reverse()

    # Per-person recognition stats (for pie chart)
    people_stats = []
    people = db.query(Person).all()
    for p in people:
        if p.recognition_count > 0:
            people_stats.append({"name": p.name, "value": p.recognition_count})
    # Add "Unknown" count (total recognitions minus known)
    known_rec = sum(ps["value"] for ps in people_stats)
    unknown_count = db.query(ThreatEvent).filter(ThreatEvent.severity == "warning").count()
    if unknown_count > 0:
        people_stats.append({"name": "Unknown Faces", "value": unknown_count})

    # Hourly activity for today from real AnalyticsSnapshot
    hourly = []
    snapshots = db.query(AnalyticsSnapshot).filter(AnalyticsSnapshot.date == today).order_by(AnalyticsSnapshot.hour).all()
    if snapshots:
        for s in snapshots:
            hourly.append({"time": f"{s.hour:02d}:00", "traffic": s.face_count})
    else:
        # If no snapshots yet, generate from today's attendance log timestamps
        for h in range(24):
            start_t = datetime.combine(today, datetime.min.time()) + timedelta(hours=h)
            end_t = start_t + timedelta(hours=1)
            count = db.query(AttendanceLog).filter(
                AttendanceLog.date == today,
                AttendanceLog.check_in >= start_t,
                AttendanceLog.check_in < end_t
            ).count()
            if count > 0 or h <= datetime.now().hour:
                hourly.append({"time": f"{h:02d}:00", "traffic": count})

    return {
        "total_people": total_people,
        "total_recognitions": total_rec,
        "today_attendance": today_logs,
        "active_alerts": active_alerts,
        "daily_data": daily,
        "people_stats": people_stats,
        "hourly_data": hourly
    }


# ─── THREAT EVENTS ───────────────────────────────────────────

@router.get("/api/threats")
def get_threats(status: str = None, severity: str = None, db: Session = Depends(get_db)):
    query = db.query(ThreatEvent).order_by(ThreatEvent.timestamp.desc())
    if status and status != "all":
        query = query.filter(ThreatEvent.status == status)
    if severity and severity != "all":
        query = query.filter(ThreatEvent.severity == severity)
    threats = query.limit(100).all()
    return [{
        "id": t.id,
        "title": t.title,
        "desc": t.description,
        "zone": t.zone or "System",
        "time": t.timestamp.strftime("%I:%M %p") if t.timestamp else "",
        "timestamp": t.timestamp.isoformat() if t.timestamp else "",
        "severity": t.severity,
        "status": t.status
    } for t in threats]


@router.put("/api/threats/{threat_id}/status")
def update_threat_status(threat_id: int, status: str, db: Session = Depends(get_db)):
    threat = db.query(ThreatEvent).filter(ThreatEvent.id == threat_id).first()
    if not threat:
        raise HTTPException(404, "Threat not found")
    if status not in ["pending", "acknowledged", "resolved"]:
        raise HTTPException(400, "Invalid status")
    threat.status = status
    db.commit()
    return {"success": True, "id": threat_id, "status": status}


# ─── SYSTEM INFO ─────────────────────────────────────────────

@router.get("/api/system/info")
def get_system_info(db: Session = Depends(get_db)):
    import os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "facevault.db")
    db_size = 0
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path)

    # Dataset folder size
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "facevault_dataset")
    dataset_size = 0
    if os.path.exists(dataset_path):
        for root, dirs, files in os.walk(dataset_path):
            for f in files:
                dataset_size += os.path.getsize(os.path.join(root, f))

    total_bytes = db_size + dataset_size

    return {
        "db_size_bytes": db_size,
        "dataset_size_bytes": dataset_size,
        "total_size_bytes": total_bytes,
        "total_size_display": f"{total_bytes / (1024*1024):.1f} MB" if total_bytes < 1024*1024*1024 else f"{total_bytes / (1024*1024*1024):.2f} GB",
        "enrolled_people": len(_face_engine.name_to_label),
        "total_features": sum(len(v) for v in _face_engine.features.values()),
        "recognition_ready": _face_engine.is_trained,
        "liveness_ready": _liveness_engine.available if _liveness_engine else False,
        "analysis_ready": _analysis_engine.available if _analysis_engine else False,
        "detection_threshold": 0.5,
        "recognition_threshold": 0.28
    }


# ─── ACTIVITY LOG (real events) ──────────────────────────────

@router.get("/api/activity")
def get_activity(limit: int = 20, db: Session = Depends(get_db)):
    """Returns the most recent real events from attendance and threat logs."""
    events = []

    # Recent attendance events
    logs = db.query(AttendanceLog).order_by(AttendanceLog.check_in.desc()).limit(limit).all()
    for log in logs:
        events.append({
            "timestamp": log.check_in.strftime("%H:%M:%S") if log.check_in else "",
            "datetime": log.check_in.isoformat() if log.check_in else "",
            "type": "Check-in" if not log.check_out else "Check-out",
            "target": log.person_name,
            "zone": "Attendance Zone",
            "status": "verified",
            "confidence": log.confidence
        })

    # Recent threat events
    threats = db.query(ThreatEvent).order_by(ThreatEvent.timestamp.desc()).limit(limit).all()
    for t in threats:
        events.append({
            "timestamp": t.timestamp.strftime("%H:%M:%S") if t.timestamp else "",
            "datetime": t.timestamp.isoformat() if t.timestamp else "",
            "type": t.title,
            "target": "Unknown" if "Unknown" in t.title else "System",
            "zone": t.zone or "System",
            "status": t.status,
            "confidence": 0
        })

    # Sort by datetime descending
    events.sort(key=lambda e: e.get("datetime", ""), reverse=True)
    return events[:limit]


# ─── ANONYMIZER ──────────────────────────────────────────────

@router.post("/api/anonymize")
async def anonymize_image(
    image: UploadFile = File(...),
    mode: str = Form(default="blur"),
    blur_strength: int = Form(default=51)
):
    data = await image.read()
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "Invalid image")

    result = _anonymizer_engine.anonymize_to_base64(frame, mode, blur_strength)
    return result


# ─── LIVENESS ────────────────────────────────────────────────

@router.post("/api/liveness/start")
def start_liveness():
    session_id = str(uuid.uuid4())
    challenge = _liveness_engine.create_challenge(session_id)
    return {"session_id": session_id, **challenge}

@router.websocket("/ws/liveness/{session_id}")
async def ws_liveness(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            frame = _face_engine.decode_frame(data)
            if frame is None:
                continue
            result = _liveness_engine.process_frame(session_id, frame)
            await websocket.send_json(result)
            if result.get("passed") or result.get("status") == "failed":
                break
    except WebSocketDisconnect:
        pass
    finally:
        _liveness_engine.cleanup_session(session_id)


# ─── COMPARE ────────────────────────────────────────────────

@router.post("/api/compare")
async def compare_faces(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...)
):
    d1 = await image1.read()
    d2 = await image2.read()
    arr1 = np.frombuffer(d1, np.uint8)
    arr2 = np.frombuffer(d2, np.uint8)
    img1 = cv2.imdecode(arr1, cv2.IMREAD_COLOR)
    img2 = cv2.imdecode(arr2, cv2.IMREAD_COLOR)
    if img1 is None or img2 is None:
        raise HTTPException(400, "Invalid images")
    result = _analysis_engine.compare_faces(img1, img2)
    return result


# ─── IMAGE DETECTION ─────────────────────────────────────────

@router.post("/api/detect/image")
async def detect_in_image(image: UploadFile = File(...)):
    data = await image.read()
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "Invalid image")
    faces = _face_engine.detect_faces(frame, detect_eyes=True)
    return {"faces": faces, "count": len(faces)}

@router.get("/api/status")
def get_status():
    return {
        "recognition": _face_engine.is_trained,
        "people_count": len(_face_engine.name_to_label),
        "liveness": _liveness_engine.available if _liveness_engine else False,
        "analysis": _analysis_engine.available if _analysis_engine else False,
        "people": _face_engine.get_people_list()
    }


# ─── USER MANAGEMENT (SUPER ADMIN) ──────────────────────────

from database.models import UserResponse, UserCreate, AuditLogResponse
from backend.auth import get_password_hash

@router.get("/api/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_super_admin)):
    return db.query(User).all()

@router.post("/api/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_super_admin),
    request: Request = None
):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(400, "Username already exists")
    
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_audit(db, current_user, "CREATE_USER", f"Created user {new_user.username} with role {new_user.role}", request)
    return new_user

@router.put("/api/users/{user_id}/status")
def toggle_user_status(
    user_id: int, 
    active: bool,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_super_admin),
    request: Request = None
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == current_user.id:
        raise HTTPException(400, "Cannot change your own status")
    
    user.is_active = active
    db.commit()
    
    status_str = "ENABLED" if active else "DISABLED"
    log_audit(db, current_user, "TOGGLE_USER_STATUS", f"{status_str} user {user.username}", request)
    return {"success": True}

@router.delete("/api/users/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_super_admin),
    request: Request = None
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.role == "super_admin":
        raise HTTPException(400, "Cannot delete super admin")
    
    username = user.username
    db.delete(user)
    db.commit()
    
    log_audit(db, current_user, "DELETE_USER", f"Deleted user {username}", request)
    return {"success": True}


# ─── AUDIT LOGS (SUPER ADMIN) ───────────────────────────────

@router.get("/api/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_super_admin)
):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

@router.get("/api/attendance/export")
def export_attendance_excel(
    date_str: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")
    
    logs = db.query(AttendanceLog).filter(AttendanceLog.date == target_date).all()
    
    if not logs:
        # Create empty DataFrame with headers if no logs
        df = pd.DataFrame(columns=['Personnel', 'Check-In', 'Check-Out', 'Confidence', 'Status'])
    else:
        data = []
        for log in logs:
            data.append({
                'Personnel': log.person_name,
                'Check-In': log.check_in.strftime("%H:%M:%S") if log.check_in else "",
                'Check-Out': log.check_out.strftime("%H:%M:%S") if log.check_out else "Active",
                'Confidence': f"{log.confidence:.1f}%",
                'Status': log.status.upper()
            })
        df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance')
        workbook = writer.book
        worksheet = writer.sheets['Attendance']
        
        # Add some formatting
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
            
    output.seek(0)
    
    filename = f"FaceVault_Attendance_{date_str}.xlsx"
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers=headers
    )
