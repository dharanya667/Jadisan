import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to sys.path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Load environment variables
load_dotenv(backend_dir / ".env")

from main import _process_complaint, PENDING_LOCATION_COMPLAINTS
from analyzer import init_gemini
from firestore_client import init_firestore

async def test_workflow():
    init_gemini()
    try:
        init_firestore()
    except Exception as e:
        print("Firestore init note:", e)

    sender = "whatsapp:+919876543210"
    
    print("--- Test 1: Complaint WITHOUT Location ('There is a huge pothole on the road.') ---")
    text_no_loc = "There is a huge pothole on the road."
    
    # Process initial text without location
    await _process_complaint(
        sender=sender,
        body=text_no_loc,
        media_url="",
        media_content_type="",
        latitude="",
        longitude=""
    )
    
    is_pending = sender in PENDING_LOCATION_COMPLAINTS
    print(f"Pending state created for {sender}: {is_pending}")
    if is_pending:
        print("Stored pending data:", PENDING_LOCATION_COMPLAINTS[sender])
    
    print("\n--- Test 2: Citizen shares WhatsApp Location Pin (lat=13.0827, lng=80.2707) ---")
    # Process follow-up location pin
    await _process_complaint(
        sender=sender,
        body="",
        media_url="",
        media_content_type="",
        latitude="13.0827",
        longitude="80.2707"
    )
    
    is_cleared = sender not in PENDING_LOCATION_COMPLAINTS
    print(f"Pending state cleared for {sender}: {is_cleared}")

if __name__ == "__main__":
    asyncio.run(test_workflow())
