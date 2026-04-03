import base64
import hashlib
import json
import os
from datetime import datetime

from cryptography.fernet import Fernet
from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Keep encryption key stable across restarts. Falling back to a deterministic
# key derived from SECRET_KEY avoids unreadable historical data when FERNET_KEY
# is not explicitly configured.
def _resolve_fernet_key() -> str:
    key = os.getenv("FERNET_KEY")
    if key:
        return key
    secret = os.getenv("SECRET_KEY", "super-secret-soc-key-change-in-prod")
    digest = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode()


FERNET_KEY = _resolve_fernet_key()
fernet = Fernet(FERNET_KEY.encode())

DATABASE_URL = "sqlite:///./soc_scans.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 15},
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    role = Column(String, default="operator")
    google_id = Column(String, unique=True, index=True, nullable=True)
    totp_secret = Column(String, nullable=True)
    is_totp_enabled = Column(Boolean, default=False, nullable=False)


class ScanReport(Base):
    __tablename__ = "scan_reports"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, index=True)
    operator = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    open_ports_count = Column(Integer)
    risk_level = Column(String)
    report_json = Column(Text)


class AutopilotScan(Base):
    __tablename__ = "autopilot_scans"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String)
    operator = Column(String)
    interval_hours = Column(Integer, default=24)
    created_at = Column(DateTime, default=datetime.utcnow)


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    operator = Column(String, unique=True, index=True)
    subscription_json = Column(Text)


def _ensure_user_columns():
    with engine.begin() as conn:
        columns = {
            row[1] for row in conn.execute(text("PRAGMA table_info(users)"))
        }

        if "google_id" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users(google_id)"))

        if "totp_secret" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN totp_secret VARCHAR"))

        if "is_totp_enabled" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_totp_enabled BOOLEAN DEFAULT 0"))


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_user_columns()

    db = SessionLocal()
    try:
        if not db.query(User).first():
            db.add(User(username="admin", hashed_password=pwd_context.hash("admin123"), role="admin"))
            db.add(User(username="operator", hashed_password=pwd_context.hash("operator123"), role="operator"))
            db.commit()
    finally:
        db.close()


def authenticate_user(db, username, password):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.hashed_password:
        return None
    if not pwd_context.verify(password, user.hashed_password):
        return None
    return user


def get_user_by_username(db, username):
    return db.query(User).filter(User.username == username).first()


def get_user_by_google_id(db, google_id):
    return db.query(User).filter(User.google_id == google_id).first()


def _build_unique_username(db, preferred: str) -> str:
    safe = "".join(ch for ch in preferred if ch.isalnum() or ch in "._-").strip("._-")
    base = safe or "google_user"

    username = base
    i = 1
    while db.query(User).filter(User.username == username).first():
        i += 1
        username = f"{base}{i}"
    return username


