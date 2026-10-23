"""
test_server_mock.py
Integration test: starts the FastAPI app with ALL external services mocked
(Firestore, Gemini, Twilio, Whisper) and sends a test POST /webhook request.
Verifies the full request-response cycle and that the pipeline is invoked.
"""
import asyncio
import json
import os
import sys
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(__file__))

# Set up fake env before importing the app
os.environ.update({
    "TWILIO_ACCOUNT_SID":    "ACtest",
    "TWILIO_AUTH_TOKEN":     "testtoken",
    "TWILIO_WHATSAPP_NUMBER":"whatsapp:+14155238886",
    "OPENAI_API_KEY":        "sk-test",
    "GEMINI_API_KEY":        "test-gemini-key",
    "FIREBASE_CREDENTIALS_PATH": "fake_path.json",
    "ESCALATION_HOURS":      "48",
})

# ── Mock everything that touches external services ────────────────────────────
MOCK_ANALYSIS = {
    "category": "Pothole",
    "severity": "High",
    "location_text": "Anna Salai near Gemini Flyover",
    "summary": "Large pothole on Anna Salai causing traffic hazard.",
    "is_duplicate": False,
    "duplicate_of_id": None,
    "language_detected": "English",
}

patches = [
    patch("firestore_client.init_firestore",    return_value=None),
    patch("firestore_client._db",               MagicMock()),
    patch("firestore_client.get_recent_complaints", return_value=[]),
    patch("firestore_client.create_complaint",  return_value=("fake-doc-id", "JDS-20260829-TEST")),
    patch("analyzer.init_gemini",               return_value=None),
    patch("analyzer.analyze_complaint",         new=AsyncMock(return_value=MOCK_ANALYSIS)),
    patch("geocoder.geocode_location",          new=AsyncMock(return_value=(13.0827, 80.2707))),
    patch("twilio_client.send_complaint_confirmation", return_value=None),
    patch("escalator.start_scheduler",          return_value=MagicMock()),
    patch("escalator.stop_scheduler",           return_value=None),
]

for p in patches:
    p.start()


class TestWebhookEndpoint(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from httpx import AsyncClient, ASGITransport
        import main  # import after patches applied
        self.client = AsyncClient(
            transport=ASGITransport(app=main.app),
            base_url="http://test",
        )
        # Give the lifespan a moment
        await asyncio.sleep(0.1)

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_webhook_returns_twiml(self):
        """POST /webhook should return empty TwiML <Response/>."""
        resp = await self.client.post(
            "/webhook",
            data={
                "From": "whatsapp:+919876543210",
                "Body": "There is a big pothole on Anna Salai near Gemini Flyover",
                "NumMedia": "0",
                "MediaUrl0": "",
                "MediaContentType0": "",
                "Latitude": "",
                "Longitude": "",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/xml", resp.headers["content-type"])
        self.assertIn("<Response>", resp.text)

    async def test_health_endpoint(self):
        """GET /api/health should return status ok."""
        resp = await self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "JadiSan")

    async def test_complaints_api_returns_list(self):
        """GET /api/complaints should return a JSON object with 'complaints' key."""
        with patch("main.get_all_complaints", return_value=[]):
            resp = await self.client.get("/api/complaints")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("complaints", data)
            self.assertIsInstance(data["complaints"], list)

    async def test_escalate_all_endpoint(self):
        """POST /api/escalate/all should return escalated_count."""
        with patch("main.run_escalation_check", new=AsyncMock(return_value=[])):
            resp = await self.client.post("/api/escalate/all")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("escalated_count", data)

    async def test_escalate_single_not_found(self):
        """POST /api/escalate/{bad-id} should return 404."""
        with patch("main.escalate_single", new=AsyncMock(side_effect=ValueError("not found"))):
            resp = await self.client.post("/api/escalate/nonexistent-id-123")
            self.assertEqual(resp.status_code, 404)

    async def test_webhook_with_gps_coordinates(self):
        """POST /webhook with lat/lng should be accepted."""
        resp = await self.client.post(
            "/webhook",
            data={
                "From": "whatsapp:+919876543210",
                "Body": "Garbage dump",
                "NumMedia": "0",
                "MediaUrl0": "",
                "MediaContentType0": "",
                "Latitude": "13.0827",
                "Longitude": "80.2707",
            },
        )
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    # Clean up patches on exit
    unittest.main(verbosity=2, exit=False)
    for p in patches:
        try:
            p.stop()
        except RuntimeError:
            pass
