"""
test_pipeline.py
Offline unit tests for JadiSan backend components.
Uses monkeypatching to avoid real API calls.
Covers:
  - Gemini analyzer (mock model response)
  - Escalator tier ladder
  - Reference ID format
  - Twilio message builder
  - Geocoder cache
"""
import asyncio
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# ── Ensure backend dir is on path ─────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))


# ─────────────────────────────────────────────────────────────────────────────
# 1. Escalator — tier ladder
# ─────────────────────────────────────────────────────────────────────────────
class TestEscalatorTierLadder(unittest.TestCase):
    def setUp(self):
        # Patch firestore_client so escalator can be imported without Firebase
        self.patcher = patch.dict("sys.modules", {
            "firestore_client": MagicMock(),
        })
        self.patcher.start()
        import importlib
        import escalator
        importlib.reload(escalator)
        self.escalator = escalator

    def tearDown(self):
        self.patcher.stop()

    def test_ladder_ward_to_zone(self):
        self.assertEqual(self.escalator.next_tier("Ward"), "Zone")

    def test_ladder_zone_to_district(self):
        self.assertEqual(self.escalator.next_tier("Zone"), "District")

    def test_ladder_district_to_commissioner(self):
        self.assertEqual(self.escalator.next_tier("District"), "Commissioner")

    def test_ladder_commissioner_is_none(self):
        self.assertIsNone(self.escalator.next_tier("Commissioner"))

    def test_unknown_tier_starts_from_first(self):
        # Unknown tier → index 0, so next is Zone
        self.assertEqual(self.escalator.next_tier("SomethingRandom"), "Zone")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Analyzer — Gemini response parsing
# ─────────────────────────────────────────────────────────────────────────────
class TestGeminiAnalyzer(unittest.IsolatedAsyncioTestCase):
    GOOD_RESPONSE = json.dumps({
        "category": "Pothole",
        "severity": "High",
        "location_text": "near Gandhi statue, Anna Nagar",
        "summary": "Large pothole near Gandhi statue causing traffic hazard.",
        "is_duplicate": False,
        "duplicate_of_id": None,
        "language_detected": "Tamil"
    })

    FENCED_RESPONSE = f"```json\n{GOOD_RESPONSE}\n```"

    def setUp(self):
        os.environ["GEMINI_API_KEY"] = "test-key"

    async def _run_with_mock(self, mock_text: str) -> dict:
        with patch("google.generativeai.GenerativeModel") as MockModel:
            mock_response = MagicMock()
            mock_response.text = mock_text
            mock_instance = MagicMock()
            mock_instance.generate_content_async = AsyncMock(return_value=mock_response)
            MockModel.return_value = mock_instance

            import importlib
            import analyzer
            importlib.reload(analyzer)
            analyzer.init_gemini()
            return await analyzer.analyze_complaint("அங்கே ஒரு பெரிய குழி இருக்கிறது", [])

    async def test_parses_valid_json(self):
        result = await self._run_with_mock(self.GOOD_RESPONSE)
        self.assertEqual(result["category"], "Pothole")
        self.assertEqual(result["severity"], "High")
        self.assertFalse(result["is_duplicate"])
        self.assertEqual(result["language_detected"], "Tamil")

    async def test_strips_markdown_fences(self):
        result = await self._run_with_mock(self.FENCED_RESPONSE)
        self.assertEqual(result["category"], "Pothole")

    async def test_invalid_category_falls_back(self):
        bad = json.dumps({
            "category": "Flying Car",
            "severity": "High",
            "location_text": "",
            "summary": "Test",
            "is_duplicate": False,
            "duplicate_of_id": None,
            "language_detected": "English"
        })
        result = await self._run_with_mock(bad)
        self.assertEqual(result["category"], "Other")

    async def test_invalid_severity_falls_back(self):
        bad = json.dumps({
            "category": "Garbage",
            "severity": "Extreme",
            "location_text": "",
            "summary": "Test",
            "is_duplicate": False,
            "duplicate_of_id": None,
            "language_detected": "English"
        })
        result = await self._run_with_mock(bad)
        self.assertEqual(result["severity"], "Low")

    async def test_malformed_json_returns_fallback(self):
        result = await self._run_with_mock("not json at all {{ bad")
        self.assertEqual(result["category"], "Other")
        self.assertFalse(result["is_duplicate"])


# ─────────────────────────────────────────────────────────────────────────────
# 3. Geocoder — cache behaviour
# ─────────────────────────────────────────────────────────────────────────────
class TestGeocoder(unittest.IsolatedAsyncioTestCase):
    async def test_empty_string_returns_none(self):
        import importlib
        import geocoder
        importlib.reload(geocoder)
        result = await geocoder.geocode_location("")
        self.assertIsNone(result)

    async def test_none_string_returns_none(self):
        import importlib
        import geocoder
        importlib.reload(geocoder)
        result = await geocoder.geocode_location(None)
        self.assertIsNone(result)

    async def test_cache_hit_avoids_nominatim(self):
        import importlib
        import geocoder
        importlib.reload(geocoder)
        # Prime the cache with a fake result
        geocoder._cache["anna nagar, chennai"] = (13.085, 80.21)
        result = await geocoder.geocode_location("Anna Nagar, Chennai")
        self.assertEqual(result, (13.085, 80.21))


# ─────────────────────────────────────────────────────────────────────────────
# 4. Twilio client — message builder (no real API call)
# ─────────────────────────────────────────────────────────────────────────────
class TestTwilioClient(unittest.TestCase):
    def setUp(self):
        os.environ["TWILIO_ACCOUNT_SID"]  = "ACtest"
        os.environ["TWILIO_AUTH_TOKEN"]   = "testtoken"
        os.environ["TWILIO_WHATSAPP_NUMBER"] = "whatsapp:+14155238886"

    def test_new_complaint_message_contains_ref(self):
        captured = {}
        with patch("twilio.rest.Client") as MockClient:
            mock_messages = MagicMock()
            mock_messages.create.return_value = MagicMock(sid="SM123")
            MockClient.return_value.messages = mock_messages

            import importlib
            import twilio_client
            importlib.reload(twilio_client)

            twilio_client.send_complaint_confirmation(
                to="whatsapp:+919876543210",
                reference_id="JDS-20260829-0001",
                category="Pothole",
                summary="Large pothole causing hazard.",
                is_duplicate=False,
            )

            args, kwargs = mock_messages.create.call_args
            body = kwargs.get("body", args[0] if args else "")
            self.assertIn("JDS-20260829-0001", body)
            self.assertIn("Pothole", body)

    def test_duplicate_message_has_no_ref_id_heading(self):
        with patch("twilio.rest.Client") as MockClient:
            mock_messages = MagicMock()
            mock_messages.create.return_value = MagicMock(sid="SM456")
            MockClient.return_value.messages = mock_messages

            import importlib
            import twilio_client
            importlib.reload(twilio_client)

            twilio_client.send_complaint_confirmation(
                to="+919876543210",   # without whatsapp: prefix
                reference_id="JDS-20260829-0001",
                category="Water Leak",
                summary="Water leaking near bus stop.",
                is_duplicate=True,
                duplicate_ref="JDS-20260829-0001",
            )

            args, kwargs = mock_messages.create.call_args
            body = kwargs.get("body", args[0] if args else "")
            self.assertIn("already been reported", body)
            # 'to' should have been normalised to whatsapp:+...
            to_arg = kwargs.get("to", "")
            self.assertTrue(to_arg.startswith("whatsapp:"))


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    unittest.main(verbosity=2)
