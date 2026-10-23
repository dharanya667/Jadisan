"""
escalator.py
Background escalation scheduler and manual escalation helper for JadiSan.

Tier ladder: Ward → Zone → District → Commissioner

The APScheduler job runs every hour and promotes any 'open' complaint
that has been sitting at its current tier longer than ESCALATION_HOURS.
"""
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore

from firestore_client import get_overdue_open_complaints, escalate_complaint

logger = logging.getLogger(__name__)

TIER_LADDER = ["Ward", "Zone", "District", "Commissioner"]

_scheduler: AsyncIOScheduler | None = None


# ─── Escalation logic ─────────────────────────────────────────────────────────

def next_tier(current_tier: str) -> str | None:
    """Return the next tier, or None if already at Commissioner."""
    try:
        idx = TIER_LADDER.index(current_tier)
    except ValueError:
        idx = 0
    if idx < len(TIER_LADDER) - 1:
        return TIER_LADDER[idx + 1]
    return None  # Already at Commissioner — can't escalate further.


async def run_escalation_check() -> list[dict]:
    """
    Check for overdue open complaints and escalate them.
    Returns a list of dicts describing what was escalated (for manual trigger).
    """
    threshold_hours = int(os.getenv("ESCALATION_HOURS", "48"))
    overdue = get_overdue_open_complaints(threshold_hours)
    escalated = []

    for complaint in overdue:
        current = complaint.get("tier", "Ward")
        nxt = next_tier(current)
        if nxt is None:
            logger.info(
                "Complaint %s already at Commissioner — skipping.", complaint["id"]
            )
            continue

        dept = complaint.get("department_name") or complaint.get("category", "Other")
        from db_config import get_matrix_officer
        officer_info = get_matrix_officer(dept, nxt)
        officer_name = f"{officer_info.get('full_name')} ({officer_info.get('role')})"

        escalate_complaint(complaint["id"], nxt, assigned_officer=officer_name)
        record = {
            "id": complaint["id"],
            "reference_id": complaint.get("reference_id", "N/A"),
            "from_tier": current,
            "to_tier": nxt,
            "category": complaint.get("category", "Other"),
            "assigned_officer": officer_name,
        }
        escalated.append(record)
        logger.warning(
            "Escalated complaint %s (%s) from %s → %s | Assigned: %s",
            complaint["id"],
            complaint.get("reference_id"),
            current,
            nxt,
            officer_name,
        )

    if not escalated:
        logger.info("Escalation check: no overdue complaints found.")
    else:
        logger.info("Escalation check: %d complaints escalated.", len(escalated))

    return escalated


async def escalate_single(complaint_id: str) -> dict:
    """
    Manually escalate a single complaint by its Firestore document ID.
    Returns the escalation result dict.
    """
    from firestore_client import get_db
    from db_config import get_matrix_officer

    db = get_db()
    doc = db.collection("complaints").document(complaint_id).get()
    if not doc.exists:
        raise ValueError(f"Complaint '{complaint_id}' not found.")

    data = doc.to_dict()
    current = data.get("tier", "Ward")
    nxt = next_tier(current)
    if nxt is None:
        return {
            "id": complaint_id,
            "reference_id": data.get("reference_id"),
            "from_tier": current,
            "to_tier": current,
            "message": "Already at Commissioner — cannot escalate further.",
        }

    dept = data.get("department_name") or data.get("category", "Other")
    officer_info = get_matrix_officer(dept, nxt)
    officer_name = f"{officer_info.get('full_name')} ({officer_info.get('role')})"

    escalate_complaint(complaint_id, nxt, assigned_officer=officer_name)
    return {
        "id": complaint_id,
        "reference_id": data.get("reference_id"),
        "from_tier": current,
        "to_tier": nxt,
        "assigned_officer": officer_name,
        "message": f"Escalated from {current} to {nxt} (Assigned to {officer_name}).",
    }



# ─── Scheduler lifecycle ──────────────────────────────────────────────────────

def start_scheduler() -> AsyncIOScheduler:
    """Create and start the APScheduler background job."""
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        run_escalation_check,
        trigger="interval",
        hours=1,
        id="escalation_check",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Escalation scheduler started (interval: 1 hour).")
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Escalation scheduler stopped.")
