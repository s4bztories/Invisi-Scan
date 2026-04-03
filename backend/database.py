import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, event
from sqlalchemy.orm import declarative_base, sessionmaker
from passlib.context import CryptContext
import os
from cryptography.fernet import Fernet

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
FERNET_KEY = os.getenv("FERNET_KEY", Fernet.generate_key().decode())
fernet = Fernet(FERNET_KEY.encode())


DATABASE_URL = "sqlite:///./soc_scans.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 15})

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
    hashed_password = Column(String)
    role = Column(String)

class ScanReport(Base):
    __tablename__ = "scan_reports"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, index=True)
    operator = Column(String)  # The user who ran the scan (e.g. admin or guest)
    timestamp = Column(DateTime, default=datetime.utcnow)
    open_ports_count = Column(Integer)
    risk_level = Column(String) # High, Medium, Low, Secure
    report_json = Column(Text)  # Storing the full intricate JSON

class AutopilotScan(Base):
    __tablename__ = "autopilot_scans"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String)
    operator = Column(String)
    interval_hours = Column(Integer, default=24)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Seed default users
    if not db.query(User).first():
        admin = User(username="admin", hashed_password=pwd_context.hash("admin123"), role="admin")
        opr = User(username="operator", hashed_password=pwd_context.hash("operator123"), role="operator")
        db.add(admin)
        db.add(opr)
        db.commit()
    db.close()

def authenticate_user(db, username, password):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def create_user(db, username, password, role="operator"):
    if db.query(User).filter(User.username == username).first():
        return False
    user = User(username=username, hashed_password=pwd_context.hash(password), role=role)
    db.add(user)
    db.commit()
    return True

def save_report(target: str, operator: str, report_data: dict, risk_level: str):
    db = SessionLocal()
    try:
        report = ScanReport(
            target=target,
            operator=operator,
            open_ports_count=len(report_data.get('open_ports', [])),
            risk_level=risk_level,
            report_json=fernet.encrypt(json.dumps(report_data).encode()).decode()
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
                    r_json = json.loads(r.report_json) # Fallback if unencrypted
                except:
                    r_json = {}
            reports_list.append({
                "id": r.id,
                "target": r.target,
                "operator": r.operator,
                "timestamp": r.timestamp.isoformat(),
                "open_ports_count": r.open_ports_count,
                "risk_level": r.risk_level,
                "report_json": r_json
            })
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
            
        top_targets = [{"name": k, "value": v} for k, v in sorted(target_counts.items(), key=lambda item: item[1], reverse=True)[:5]]
        timeline = [{"date": k, "scans": v} for k, v in sorted(date_counts.items())]

        return {
            "total_scans": total_scans,
            "risk_distribution": [
                {"name": "High", "value": high_risk},
                {"name": "Medium", "value": medium_risk},
                {"name": "Low", "value": low_risk}
            ],
            "top_targets": top_targets,
            "timeline": timeline
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
        return [{"id": s.id, "target": s.target, "interval": s.interval_hours, "operator": s.operator} for s in query.all()]
    finally:
        db.close()

def delete_scheduled_scan(scan_id: int):
    db = SessionLocal()
    try:
        scan = db.query(AutopilotScan).filter(AutopilotScan.id == scan_id).first()
        if scan:
            db.delete(scan)
            db.commit()
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
            
        top_targets = [{"name": k, "value": v} for k, v in sorted(target_counts.items(), key=lambda item: item[1], reverse=True)[:5]]
        timeline = [{"date": k, "scans": v} for k, v in sorted(date_counts.items())]

        return {
            "total_scans": total_scans,
            "risk_distribution": [
                {"name": "High", "value": high_risk},
                {"name": "Medium", "value": medium_risk},
                {"name": "Low", "value": low_risk}
            ],
            "top_targets": top_targets,
            "timeline": timeline
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
        return [{"id": s.id, "target": s.target, "interval": s.interval_hours, "operator": s.operator} for s in query.all()]
    finally:
        db.close()

def delete_scheduled_scan(scan_id: int):
    db = SessionLocal()
    try:
        scan = db.query(AutopilotScan).filter(AutopilotScan.id == scan_id).first()
        if scan:
            db.delete(scan)
            db.commit()
    finally:
        db.close()

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    operator = Column(String, unique=True, index=True)
    subscription_json = Column(Text)

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
        return [{"operator": s.operator, "subscription": json.loads(s.subscription_json)} for s in db.query(PushSubscription).all()]
    finally:
        db.close()
