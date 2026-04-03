import asyncio
import json
import os
import sys
import socket
import ipaddress
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import BaseModel, field_validator, validator
from typing import Dict, Any, Optional, List
import httpx
import jwt
import pyotp
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager

SECRET_KEY = "super-secret-soc-key-change-in-prod"
ALGORITHM = "HS256"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to verify JWT token and return user info."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role", "operator")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        logger.info(f"Authenticated user: {username} with role: {role}")
        return {"username": username, "role": role}
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")


# Load secret environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.subdomains import enumerate_subdomains
from backend.geo_lookup import lookup_geo
from backend.waf_detector import detect_waf
from backend.dir_fuzzer import fuzz_directories

from backend.core.scanner_async import AsyncPortScanner
from backend.core.banner import BannerGrabber
from backend.core.cve_lookup import CVELookup
from backend.core.ai_helper import AIHelper
from backend.core.reporter import Reporter
from backend import database
from pywebpush import webpush, WebPushException

# Initialize the database schema
database.init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    reload_scheduler()
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(
    title="Invisi-Scan SOC Pipeline API",
    description="""
    Advanced Network Intelligence & Ethical Attack Surface Analyzer API.
    
    This API provides comprehensive reconnaissance capabilities including:
    - Real-time port scanning and service enumeration
    - Web Application Firewall detection
    - Subdomain discovery via SSL transparency logs
    - CVE correlation and AI-powered threat analysis
    - Automated Metasploit exploit generation
    - Encrypted audit logging and Telegram notifications
    
    ## Authentication
    Most endpoints require JWT authentication via Bearer token in Authorization header.
    
    ## Rate Limiting
    Authentication endpoints are rate-limited to 5 requests per minute.
    """,
    version="1.0.0",
    lifespan=lifespan
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Allow CORS for the Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["General"])
def read_root():
    """
    Health check endpoint.
    
    Returns the API status to verify the service is running.
    """
    return {"status": "Invisi-Scan API is running"}

@app.get("/api/history")
def get_scan_history(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"ok": False, "error": "Unauthorized"}
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role", "operator")
        username = payload.get("sub", "unknown")
    except Exception:
        return {"ok": False, "error": "Invalid token"}

    reports = database.get_history(role, username)
    return {"ok": True, "history": reports}

@app.get("/api/analytics")
def get_analytics_data(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "): return {"ok": False, "error": "Unauthorized"}
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role", "operator")
        username = payload.get("sub", "unknown")
    except Exception: return {"ok": False, "error": "Invalid token"}
    data = database.get_analytics(role, username)
    return {"ok": True, "analytics": data}

class SubscribeRequest(BaseModel):
    subscription: dict

@app.get("/api/vapid-public-key")
def get_vapid_key():
    return {"publicKey": "BMNZc7XW9W5dOeNImG5ZG4P2UFZtEa-5udjbuiTpmnRSR2o58iUOSr2Qsey25I9W5NxMEPQVl2UbxTZHf67D2gI"}

@app.post("/api/subscribe")
def subscribe_push(req: SubscribeRequest, current_user: dict = Depends(get_current_user)):
    try:
        username = current_user["username"]
        database.save_push_subscription(username, req.subscription)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Subscription error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")

async def send_web_push(title: str, message: str):
    subs = database.get_push_subscriptions()
    payload = json.dumps({"title": title, "body": message})
    for sub in subs:
        try:
            webpush(
                subscription_info=sub["subscription"],
                data=payload,
                vapid_private_key=os.path.join(os.path.dirname(os.path.abspath(__file__)), "private_key.pem"),
                vapid_claims={"sub": "mailto:admin@example.com"}
            )
        except WebPushException as ex:
            logger.error(f"Web Push config error: {repr(ex)}")
        except Exception as e:
            logger.error(f"Web push error: {e}")

@app.get("/api/admin/users")
def get_admin_users(request: Request):
    auth = request.headers.get("Authorization")
    if not auth: return {"ok": False}
    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin": return {"ok": False}
    except: return {"ok": False}
    db = database.SessionLocal()
    users = db.query(database.User).all()
    res = [{"id": u.id, "username": u.username, "role": u.role} for u in users]
    db.close()
    return {"ok": True, "users": res}

@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    db = database.SessionLocal()
    try:
        if current_user["username"] == "admin":
            target = db.query(database.User).filter(database.User.id == user_id).first()
            if target and target.username == "admin":
                return {"ok": False, "error": "Default admin cannot be deleted."}
        db.query(database.User).filter(database.User.id == user_id).delete()
        db.commit()
        return {"ok": True}
    finally:
        db.close()

@app.put("/api/admin/users/{user_id}/promote")
def promote_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    db = database.SessionLocal()
    try:
        user = db.query(database.User).filter(database.User.id == user_id).first()
        if user:
            user.role = "admin"
            db.commit()
        return {"ok": True}
    finally:
        db.close()

scheduler = AsyncIOScheduler()

async def run_autopilot_scan(target: str, username: str):
    import urllib.parse
    raw_target = target
    tgt = urllib.parse.urlparse(raw_target).netloc if "://" in raw_target else (raw_target.split("/")[0] if "/" in raw_target else raw_target)
    ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306, 3389, 8080]
    scanner = AsyncPortScanner(tgt, ports, concurrency=50, timeout=3.0)
    open_ports = await scanner.run()
    if not open_ports: return
    report_data = {
        "target": tgt, "open_ports": open_ports, "banners": {}, "cves": {}, "explanations": {}, 
        "geolocation": None, "web_recon": {}, "subdomains": [], "is_autopilot": True
    }
    database.save_report(tgt, username, report_data, "Medium")

