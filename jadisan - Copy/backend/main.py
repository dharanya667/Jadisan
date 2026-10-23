"""
main.py
JadiSan — FastAPI application entry point.

Endpoints:
  POST /webhook                    Twilio WhatsApp incoming message
  GET  /api/complaints             Admin dashboard data feed
  POST /api/escalate/all           Manually trigger escalation check
  POST /api/escalate/{id}          Manually escalate a single complaint
  GET  /api/health                 Health check
  GET  /                           Admin dashboard (static HTML)
"""
import asyncio
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Load .env explicitly from backend directory before importing modules
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)
from analyzer import analyze_complaint, init_gemini
from db_config import authenticate_user, get_all_departments, get_matrix_officer, init_db
from escalator import escalate_single, run_escalation_check, start_scheduler, stop_scheduler
from firestore_client import (
    create_complaint,
    get_all_complaints,
    get_recent_complaints,
    increment_affected_count,
    init_firestore,
)
from geocoder import geocode_location, reverse_geocode
from transcriber import load_model, transcribe_audio
from twilio_client import (
    send_complaint_confirmation,
    send_location_received_confirmation,
    send_location_request,
    send_resolution_notification,
)

# ─── Pending Location State ───────────────────────────────────────────────────

PENDING_LOCATION_COMPLAINTS: dict[str, dict] = {}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── App lifecycle ────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("JadiSan starting up …")
    init_db()
    init_firestore()
    init_gemini()
    load_model()          # Load Whisper 'base' model into memory once.
    start_scheduler()
    yield
    logger.info("JadiSan shutting down …")
    stop_scheduler()


app = FastAPI(
    title="JadiSan — Civic Grievance API",
    description="Voice-based civic complaint system for citizens via WhatsApp.",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── Static files (dashboard) ─────────────────────────────────────────────────

DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard"
app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    html_path = DASHBOARD_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/styles.css", include_in_schema=False)
async def serve_styles():
    css_path = DASHBOARD_DIR / "styles.css"
    if not css_path.exists():
        raise HTTPException(status_code=404, detail="Stylesheet not found.")
    return FileResponse(css_path)


@app.get("/app.js", include_in_schema=False)
async def serve_app_js():
    js_path = DASHBOARD_DIR / "app.js"
    if not js_path.exists():
        raise HTTPException(status_code=404, detail="Script not found.")
    return FileResponse(js_path)


# ─── Health ───────────────────────────────────────────────────────────────────


@app.get("/api/health", tags=["System"])
async def health():
    return {"status": "ok", "service": "JadiSan"}


# ─── Webhook ──────────────────────────────────────────────────────────────────


@app.post("/webhook", tags=["Twilio"])
async def webhook(
    request: Request,
    From: str = Form(default=""),
    Body: str = Form(default=""),
    MediaUrl0: str = Form(default=""),
    MediaContentType0: str = Form(default=""),
    Latitude: str = Form(default=""),
    Longitude: str = Form(default=""),
    NumMedia: str = Form(default="0"),
):
    """
    Receives incoming WhatsApp messages from Twilio.
    Handles:
      - Voice notes (OGG audio) → Whisper → Gemini → Firestore → Reply
      - Location shares  → captured as lat/lng coordinates
      - Text messages    → treated as typed complaints (Gemini directly)
    Returns an empty TwiML <Response/> immediately; the reply is sent async
    via the REST API so Twilio doesn't timeout waiting for us.
    """
    logger.info("Webhook received from %s | media=%s | body='%s'", From, NumMedia, Body[:80])

    sender = From  # Already in 'whatsapp:+91...' format from Twilio.

    # We do the heavy lifting in a background task so the webhook returns fast.
    asyncio.create_task(
        _process_complaint(
            sender=sender,
            body=Body,
            media_url=MediaUrl0,
            media_content_type=MediaContentType0,
            latitude=Latitude,
            longitude=Longitude,
        )
    )

    # Twilio expects a TwiML response; empty = no immediate reply.
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )


