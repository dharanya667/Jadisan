import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
load_dotenv(backend_dir / ".env")

from main import app, DEPARTMENT_EMAILS, _send_resend_email
import httpx

async def test_email_endpoint():
    print("--- Test 1: Department Email Resolution ---")
    dept = "Road Department"
    recipient = DEPARTMENT_EMAILS.get(dept)
    print(f"Department '{dept}' -> Recipient: {recipient}")

    print("\n--- Test 2: Resend API Dispatch Check ---")
    mock_complaint = {
        "id": "JDS-001",
        "reference_id": "JDS-001",
        "category": "Pothole",
        "department_name": "Road Department",
        "severity": "High",
        "location_text": "Anna Nagar",
        "transcript": "There is a large pothole near Anna Nagar bus stand.",
        "latitude": 13.0850,
        "longitude": 80.2100,
        "created_at": "2026-09-04T23:00:00Z"
    }

    success, email, msg = await _send_resend_email(mock_complaint)
    print(f"Success: {success}")
    print(f"Recipient Email: {email}")
    print(f"Response/Message: {msg}")

if __name__ == "__main__":
    asyncio.run(test_email_endpoint())
