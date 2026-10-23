"""
analyzer.py
Uses Gemini 2.5 Flash to classify a complaint and check for duplicates.
"""
import json
import logging
import os
import re
from typing import Optional

import google.generativeai as genai # type: ignore

logger = logging.getLogger(__name__)

# ─── Categories & Severity ────────────────────────────────────────────────────

CATEGORIES = [
    "Pothole",
    "Water Leak",
    "Garbage",
    "Broken Streetlight",
    "Sewage",
    "Road Damage",
    "Other",
]

SEVERITIES = ["Low", "Medium", "High", "Critical"]

TIERS = ["Ward", "Zone", "District", "Commissioner"]


# ─── Initialisation ───────────────────────────────────────────────────────────

def init_gemini() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment.")
    genai.configure(api_key=api_key)
    logger.info("Gemini configured successfully.")


# ─── Analysis ─────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """
You are JadiSan's civic complaint classifier. Your job is to analyse a citizen's
voice-transcribed or text message and return a structured JSON object.

CATEGORIES (choose exactly one):
Pothole, Water Leak, Garbage, Broken Streetlight, Sewage, Road Damage, Other

SEVERITY (choose exactly one):
- Low    : Minor inconvenience, not urgent
- Medium : Causes daily problems for residents
- High   : Safety hazard or major disruption
- Critical: Immediate danger to life or property

LOCATION FOUND:
Set "location_found" to true ONLY if a specific street, area, landmark, bus stand, station, or identifiable place is mentioned in the message (e.g. "near Anna Nagar bus stand", "Tambaram railway station", "Gandhi Road").
Set "location_found" to false if no location is mentioned at all, or if the location is too generic/vague (e.g. "on the road", "here", "in my street", "near my house", "in front of my shop").

You will also receive a list of recent complaints. Check if the new complaint
is likely a DUPLICATE — same type of issue in the same rough location as an
existing complaint.

RETURN ONLY valid JSON. No markdown fences, no explanation. Schema:
{
  "category": "<category>",
  "severity": "<severity>",
  "location_text": "<extracted location string, or empty string>",
  "location_found": <true|false>,
  "summary": "<one concise English sentence describing the issue>",
  "is_duplicate": <true|false>,
  "duplicate_of_id": "<id of the most similar recent complaint, or null>",
  "language_detected": "<language name>"
}
""".strip()


async def analyze_complaint(
    transcript: str,
    recent_complaints: list[dict],
) -> dict:
    """
    Classify a transcribed complaint and check for duplicates.

    Parameters
    ----------
    transcript : str
        Raw transcribed text from Whisper or user message.
    recent_complaints : list[dict]
        Up to 50 recent complaints from Firestore for duplicate detection.

    Returns
    -------
    dict with keys: category, severity, location_text, location_found, summary,
                    is_duplicate, duplicate_of_id, language_detected
    """
    # Build a compact summary of recent complaints for the model context.
    recent_summaries = []
    for c in recent_complaints[:50]:
        recent_summaries.append(
            f"[id={c.get('id','?')}] {c.get('category','?')} at "
            f"'{c.get('location_text','unknown')}': {c.get('summary','')}"
        )
    recent_context = (
        "\n".join(recent_summaries)
        if recent_summaries
        else "No recent complaints on record."
    )

    user_message = (
        f"CITIZEN MESSAGE:\n{transcript}\n\n"
        f"RECENT COMPLAINTS (for duplicate detection):\n{recent_context}"
    )

    model = genai.GenerativeModel(
        model_name="gemini-3.6-flash",
        system_instruction=_SYSTEM_PROMPT,
    )

    try:
        response = await model.generate_content_async(user_message)
        raw = response.text.strip()

        # Strip markdown code fences if Gemini adds them despite instructions.
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)

        # Validate and sanitise fields.
        result["category"] = result.get("category", "Other")
        if result["category"] not in CATEGORIES:
            result["category"] = "Other"

        result["severity"] = result.get("severity", "Low")
        if result["severity"] not in SEVERITIES:
            result["severity"] = "Low"

        result.setdefault("location_text", "")
        loc_text = result["location_text"].strip()

        # Fallback evaluation if location_found is missing
        if "location_found" not in result:
            result["location_found"] = bool(loc_text and len(loc_text) > 3)
        else:
            result["location_found"] = bool(result["location_found"])

        result.setdefault("summary", transcript[:120])
        result.setdefault("is_duplicate", False)
        result.setdefault("duplicate_of_id", None)
        result.setdefault("language_detected", "Unknown")

        logger.info(
            "Gemini analysis: category=%s severity=%s loc_found=%s loc_text='%s'",
            result["category"],
            result["severity"],
            result["location_found"],
            result["location_text"],
        )
        return result

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.error("Failed to parse Gemini response: %s\nRaw: %s", exc, raw if 'raw' in dir() else "N/A")
        # Graceful fallback — store with minimal info
        return {
            "category": "Other",
            "severity": "Low",
            "location_text": "",
            "location_found": False,
            "summary": transcript[:120],
            "is_duplicate": False,
            "duplicate_of_id": None,
            "language_detected": "Unknown",
        }
    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        raise
