# JadiSan — Voice-Based Civic Grievance Reporting

> Citizens report civic problems (potholes, water leaks, garbage, broken streetlights, etc.)
> by sending a **voice message on WhatsApp** in their own language.
> Built by **Team ByteCraft, Panimalar Engineering College**.

---

## Architecture

```
Citizen Voice → WhatsApp (Twilio Sandbox)
              → FastAPI /webhook
              → OpenAI Whisper (speech-to-text)
              → Gemini 2.5 Flash (classify + duplicate check)
              → Nominatim (geocode location text)
              → Firestore (store complaint)
              → Twilio (send WhatsApp confirmation)
              ↕
          Admin Dashboard (table + map)
              ↕
     APScheduler (hourly escalation: Ward→Zone→District→Commissioner)
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| ngrok | any |
| Firebase project | with Firestore enabled |
| Twilio account | WhatsApp sandbox activated |

---

## Setup

### 1. Create your `.env` file

```bash
cp .env.example .env
# Edit .env with your real credentials
```

Required variables:

```
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
OPENAI_API_KEY=...
GEMINI_API_KEY=...
FIREBASE_CREDENTIALS_PATH=path/to/serviceAccountKey.json
ESCALATION_HOURS=48
```

### 2. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Open the admin dashboard

```
http://localhost:8000/
```

### 5. Expose via ngrok (for Twilio webhook)

```bash
ngrok http 8000
```

Copy the `https://<id>.ngrok-free.app` URL and set it as your Twilio sandbox webhook:

- Go to [Twilio Console → Messaging → WhatsApp Sandbox](https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox)
- Set **"When a message comes in"** to:
  ```
  https://<id>.ngrok-free.app/webhook
  ```
- Method: **HTTP POST**

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhook` | Twilio WhatsApp incoming messages |
| `GET`  | `/api/complaints` | List complaints (supports `?category=&severity=&status=&tier=`) |
| `POST` | `/api/escalate/all` | Run escalation check on all overdue complaints |
| `POST` | `/api/escalate/{id}` | Escalate a single complaint by Firestore ID |
| `GET`  | `/api/health` | Health check |
| `GET`  | `/` | Admin dashboard |

---

## Firestore Schema

Collection: `complaints`

```json
{
  "reference_id": "JDS-20260829-0001",
  "sender_phone": "whatsapp:+919876543210",
  "transcript": "Raw Whisper transcription...",
  "summary": "One-sentence English summary",
  "category": "Pothole",
  "severity": "High",
  "location_text": "near Gandhi statue, Anna Nagar",
  "latitude": 13.0827,
  "longitude": 80.2707,
  "status": "open",
  "tier": "Ward",
  "is_duplicate": false,
  "duplicate_of_id": null,
  "affected_count": 1,
  "language_detected": "Tamil",
  "created_at": "2026-08-29T12:34:56Z",
  "updated_at": "2026-08-29T12:34:56Z"
}
```

---

## Escalation

- **Automatic**: APScheduler runs every hour, escalates any `open` complaint
  older than `ESCALATION_HOURS` (default: 48h) to the next tier.
- **Manual (demo)**: Click **⚡ Escalate** on any row in the dashboard,
  or **⚡ Escalate Overdue** to run a bulk check.
- **Tier ladder**: `Ward → Zone → District → Commissioner`

---

## Testing the Pipeline (without a real WhatsApp message)

```bash
# Test the full pipeline with a text message
curl -X POST http://localhost:8000/webhook \
  -d "From=whatsapp:+919876543210" \
  -d "Body=There is a large pothole near the Gandhi statue on Anna Salai that is causing accidents" \
  -d "NumMedia=0"

# Check the complaint was stored
curl http://localhost:8000/api/complaints | python -m json.tool

# Manually escalate all overdue complaints (demo)
curl -X POST http://localhost:8000/api/escalate/all
```

---

## Project Structure

```
jadisan/
├── backend/
│   ├── main.py              # FastAPI app + webhook + admin API
│   ├── transcriber.py       # OpenAI Whisper transcription
│   ├── analyzer.py          # Gemini 2.5 Flash classification
│   ├── firestore_client.py  # Firestore CRUD
│   ├── twilio_client.py     # WhatsApp confirmation sender
│   ├── escalator.py         # APScheduler + manual escalation
│   ├── geocoder.py          # Nominatim geocoding
│   └── requirements.txt
├── dashboard/
│   ├── index.html           # Admin SPA
│   ├── styles.css
│   └── app.js
├── .env.example
└── README.md
```
