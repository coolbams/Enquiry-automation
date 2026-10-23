import hashlib
import hmac
import logging
import os
import secrets
import uuid
from pathlib import Path

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .apis.resendEmailApi import send_email
from .database import crud
from .database.connection import Base, SessionLocal, engine, get_db
from .schemas import (
    AdminLoginRequest,
    AdminStatsResponse,
    EnquiryDetailsResponse,
    EnquiryLogResponse,
    EnquiryRequest,
    EnquiryResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

Base.metadata.create_all(bind=engine)

app = FastAPI(
    debug=True,
    title="Enquiry Automation API",
    version="1.0.0",
    description="API for automating enquiry processes.",
)
app.mount("/static", StaticFiles(directory=TEMPLATE_DIR), name="static")

security = HTTPBasic(auto_error=False)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.getenv("SECRET_KEY", "enquiry-automation-secret-key-change-in-prod")


def create_session_token(username: str) -> str:
    """Create a signed tamper-proof session token."""
    signature = hmac.new(
        SECRET_KEY.encode(), username.encode(), hashlib.sha256
    ).hexdigest()
    return f"{username}:{signature}"


def verify_session_token(token: str) -> str | None:
    """Validate signed session token and return the username if valid."""
    try:
        username, signature = token.split(":", 1)
        expected = hmac.new(
            SECRET_KEY.encode(), username.encode(), hashlib.sha256
        ).hexdigest()
        if secrets.compare_digest(signature, expected):
            return username
    except Exception:
        return None
    return None


def authenticate_admin(
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(security),
) -> str:
    """Authenticate via HTTP-only cookie first, falling back to HTTP Basic auth."""
    # 1. Cookie-based authentication (Web UI)
    cookie_token = request.cookies.get("admin_session")
    if cookie_token:
        username = verify_session_token(cookie_token)
        if username == ADMIN_USERNAME:
            return username

    # 2. HTTP Basic authentication (Automated tests & API clients)
    if credentials:
        is_correct_user = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
        is_correct_pass = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
        if is_correct_user and is_correct_pass:
            return credentials.username

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Basic"},
    )


def send_email_background(enquiry_id: uuid.UUID, email: str):
    """Worker task that runs after response is returned and records delivery log."""
    db = SessionLocal()
    try:
        send_email(email)
        crud.create_log(
            db,
            enquiry_id=enquiry_id,
            status="email_sent",
            sent_confirmation_email=True,
        )
    except Exception as exc:
        logger.exception("Failed to send confirmation email to %s", email)
        crud.create_log(
            db,
            enquiry_id=enquiry_id,
            status="email_failed",
            sent_confirmation_email=False,
            error_message=str(exc)[:500],
        )
    finally:
        db.close()


@app.get("/")
def read_root():
    """Serve the enquiry form."""
    return FileResponse(TEMPLATE_DIR / "Index.html")


@app.post("/enquiries", response_model=EnquiryResponse)
def make_enquiry(
    enquiry: EnquiryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Endpoint to handle new enquiries."""
    if enquiry.website:
        logger.warning("Bot detected via honeypot from %s", enquiry.email)
        crud.create_log(db, status="bot_blocked", is_human=False)
        return {"message": "Enquiry received successfully"}

    new_enquiry = crud.create_enquiry(db, enquiry)

    if not crud.is_in_cooldown(
        db, email=enquiry.email, exclude_enquiry_id=new_enquiry.id
    ):
        background_tasks.add_task(send_email_background, new_enquiry.id, enquiry.email)
    else:
        logger.info(
            "Skipping confirmation email for %s (cooldown active)", enquiry.email
        )
        crud.create_log(
            db,
            enquiry_id=new_enquiry.id,
            status="cooldown_skipped",
        )

    return {"message": "Enquiry received successfully"}


@app.get("/login")
def serve_login_page(request: Request):
    """Serve login HTML, or redirect to /admin if already logged in."""
    cookie_token = request.cookies.get("admin_session")
    if cookie_token and verify_session_token(cookie_token) == ADMIN_USERNAME:
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse(TEMPLATE_DIR / "login.html")


@app.post("/api/admin/login")
def admin_login(payload: AdminLoginRequest):
    """Authenticate credentials and set secure HTTP-only session cookie."""
    is_correct_user = secrets.compare_digest(payload.username, ADMIN_USERNAME)
    is_correct_pass = secrets.compare_digest(payload.password, ADMIN_PASSWORD)

    if not (is_correct_user and is_correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_session_token(ADMIN_USERNAME)
    response = JSONResponse(content={"message": "Authenticated successfully"})
    response.set_cookie(
        key="admin_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600 * 24,  # 24 hours
    )
    return response


@app.post("/api/admin/logout")
def admin_logout():
    """Clear session cookie and log out."""
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(key="admin_session")
    return response


@app.get("/admin")
def serve_admin_dashboard(request: Request):
    """Serve admin dashboard if authenticated; otherwise redirect to /login."""
    cookie_token = request.cookies.get("admin_session")
    if not (cookie_token and verify_session_token(cookie_token) == ADMIN_USERNAME):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return FileResponse(TEMPLATE_DIR / "admin.html")


@app.get("/api/admin/stats", response_model=AdminStatsResponse)
def get_stats(
    admin: str = Depends(authenticate_admin),
    db: Session = Depends(get_db),
):
    """Return summary metric cards."""
    return crud.get_admin_stats(db)


@app.get("/api/admin/enquiries", response_model=list[EnquiryDetailsResponse])
def get_enquiries(
    skip: int = 0,
    limit: int = 50,
    admin: str = Depends(authenticate_admin),
    db: Session = Depends(get_db),
):
    """Return list of enquiries with their audit logs."""
    return crud.get_enquiries(db, skip=skip, limit=limit)


@app.get("/api/admin/bots", response_model=list[EnquiryLogResponse])
def get_bots(
    skip: int = 0,
    limit: int = 50,
    admin: str = Depends(authenticate_admin),
    db: Session = Depends(get_db),
):
    """Return list of blocked bot logs."""
    return crud.get_bot_logs(db, skip=skip, limit=limit)
