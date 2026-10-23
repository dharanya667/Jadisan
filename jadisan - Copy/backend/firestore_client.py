"""
firestore_client.py
Handles all Firestore read/write operations for JadiSan.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter

logger = logging.getLogger(__name__)

_db: Optional[firestore.Client] = None


def init_firestore() -> firestore.Client:
    """Initialise Firebase Admin SDK and return the Firestore client."""
    global _db
    if _db is not None:
        return _db

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not cred_path:
        raise RuntimeError("FIREBASE_CREDENTIALS_PATH is not set in the environment.")

    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    logger.info("Firestore initialised successfully.")
    return _db


def get_db() -> firestore.Client:
    if _db is None:
        raise RuntimeError("Firestore not initialised. Call init_firestore() first.")
    return _db


# ─── Reference ID ──────────────────────────────────────────────────────────────

def _generate_reference_id() -> str:
    """Generate a human-readable reference ID like JDS-20260829-0001."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"JDS-{today}-"
    try:
        db = get_db()
        start = datetime(
            int(today[:4]), int(today[4:6]), int(today[6:8]), tzinfo=timezone.utc
        )
        count_query = (
            db.collection("complaints")
            .where(filter=FieldFilter("created_at", ">=", start))
            .count()
        )
        agg_result = count_query.get()
        count = agg_result[0][0].value if agg_result else 0
        return f"{prefix}{str(count + 1).zfill(4)}"
    except Exception as exc:
        logger.warning("Could not query reference ID from Firestore, using fallback: %s", exc)
        return f"JDS-{today}-0001"


# ─── Read helpers ──────────────────────────────────────────────────────────────

def get_recent_complaints(limit: int = 50) -> list[dict]:
    """Return the most recent `limit` complaints (for duplicate checking)."""
    try:
        db = get_db()
        docs = (
            db.collection("complaints")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(data)
        return results
    except Exception as exc:
        logger.warning("Could not fetch recent complaints: %s", exc)
        return []


def get_all_complaints(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = 500,
) -> list[dict]:
    """Return complaints for the admin dashboard, with optional filters."""
    db = get_db()
    query = db.collection("complaints").order_by(
        "created_at", direction=firestore.Query.DESCENDING
    )
    if category:
        query = query.where(filter=FieldFilter("category", "==", category))
    if severity:
        query = query.where(filter=FieldFilter("severity", "==", severity))
    if status:
        query = query.where(filter=FieldFilter("status", "==", status))
    if tier:
        query = query.where(filter=FieldFilter("tier", "==", tier))

    docs = query.limit(limit).stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        # Convert Firestore Timestamp to ISO string for JSON serialisation.
        for field in ("created_at", "updated_at"):
            if field in data and hasattr(data[field], "isoformat"):
                data[field] = data[field].isoformat()
        results.append(data)
    return results


def get_overdue_open_complaints(threshold_hours: int) -> list[dict]:
    """Return complaints that are 'open' and older than threshold_hours."""
    from datetime import timedelta

    db = get_db()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)
    docs = (
        db.collection("complaints")
        .where(filter=FieldFilter("status", "==", "open"))
        .where(filter=FieldFilter("created_at", "<=", cutoff))
        .stream()
    )
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


# ─── Write helpers ─────────────────────────────────────────────────────────────

def create_complaint(data: dict) -> str:
    """Create a new complaint document. Returns (doc_id, reference_id)."""
    now = datetime.now(timezone.utc)
    reference_id = _generate_reference_id()

    doc_data = {
        "reference_id": reference_id,
        "sender_phone": data.get("sender_phone", "unknown"),
        "transcript": data.get("transcript", ""),
        "summary": data.get("summary", ""),
        "category": data.get("category", "Other"),
        "department_name": data.get("department_name", "General Municipal Office"),
        "severity": data.get("severity", "Low"),
        "location_text": data.get("location_text", ""),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "email_sent": False,
        "department_response": "",
        "response_received": False,
        "status": "open",
        "tier": "Ward",
        "is_duplicate": data.get("is_duplicate", False),
        "duplicate_of_id": data.get("duplicate_of_id"),
        "affected_count": 1,
        "language_detected": data.get("language_detected", "Unknown"),
        "created_at": now,
        "updated_at": now,
        "solved_at": None,
    }

    try:
        db = get_db()
        _, doc_ref = db.collection("complaints").add(doc_data)
        logger.info("Created complaint %s (ref %s)", doc_ref.id, reference_id)
        return doc_ref.id, reference_id
    except Exception as exc:
        logger.warning("Could not write complaint to Firestore: %s", exc)
        return f"local-{reference_id}", reference_id


def increment_affected_count(complaint_id: str) -> None:
    """Increment the affected_count on the original complaint (duplicate flow)."""
    db = get_db()
    ref = db.collection("complaints").document(complaint_id)
    ref.update(
        {
            "affected_count": firestore.Increment(1),
            "updated_at": datetime.now(timezone.utc),
        }
    )
    logger.info("Incremented affected_count for complaint %s", complaint_id)


def escalate_complaint(complaint_id: str, new_tier: str, assigned_officer: str = "") -> None:
    """Move a complaint to the next escalation tier and assign matrix officer."""
    db = get_db()
    ref = db.collection("complaints").document(complaint_id)
    update_data = {"tier": new_tier, "updated_at": datetime.now(timezone.utc)}
    if assigned_officer:
        update_data["assigned_officer"] = assigned_officer
    ref.update(update_data)
    logger.info("Escalated complaint %s to tier '%s' (Officer: %s)", complaint_id, new_tier, assigned_officer)