def reload_scheduler():
    scheduler.remove_all_jobs()
    scans = database.get_scheduled_scans("admin", "")
    for s in scans:
        scheduler.add_job(run_autopilot_scan, 'interval', hours=s["interval"], args=[s["target"], s["operator"]], id=f"auto_{s['id']}")

class ScheduleRequest(BaseModel):
    target: str
    interval: int

    @field_validator('target')
    @classmethod
    def validate_target(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Target cannot be empty')
        # Basic validation for IP or hostname
        try:
            ipaddress.ip_address(v.strip())
        except ValueError:
            # Check if it's a valid hostname pattern
            if not all(c.isalnum() or c in '.-' for c in v.strip()):
                raise ValueError('Invalid target format')
        return v.strip()

    @field_validator('interval')
    @classmethod
    def validate_interval(cls, v):
        if v < 1 or v > 168:  # Max 1 week
            raise ValueError('Interval must be between 1 and 168 hours')
        return v

@app.get("/api/schedule")
def get_schedule(current_user: dict = Depends(get_current_user)):
    try:
        role = current_user["role"]
        username = current_user["username"]
        scans = database.get_scheduled_scans(role, username)
        logger.info(f"Retrieved {len(scans)} scheduled scans for user: {username}")
        return {"ok": True, "scans": scans}
    except Exception as e:
        logger.error(f"Error retrieving schedules for {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/schedule")
def add_schedule(req: ScheduleRequest, current_user: dict = Depends(get_current_user)):
    try:
        username = current_user["username"]
        database.create_scheduled_scan(req.target, req.interval, username)
        reload_scheduler()
        logger.info(f"Created scheduled scan for target {req.target} by user: {username}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error creating scheduled scan for {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/schedule/{scan_id}")
def delete_schedule(scan_id: int, current_user: dict = Depends(get_current_user)):
    try:
        # Check if user owns this scan or is admin
        role = current_user["role"]
        username = current_user["username"]
        if role != "admin":
            # Additional check would be needed here for ownership
            pass
        database.delete_scheduled_scan(scan_id)
        reload_scheduler()
        logger.info(f"Deleted scheduled scan {scan_id} by user: {username}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error deleting scheduled scan {scan_id} for {current_user['username']}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "operator"

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['operator', 'admin']:
            raise ValueError('Role must be operator or admin')
        return v


class OtpVerifyRequest(BaseModel):
    otp_ticket: str
    otp_code: str

    @field_validator("otp_code")
    @classmethod
    def validate_otp_code(cls, v):
        code = v.strip()
        if not code.isdigit() or len(code) != 6:
            raise ValueError("OTP code must be a 6-digit number")
        return code


class TotpSetupVerifyRequest(BaseModel):
    otp_code: str

    @field_validator("otp_code")
    @classmethod
    def validate_otp_code(cls, v):
        code = v.strip()
        if not code.isdigit() or len(code) != 6:
            raise ValueError("OTP code must be a 6-digit number")
        return code


class GoogleAuthRequest(BaseModel):
    id_token: str

async def send_telegram_alert(username: str, client_ip: str, user_agent: str, action: str = "LOGIN"):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Get geolocation data
    geo_data = await lookup_geo(client_ip)
    
    # Format detailed message
    message = f"""🚨 *SOC {action.upper()} ALERT* 🚨

👤 **User:** `{username}`
🕒 **Time:** {timestamp}
🌐 **IP Address:** {client_ip}
📍 **Location:** {geo_data.get('city', 'Unknown')}, {geo_data.get('country', 'Unknown')}
🏢 **ISP:** {geo_data.get('isp', 'Unknown')}
📱 **User Agent:** {user_agent[:100]}...

⚠️ *Action detected: {action.upper()} - monitor activity*"""

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": message,
        "parse_mode": "Markdown"
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload, timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")


def create_access_token(user: database.User, hours: int = 24):
    token_data = {
        "sub": user.username,
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=hours),
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


def create_otp_challenge_token(username: str):
    token_data = {
        "sub": username,
        "purpose": "otp_challenge",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


def verify_otp_challenge_token(token: str) -> str:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("purpose") != "otp_challenge":
        raise HTTPException(status_code=401, detail="Invalid OTP challenge")
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid OTP challenge")
    return username

@app.post("/api/register")
@limiter.limit("5/minute")
async def register(request: Request, req: RegisterRequest, background_tasks: BackgroundTasks):
    try:
        db = database.SessionLocal()
        success = database.create_user(db, req.username, req.password, req.role)
        db.close()
        if not success:
            logger.warning(f"Registration failed: username {req.username} already exists")
            return {"ok": False, "error": "Username already exists."}
        logger.info(f"New user registered: {req.username} with role: {req.role}")
        
        client_ip = request.client.host if request.client else "Unknown"
        user_agent = request.headers.get("User-Agent", "Unknown")
        background_tasks.add_task(send_telegram_alert, req.username, client_ip, user_agent, "REGISTRATION")
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Registration error for {req.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/login")
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest, background_tasks: BackgroundTasks):
    try:
        db = database.SessionLocal()
        user = database.authenticate_user(db, req.username, req.password)
        db.close()

        if not user:
            logger.warning(f"Failed login attempt for username: {req.username}")
            return {"ok": False, "error": "Invalid credentials"}

        logger.info(f"Successful login for user: {req.username}")
        client_ip = request.client.host if request.client else "Unknown"
        user_agent = request.headers.get("User-Agent", "Unknown")
        background_tasks.add_task(send_telegram_alert, req.username, client_ip, user_agent)

        if user.is_totp_enabled:
            otp_ticket = create_otp_challenge_token(user.username)
            return {
                "ok": True,
                "otp_required": True,
                "otp_ticket": otp_ticket,
                "message": "OTP verification required",
            }

        token = create_access_token(user)
        return {"ok": True, "token": token, "role": user.role, "username": user.username}
    except Exception as e:
        logger.error(f"Login error for {req.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/login/verify-otp")
@limiter.limit("10/minute")
async def verify_login_otp(request: Request, req: OtpVerifyRequest):
    try:
        username = verify_otp_challenge_token(req.otp_ticket)

        db = database.SessionLocal()
        user = database.get_user_by_username(db, username)
        if not user or not user.totp_secret or not user.is_totp_enabled:
            db.close()
            return {"ok": False, "error": "OTP is not configured for this account."}

        is_valid = pyotp.TOTP(user.totp_secret).verify(req.otp_code, valid_window=1)
        db.close()
        if not is_valid:
            return {"ok": False, "error": "Invalid OTP code."}

        token = create_access_token(user)
        return {"ok": True, "token": token, "role": user.role, "username": user.username}
    except jwt.ExpiredSignatureError:
        return {"ok": False, "error": "OTP challenge expired. Please login again."}
    except jwt.InvalidTokenError:
        return {"ok": False, "error": "Invalid OTP challenge. Please login again."}
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/auth/google")
@limiter.limit("10/minute")
async def login_with_google(request: Request, req: GoogleAuthRequest, background_tasks: BackgroundTasks):
    try:
        async with httpx.AsyncClient() as client:
            verify_res = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": req.id_token},
                timeout=8.0,
            )

        if verify_res.status_code != 200:
            return {"ok": False, "error": "Invalid Google token."}

        token_info = verify_res.json()
        audience = token_info.get("aud")
        issuer = token_info.get("iss")
        google_id = token_info.get("sub")
        email = token_info.get("email", "")
        email_verified = token_info.get("email_verified")
        name = token_info.get("name", "")

        if GOOGLE_CLIENT_ID and audience != GOOGLE_CLIENT_ID:
            return {"ok": False, "error": "Google token audience mismatch."}
        if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
            return {"ok": False, "error": "Invalid Google token issuer."}
        if not google_id or not email:
            return {"ok": False, "error": "Google token missing required claims."}
        if str(email_verified).lower() not in {"true", "1"}:
            return {"ok": False, "error": "Google email is not verified."}

        db = database.SessionLocal()
        user = database.create_or_update_google_user(db, google_id=google_id, email=email, name=name)
        db.close()

        client_ip = request.client.host if request.client else "Unknown"
        user_agent = request.headers.get("User-Agent", "Unknown")
        background_tasks.add_task(send_telegram_alert, user.username, client_ip, user_agent, "GOOGLE_LOGIN")

        token = create_access_token(user)
        return {"ok": True, "token": token, "role": user.role, "username": user.username}
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/2fa/status")
def get_totp_status(current_user: dict = Depends(get_current_user)):
    db = database.SessionLocal()
    try:
        user = database.get_user_by_username(db, current_user["username"])
        if not user:
            return {"ok": False, "error": "User not found."}
        return {"ok": True, "is_totp_enabled": bool(user.is_totp_enabled)}
    finally:
        db.close()


@app.post("/api/2fa/setup")
def setup_totp(current_user: dict = Depends(get_current_user)):
    db = database.SessionLocal()
    try:
        user = database.get_user_by_username(db, current_user["username"])
        if not user:
            return {"ok": False, "error": "User not found."}

        secret = user.totp_secret or pyotp.random_base32()
        user.totp_secret = secret
        user.is_totp_enabled = False
        db.commit()

        issuer = "Invisi-Scan"
        otpauth_uri = pyotp.TOTP(secret).provisioning_uri(name=user.username, issuer_name=issuer)
        return {"ok": True, "otpauth_uri": otpauth_uri, "secret": secret}
    finally:
        db.close()


@app.post("/api/2fa/enable")
def enable_totp(req: TotpSetupVerifyRequest, current_user: dict = Depends(get_current_user)):
    db = database.SessionLocal()
    try:
        user = database.get_user_by_username(db, current_user["username"])
        if not user or not user.totp_secret:
            return {"ok": False, "error": "TOTP is not initialized. Run setup first."}

        is_valid = pyotp.TOTP(user.totp_secret).verify(req.otp_code, valid_window=1)
        if not is_valid:
            return {"ok": False, "error": "Invalid OTP code."}

        user.is_totp_enabled = True
        db.commit()
        return {"ok": True, "is_totp_enabled": True}
    finally:
        db.close()


@app.post("/api/2fa/disable")
def disable_totp(current_user: dict = Depends(get_current_user)):
    db = database.SessionLocal()
    try:
        user = database.get_user_by_username(db, current_user["username"])
        if not user:
            return {"ok": False, "error": "User not found."}
        user.is_totp_enabled = False
        user.totp_secret = None
        db.commit()
        return {"ok": True, "is_totp_enabled": False}
    finally:
        db.close()

@app.post("/api/logout")
async def logout(request: Request, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    try:
        username = current_user["username"]
        client_ip = request.client.host if request.client else "Unknown"
        user_agent = request.headers.get("User-Agent", "Unknown")
        background_tasks.add_task(send_telegram_alert, username, client_ip, user_agent, "LOGOUT")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Logout error for {current_user.get('username')}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

import urllib.parse

@app.websocket("/ws/scan")
async def websocket_scan(websocket: WebSocket):
    await websocket.accept()
    try:
        req_data = await websocket.receive_text()
        req = json.loads(req_data)
        
        raw_target = req.get("target", "")
        if "://" in raw_target:
            target = urllib.parse.urlparse(raw_target).netloc
        elif "/" in raw_target:
            target = raw_target.split("/")[0]
        else:
            target = raw_target

        ports_mode = req.get("ports", "fast") # 'fast' or 'all'
        token = req.get("token", "")
        
        # User explicitly requested to remove target restrictions because the system is secured
        # behind a strong authentication layer. Any authorized user can scan any domain.
        if not token:
            await websocket.send_json({
                "type": "error", 
                "message": "Valid clearance token required to initialize scanner."
            })
            await websocket.close()
            return
            
        # Verify JWT Token
        operator_role = "guest"
        username = "guest"
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            operator_role = payload.get("role", "operator")
            username = payload.get("sub", "unknown")
        except jwt.ExpiredSignatureError:
            await websocket.send_json({"type": "error", "message": "Clearance token expired."})
            await websocket.close()
            return
        except jwt.InvalidTokenError:
            await websocket.send_json({"type": "error", "message": "Invalid clearance token."})
            await websocket.close()
            return

        # SSRF Protection Core Layer
        def is_ssrf_attempt(tgt):
            if tgt.lower() in ['localhost', '127.0.0.1']: return True
            try:
                ip = socket.gethostbyname(tgt)
                return ipaddress.ip_address(ip).is_private or ipaddress.ip_address(ip).is_loopback
            except Exception:
                return True
                
        if is_ssrf_attempt(target):
            await websocket.send_json({"type": "error", "message": "SSRF Protection Activated: Cannot scan private or internal network endpoints."})
            await websocket.close()
            return
            

        # Standard ports or subset to 1024
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306, 3389, 8080] if ports_mode == "fast" else list(range(1, 1025))
        
        await websocket.send_json({"type": "info", "message": "Tracing Network Routing and Geolocation Data..."})
        geo_data = await lookup_geo(target)
        if geo_data:
            await websocket.send_json({"type": "info", "message": f"Target traced to {geo_data.get('city', 'Unknown')}, {geo_data.get('country', 'Unknown')}"})
            await websocket.send_json({"type": "geolocation", "data": geo_data})

        await websocket.send_json({"type": "info", "message": "Performing OSINT Reconnaissance (Subdomains)..."})
        subs = await enumerate_subdomains(target)
        if subs:
            await websocket.send_json({"type": "info", "message": f"Found {len(subs)} subdomains."})
            await websocket.send_json({"type": "subdomains", "data": subs})
        
        await websocket.send_json({"type": "info", "message": f"Starting port scan on {target} ({len(ports)} ports)..."})
        
        async def progress_callback(port: int, ok: bool):
            if ok:
                await websocket.send_json({"type": "port_found", "port": port})
                
        scanner = AsyncPortScanner(target, ports, concurrency=50, timeout=3.0, progress_callback=progress_callback)
        open_ports = await scanner.run()
        
        await websocket.send_json({"type": "info", "message": f"Port scan completed. {len(open_ports)} open ports found."})
        
        web_ports = [p for p in open_ports if p in [80, 443, 8080]]
        web_recon = {}
        if web_ports:
            await websocket.send_json({"type": "info", "message": "Executing Advanced Web Fuzzing and WAF Detection..."})
            for wp in web_ports:
                waf = await detect_waf(target, wp)
                dirs = await fuzz_directories(target, wp)
                if waf != "No WAF Detected" or dirs:
                    web_recon[str(wp)] = {"waf": waf, "directories": dirs}
            if web_recon:
                await websocket.send_json({"type": "web_recon", "data": web_recon})
        
        if not open_ports:
            await websocket.send_json({"type": "complete", "report": {}})
            await websocket.close()
            return

        await websocket.send_json({"type": "info", "message": "Grabbing banners..."})
        grabber = BannerGrabber(target, timeout=2.0)
        banners = await grabber.grab_many(open_ports)
        await websocket.send_json({"type": "banners", "data": banners})

        await websocket.send_json({"type": "info", "message": "Looking up CVEs..."})
        cve = CVELookup()
        cve_results = cve.check_services(banners)
        await websocket.send_json({"type": "cves", "data": cve_results})

        await websocket.send_json({"type": "info", "message": "Generating AI Risk Assessment..."})
        try:
            ai = AIHelper()
            explanations = ai.explain_cves(cve_results)
        except Exception as e:
            explanations = {p: f"AI Error: {e}" for p in open_ports}
            
        await websocket.send_json({"type": "explanations", "data": explanations})

        # Generate report data
        report = Reporter(target, open_ports, banners, cve_results, explanations)
        report_data = report._make_data()
        report_data["subdomains"] = subs
        if geo_data:
            report_data["geolocation"] = geo_data
        if web_recon:
            report_data["web_recon"] = web_recon
        
        # Determine aggregate risk
        risk_level = "Secure"
        if any(len(cves) > 0 for cves in cve_results.values()):
            risk_level = "High"
            # Send Web Push alert for high risk
            asyncio.create_task(send_web_push("🚨 High Risk Vulnerability Found!", f"Target {target} is exposed with critical exploits."))
        elif len(open_ports) > 0:
            risk_level = "Medium"
            
        # Save to SQLite Database natively!
        database.save_report(target, username, report_data, risk_level)
        
        await websocket.send_json({"type": "complete", "report": report_data})
        await websocket.close()
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