def create_or_update_google_user(db, google_id: str, email: str, name: str | None = None):
    user = get_user_by_google_id(db, google_id)
    if user:
        if email and user.username != email:
            # Preserve human-friendly usernames; do not overwrite.
            pass
        return user

    preferred = email or name or "google_user"
    username = _build_unique_username(db, preferred)

    user = User(
        username=username,
        hashed_password=None,
        role="operator",
        google_id=google_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_user(db, username, password, role="operator"):
    if db.query(User).filter(User.username == username).first():
        return False

    db.add(User(username=username, hashed_password=pwd_context.hash(password), role=role))
    db.commit()
    return True


def save_report(target: str, operator: str, report_data: dict, risk_level: str):
    db = SessionLocal()
    try:
        report = ScanReport(
            target=target,
            operator=operator,
            open_ports_count=len(report_data.get("open_ports", [])),
            risk_level=risk_level,
            report_json=fernet.encrypt(json.dumps(report_data).encode()).decode(),
        )
        db.add(report)
        db.commit()
    finally:
        db.close()


def get_history(role: str = "admin", username: str = ""):
    db = SessionLocal()
    try:
        query = db.query(ScanReport)
        if role != "admin":
            query = query.filter(ScanReport.operator == username)

        reports = query.order_by(ScanReport.timestamp.desc()).all()
        reports_list = []
        for r in reports:
            try:
                decrypted = fernet.decrypt(r.report_json.encode()).decode()
                r_json = json.loads(decrypted)
            except Exception:
                try:
                    r_json = json.loads(r.report_json)
                except Exception:
                    r_json = {}
            reports_list.append(
                {
                    "id": r.id,
                    "target": r.target,
                    "operator": r.operator,
                    "timestamp": r.timestamp.isoformat(),
                    "open_ports_count": r.open_ports_count,
                    "risk_level": r.risk_level,
                    "report_json": r_json,
                }
            )
        return reports_list
    finally:
        db.close()


def get_analytics(role: str = "admin", username: str = ""):
    db = SessionLocal()
    try:
        query = db.query(ScanReport)
        if role != "admin":
            query = query.filter(ScanReport.operator == username)

        reports = query.all()

        total_scans = len(reports)
        high_risk = sum(1 for r in reports if r.risk_level == "High")
        medium_risk = sum(1 for r in reports if r.risk_level == "Medium")
        low_risk = sum(1 for r in reports if r.risk_level == "Low")

        target_counts = {}
        date_counts = {}
        for r in reports:
            target_counts[r.target] = target_counts.get(r.target, 0) + 1
            date_str = r.timestamp.strftime("%Y-%m-%d")
            date_counts[date_str] = date_counts.get(date_str, 0) + 1

        top_targets = [
            {"name": k, "value": v}
            for k, v in sorted(target_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        ]
        timeline = [{"date": k, "scans": v} for k, v in sorted(date_counts.items())]

        return {
            "total_scans": total_scans,
            "risk_distribution": [
                {"name": "High", "value": high_risk},
                {"name": "Medium", "value": medium_risk},
                {"name": "Low", "value": low_risk},
            ],
            "top_targets": top_targets,
            "timeline": timeline,
        }
    finally:
        db.close()


def create_scheduled_scan(target: str, interval: int, operator: str):
    db = SessionLocal()
    try:
        scan = AutopilotScan(target=target, interval_hours=interval, operator=operator)
        db.add(scan)
        db.commit()
    finally:
        db.close()


def get_scheduled_scans(role: str = "admin", username: str = ""):
    db = SessionLocal()
    try:
        query = db.query(AutopilotScan)
        if role != "admin":
            query = query.filter(AutopilotScan.operator == username)
        return [
            {"id": s.id, "target": s.target, "interval": s.interval_hours, "operator": s.operator}
            for s in query.all()
        ]
    finally:
        db.close()


def delete_scheduled_scan(scan_id: int, role: str = "operator", username: str = ""):
    db = SessionLocal()
    try:
        query = db.query(AutopilotScan).filter(AutopilotScan.id == scan_id)
        if role != "admin":
            query = query.filter(AutopilotScan.operator == username)
        scan = query.first()
        if scan:
            db.delete(scan)
            db.commit()
            return True
        return False
    finally:
        db.close()


def save_push_subscription(operator: str, subscription_data: dict):
    db = SessionLocal()
    try:
        sub = db.query(PushSubscription).filter(PushSubscription.operator == operator).first()
        if sub:
            sub.subscription_json = json.dumps(subscription_data)
        else:
            sub = PushSubscription(operator=operator, subscription_json=json.dumps(subscription_data))
            db.add(sub)
        db.commit()
    finally:
        db.close()


def get_push_subscriptions():
    db = SessionLocal()
    try:
        return [
            {"operator": s.operator, "subscription": json.loads(s.subscription_json)}
            for s in db.query(PushSubscription).all()
        ]
    finally:
        db.close()


def healthcheck() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
