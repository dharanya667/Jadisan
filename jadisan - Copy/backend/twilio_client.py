"""
twilio_client.py
Sends WhatsApp messages back to citizens via the Twilio REST API.
"""
import logging
import os
from typing import Optional

from twilio.rest import Client

logger = logging.getLogger(__name__)


def _get_client() -> Client:
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        raise RuntimeError(
            "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in the environment."
        )
    return Client(sid, token)


def _get_from_number() -> str:
    number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
    return number


def send_complaint_confirmation(
    to: str,
    reference_id: str,
    category: str,
    summary: str,
    is_duplicate: bool = False,
    duplicate_ref: Optional[str] = None,
) -> None:
    """
    Send a WhatsApp confirmation message to the citizen.

    Parameters
    ----------
    to : str
        Citizen's WhatsApp number in the format 'whatsapp:+91XXXXXXXXXX'.
    reference_id : str
        Human-readable complaint reference, e.g. 'JDS-20260829-0001'.
    category : str
        Complaint category from Gemini analysis.
    summary : str
        One-sentence summary.
    is_duplicate : bool
        True if this was flagged as a duplicate.
    duplicate_ref : str | None
        Reference ID of the original complaint if duplicate.
    """
    client = _get_client()
    from_number = _get_from_number()

    # Normalise the 'to' number — Twilio requires 'whatsapp:+...' format.
    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    severity_emoji = {
        "Low": "🟢",
        "Medium": "🟡",
        "High": "🟠",
        "Critical": "🔴",
    }

    category_emoji = {
        "Pothole": "🕳️",
        "Water Leak": "💧",
        "Garbage": "🗑️",
        "Broken Streetlight": "💡",
        "Sewage": "🚰",
        "Road Damage": "🛣️",
        "Other": "📌",
    }

    cat_icon = category_emoji.get(category, "📌")

    if is_duplicate:
        body = (
            f"ℹ️ *JadiSan — Issue Already Reported*\n\n"
            f"This issue has already been reported in your area.\n"
            f"Your concern has been noted and the affected-citizen count has been updated.\n\n"
            f"{cat_icon} *Category:* {category}\n"
            f"📝 *Summary:* {summary}\n"
        )
        if duplicate_ref:
            body += f"🔗 *Original Reference:* {duplicate_ref}\n"
        body += "\nThank you for helping us track civic issues! 🙏"
    else:
        body = (
            f"✅ *JadiSan — Complaint Registered!*\n\n"
            f"Your civic complaint has been received and logged.\n\n"
            f"📌 *Reference ID:* `{reference_id}`\n"
            f"{cat_icon} *Category:* {category}\n"
            f"📝 *Summary:* {summary}\n\n"
            f"Our team will review and act on your complaint. "
            f"You can track it using your Reference ID.\n\n"
            f"Thank you for making our city better! 🙏"
        )

    try:
        message = client.messages.create(
            from_=from_number,
            to=to,
            body=body,
        )
        logger.info(
            "WhatsApp confirmation sent to %s (SID: %s)", to, message.sid
        )
    except Exception as exc:
        logger.error("Failed to send WhatsApp message to %s: %s", to, exc)
        raise


def send_resolution_notification(
    to: str,
    reference_id: str,
    summary: str,
    department: str = "Municipal Department",
    resolution_notes: str = "",
) -> None:
    """
    Send a WhatsApp notification to the citizen when their grievance is marked as Resolved.
    """
    client = _get_client()
    from_number = _get_from_number()

    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    body = (
        f"🎉 *JadiSan — Grievance Resolved!*\n\n"
        f"Great news! Your complaint has been inspected and resolved by the authorities.\n\n"
        f"📌 *Reference ID:* `{reference_id}`\n"
        f"🏛️ *Department:* {department}\n"
        f"📝 *Summary:* {summary}\n"
        f"✅ *Status:* Resolved\n"
    )
    if resolution_notes:
        body += f"💬 *Action Taken:* {resolution_notes}\n"

    body += "\nThank you for reporting civic issues and helping keep our community clean and safe! 🙏"

    try:
        message = client.messages.create(
            from_=from_number,
            to=to,
            body=body,
        )
        logger.info(
            "WhatsApp resolution notification sent to %s (SID: %s)", to, message.sid
        )
    except Exception as exc:
        logger.error("Failed to send resolution notification to %s: %s", to, exc)


def send_location_request(to: str) -> None:
    """
    Send a message requesting the citizen to share their WhatsApp location pin.
    """
    client = _get_client()
    from_number = _get_from_number()

    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    body = "📍 I couldn't identify the location of this issue. Please share your current location on WhatsApp so we can send the complaint to the correct officer."

    try:
        message = client.messages.create(
            from_=from_number,
            to=to,
            body=body,
        )
        logger.info("WhatsApp location request sent to %s (SID: %s)", to, message.sid)
    except Exception as exc:
        logger.error("Failed to send location request to %s: %s", to, exc)


def send_location_received_confirmation(
    to: str,
    reference_id: str,
) -> None:
    """
    Send a WhatsApp confirmation when location is attached to a pending complaint.
    """
    client = _get_client()
    from_number = _get_from_number()

    if not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"

    body = f"Thank you. Your location has been received. Your complaint {reference_id} has been registered successfully."

    try:
        message = client.messages.create(
            from_=from_number,
            to=to,
            body=body,
        )
        logger.info("WhatsApp location confirmation sent to %s (SID: %s)", to, message.sid)
    except Exception as exc:
        logger.error("Failed to send location confirmation to %s: %s", to, exc)