async def _process_complaint(
    sender: str,
    body: str,
    media_url: str,
    media_content_type: str,
    latitude: str,
    longitude: str,
) -> None:
    """
    Background pipeline:
    1. Parse inputs (audio voice transcription, WhatsApp text, WhatsApp location pin).
    2. Handle pending location workflow if citizen was previously asked for location.
    3. Analyze complaint via Gemini & extract location_found status.
    4. If location is missing/vague, store pending state and request location via WhatsApp.
    5. If location is valid, create complaint in Firestore and send registration confirmation.
    """
    try:
        # Check for GPS coordinates shared directly via WhatsApp location pin
        lat: float | None = None
        lng: float | None = None
        reverse_address: str | None = None

        if latitude and longitude:
            try:
                lat = float(latitude)
                lng = float(longitude)
                logger.info("WhatsApp GPS Location Pin received from %s: %s, %s", sender, lat, lng)
                reverse_address = await reverse_geocode(lat, lng)
            except ValueError:
                pass

        # CASE 3: Citizen sends a WhatsApp Location pin to resolve a pending complaint
        if lat is not None and lng is not None and sender in PENDING_LOCATION_COMPLAINTS:
            logger.info("Resolving pending location complaint for %s using WhatsApp GPS pin...", sender)
            pending = PENDING_LOCATION_COMPLAINTS.pop(sender)
            final_loc = reverse_address or f"GPS Pin ({lat:.4f}, {lng:.4f})"

            complaint_data = {
                "sender_phone": sender,
                "transcript": pending["transcript"],
                "summary": pending["summary"],
                "category": pending["category"],
                "severity": pending["severity"],
                "location_text": final_loc,
                "latitude": lat,
                "longitude": lng,
                "assigned_officer": pending["assigned_officer"],
                "is_duplicate": False,
                "duplicate_of_id": None,
                "language_detected": pending.get("language_detected", "Unknown"),
            }
            doc_id, reference_id = create_complaint(complaint_data)
            logger.info("Created complaint %s (%s) after location share by %s", doc_id, reference_id, sender)

            await asyncio.to_thread(
                send_location_received_confirmation,
                to=sender,
                reference_id=reference_id,
            )
            return

        # ── Step 1: Transcribe audio or extract text message ─────────────────
        transcript = ""
        if media_url and "audio" in media_content_type.lower():
            logger.info("Downloading audio from %s", media_url)
            audio_bytes = await _download_twilio_media(media_url)
            if audio_bytes:
                ext = media_content_type.split("/")[-1].split(";")[0].strip() or "ogg"
                tmp = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
                try:
                    tmp.write(audio_bytes)
                    tmp.flush()
                    tmp.close()
                    transcript = await transcribe_audio(tmp.name)
                    logger.info("Transcript: %s", transcript[:120])
                finally:
                    try:
                        os.unlink(tmp.name)
                    except OSError:
                        pass
            else:
                logger.warning("Audio download returned empty bytes.")

        if not transcript and body:
            transcript = body
            logger.info("Using text body as transcript: %s", transcript[:80])

        if not transcript and lat is not None and lng is not None:
            location_str = reverse_address if reverse_address else f"({lat}, {lng})"
            transcript = f"Civic grievance reported via WhatsApp GPS Location Pin at {location_str}."

        if not transcript:
            logger.warning("No usable content from %s — ignoring.", sender)
            return

        recent = get_recent_complaints(limit=50)

        # CASE 4: Citizen sends follow-up text instead of GPS pin for a pending complaint
        if sender in PENDING_LOCATION_COMPLAINTS:
            pending = PENDING_LOCATION_COMPLAINTS[sender]
            combined_text = f"{pending['transcript']}. Additional location details: {transcript}"
            logger.info("Evaluating follow-up location text for %s: '%s'", sender, transcript)

            analysis = await analyze_complaint(combined_text, recent)
            loc_found = analysis.get("location_found", False)
            loc_text = analysis.get("location_text", "").strip()

            if loc_found and loc_text:
                coords = await geocode_location(loc_text)
                c_lat, c_lng = coords if coords else (None, None)

                PENDING_LOCATION_COMPLAINTS.pop(sender)
                complaint_data = {
                    "sender_phone": sender,
                    "transcript": combined_text,
                    "summary": analysis["summary"],
                    "category": pending["category"],
                    "severity": pending["severity"],
                    "location_text": loc_text,
                    "latitude": c_lat,
                    "longitude": c_lng,
                    "assigned_officer": pending["assigned_officer"],
                    "is_duplicate": False,
                    "duplicate_of_id": None,
                    "language_detected": pending.get("language_detected", "Unknown"),
                }
                doc_id, reference_id = create_complaint(complaint_data)
                logger.info("Created complaint %s (%s) after follow-up location text by %s", doc_id, reference_id, sender)

                await asyncio.to_thread(
                    send_location_received_confirmation,
                    to=sender,
                    reference_id=reference_id,
                )
                return
            else:
                # Still ambiguous — re-ask for WhatsApp location pin
                logger.info("Follow-up location text for %s still ambiguous — re-prompting...", sender)
                await asyncio.to_thread(send_location_request, to=sender)
                return

        # ── Step 2: New Complaint Analysis ──────────────────────────────────
        analysis = await analyze_complaint(transcript, recent)
        location_found = analysis.get("location_found", False)
        location_text = analysis.get("location_text", "").strip()

        final_location = reverse_address or location_text

        # Geocode if location text exists and lat/lng not already set by GPS pin
        if lat is None and location_text:
            coords = await geocode_location(location_text)
            if coords:
                lat, lng = coords
                location_found = True

        # Determine Matrix Officer (Department + Tier)
        dept = analysis.get("category", "Other")
        officer_info = get_matrix_officer(dept, "Ward")
        initial_officer = f"{officer_info.get('full_name')} ({officer_info.get('role')})"

        # CASE 2: Location is NOT specified or found — store pending state and request location
        if not location_found and lat is None:
            logger.info("Location missing for %s. Storing pending state and sending location request.", sender)
            PENDING_LOCATION_COMPLAINTS[sender] = {
                "sender_phone": sender,
                "transcript": transcript,
                "summary": analysis["summary"],
                "category": analysis["category"],
                "severity": analysis["severity"],
                "assigned_officer": initial_officer,
                "language_detected": analysis.get("language_detected", "Unknown"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await asyncio.to_thread(send_location_request, to=sender)
            return

        # CASE 1: Location IS specified — process & store in Firestore normally
        is_dup = analysis.get("is_duplicate", False)
        dup_id = analysis.get("duplicate_of_id")

        if is_dup and dup_id:
            recent_ids = {c["id"] for c in recent}
            if dup_id not in recent_ids:
                logger.warning("Gemini returned unknown duplicate_of_id %s — treating as new.", dup_id)
                is_dup = False
                dup_id = None

        if is_dup and dup_id:
            increment_affected_count(dup_id)
            orig = next((c for c in recent if c["id"] == dup_id), {})
            orig_ref = orig.get("reference_id", dup_id)

            await asyncio.to_thread(
                send_complaint_confirmation,
                to=sender,
                reference_id=orig_ref,
                category=analysis["category"],
                summary=analysis["summary"],
                is_duplicate=True,
                duplicate_ref=orig_ref,
            )
        else:
            complaint_data = {
                "sender_phone": sender,
                "transcript": transcript,
                "summary": analysis["summary"],
                "category": analysis["category"],
                "severity": analysis["severity"],
                "location_text": final_location or "Location recorded via GPS",
                "latitude": lat,
                "longitude": lng,
                "assigned_officer": initial_officer,
                "is_duplicate": False,
                "duplicate_of_id": None,
                "language_detected": analysis.get("language_detected", "Unknown"),
            }
            doc_id, reference_id = create_complaint(complaint_data)
            logger.info("Stored complaint %s as %s (Assigned: %s)", doc_id, reference_id, initial_officer)

            await asyncio.to_thread(
                send_complaint_confirmation,
                to=sender,
                reference_id=reference_id,
                category=analysis["category"],
                summary=analysis["summary"],
                is_duplicate=False,
            )

    except Exception as exc:
        logger.exception("Pipeline error processing complaint from %s: %s", sender, exc)


async def _download_twilio_media(url: str) -> bytes | None:
    """Download audio from a Twilio media URL using Basic Auth."""
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, auth=(sid, token))
                logger.info("Media download status: %s | content-length: %s", resp.status_code, len(resp.content))
                resp.raise_for_status()
                return resp.content
        except Exception:
            logger.exception("Failed to download media from %s (attempt %s)", url, attempt + 1)
            if attempt == 0:
                await asyncio.sleep(1)
    return None
# ─── Admin API ────────────────────────────────────────────────────────────────


@app.get("/api/complaints", tags=["Admin"])
async def list_complaints(
    category: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    tier: str | None = None,
    limit: int = 500,
):
    """Return complaints for the admin dashboard, with optional filters."""
    try:
        complaints = get_all_complaints(
            category=category,
            severity=severity,
            status=status,
            tier=tier,
            limit=limit,
        )
        return JSONResponse(content={"complaints": complaints, "total": len(complaints)})
    except Exception as exc:
        logger.error("Error fetching complaints: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/escalate/all", tags=["Admin"])
async def trigger_escalation_all():
    """Manually run the escalation check across all overdue complaints."""
    try:
        escalated = await run_escalation_check()
        return {
            "escalated_count": len(escalated),
            "details": escalated,
        }
    except Exception as exc:
        logger.error("Manual escalation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/escalate/{complaint_id}", tags=["Admin"])
async def trigger_escalation_single(complaint_id: str):
    """Manually escalate a single complaint to the next tier."""
    try:
        result = await escalate_single(complaint_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Single escalation failed for %s: %s", complaint_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


from db_config import authenticate_user, get_all_departments, get_matrix_officer, init_db, register_user


# ─── Admin Authentication & Department Endpoints ───────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    zone: str
    password: str


class StatusUpdateRequest(BaseModel):
    status: str
    resolution_notes: str = ""


class DepartmentResponseRequest(BaseModel):
    response: str


class DepartmentForwardRequest(BaseModel):
    department: str = ""


def get_department_for_category(category: str) -> str:
    cat = (category or "").lower()
    if any(k in cat for k in ["road", "pothole", "asphalt", "street damage"]):
        return "Road Department"
    if any(k in cat for k in ["sewage", "drain", "sewer", "manhole"]):
        return "Sewage Department"
    if any(k in cat for k in ["water", "leak", "pipe"]):
        return "Water Department"
    if any(k in cat for k in ["garbage", "waste", "sanitation", "trash"]):
        return "Sanitation Department"
    if any(k in cat for k in ["light", "streetlights", "electric", "power"]):
        return "Electricity Department"
    return "Road Department"


@app.post("/api/auth/login", tags=["Auth"])
async def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {"status": "success", "user": user}


@app.post("/api/auth/register", tags=["Auth"])
async def register(req: RegisterRequest):
    try:
        username = req.name.strip().lower().replace(" ", "_")
        user = register_user(username=username, password=req.password, full_name=req.name, role=req.zone)
        return {"status": "success", "user": user}
    except Exception as exc:
        logger.error("Registration error: %s", exc)
        raise HTTPException(status_code=400, detail="Registration failed or username already exists.")


@app.get("/api/departments", tags=["Admin"])
async def list_departments():
    return {"departments": get_all_departments()}


@app.post("/api/complaints/{complaint_id}/forward", tags=["Admin"])
async def forward_complaint(complaint_id: str, req: DepartmentForwardRequest | None = None):
    """Forward a complaint to its responsible department (Internal Dashboard Routing)."""
    from firestore_client import get_db
    try:
        now = datetime.now(timezone.utc)
        target_dept = (req.department if req and req.department else "").strip()
        ref = None
        doc_exists = False
        dept_name = target_dept or "Road Department"

        try:
            db = get_db()
            ref = db.collection("complaints").document(complaint_id)
            doc = ref.get()
            if doc.exists:
                doc_exists = True
                data = doc.to_dict()
                category = data.get("category") or data.get("problem_type") or ""
                dept_name = target_dept or get_department_for_category(category)
                ref.update({
                    "status": "FORWARDED",
                    "assigned": True,
                    "assigned_department": dept_name,
                    "department_name": dept_name,
                    "forwarded_at": now.isoformat(),
                    "updated_at": now,
                })
        except Exception as exc:
            logger.warning("Could not update Firestore for complaint %s: %s", complaint_id, exc)

        return {
            "status": "success",
            "id": complaint_id,
            "complaint_status": "FORWARDED",
            "assigned": True,
            "assigned_department": dept_name,
            "forwarded_at": now.isoformat(),
        }
    except Exception as exc:
        logger.error("Error forwarding complaint %s: %s", complaint_id, exc)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


@app.post("/api/complaints/{complaint_id}/department-response", tags=["Admin"])
async def receive_department_response(complaint_id: str, req: DepartmentResponseRequest):
    """Receive and record official department response text for a complaint."""
    from firestore_client import get_db
    try:
        now = datetime.now(timezone.utc)
        try:
            db = get_db()
            ref = db.collection("complaints").document(complaint_id)
            doc = ref.get()
            if doc.exists:
                ref.update({
                    "department_response": req.response,
                    "response_received": True,
                    "response_received_at": now.isoformat(),
                    "status": "RESPONSE_RECEIVED",
                    "updated_at": now,
                })
        except Exception as exc:
            logger.warning("Could not update department response in Firestore for %s: %s", complaint_id, exc)

        return {
            "status": "success",
            "id": complaint_id,
            "complaint_status": "RESPONSE_RECEIVED",
            "department_response": req.response,
            "response_received_at": now.isoformat(),
        }
    except Exception as exc:
        logger.error("Error updating department response for %s: %s", complaint_id, exc)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


@app.patch("/api/complaints/{complaint_id}/status", tags=["Admin"])
async def update_complaint_status(complaint_id: str, req: StatusUpdateRequest):
    """Update complaint status (e.g., RESOLVED) and trigger citizen WhatsApp notification if resolved."""
    from firestore_client import get_db
    try:
        now = datetime.now(timezone.utc)
        new_status = req.status.upper()
        data = {}

        try:
            db = get_db()
            ref = db.collection("complaints").document(complaint_id)
            doc = ref.get()
            if doc.exists:
                data = doc.to_dict()
                update_fields = {
                    "status": new_status,
                    "resolution_notes": req.resolution_notes,
                    "updated_at": now,
                }
                if new_status == "RESOLVED":
                    update_fields["resolved"] = True
                    update_fields["resolved_at"] = now.isoformat()
                    update_fields["solved_at"] = now.isoformat()

                ref.update(update_fields)
        except Exception as exc:
            logger.warning("Could not update status in Firestore for %s: %s", complaint_id, exc)

        # Trigger existing WhatsApp notification if status changed to 'RESOLVED' (UNTOUCHED!)
        whatsapp_sent = False
        if new_status == "RESOLVED" and data.get("sender_phone"):
            try:
                logger.info("Sending resolution WhatsApp notification to %s for %s...", data["sender_phone"], complaint_id)
                await asyncio.to_thread(
                    send_resolution_notification,
                    to=data["sender_phone"],
                    reference_id=data.get("reference_id", complaint_id),
                    summary=data.get("summary", "Civic Grievance"),
                    department=data.get("category", "General Municipal Office"),
                    resolution_notes=req.resolution_notes,
                )
                whatsapp_sent = True
            except Exception as exc:
                logger.error("Failed to send WhatsApp resolution notification to %s: %s", data["sender_phone"], exc)

        return {
            "status": "success",
            "id": complaint_id,
            "new_status": new_status,
            "resolved": (new_status == "RESOLVED"),
            "whatsapp_sent": whatsapp_sent,
            "resolution_notes": req.resolution_notes,
        }
    except Exception as exc:
        logger.error("Error updating complaint status for %s: %s", complaint_id, exc)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})



