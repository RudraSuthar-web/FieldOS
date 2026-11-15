# FieldOS — AI Co-Worker for Field Operations

Voice-first, multilingual field operations intelligence platform built for the **Gnani AI Internship Challenge**. FieldOS empowers field technicians to report machine issues, inspections, and maintenance tasks using natural voice in **Gujarati**, **Hindi**, **English**, and **Hinglish** — converting unstructured vernacular speech into structured work orders and automated operational workflows.

---

## 1. Overview & MVP Flow

Field technicians frequently operate in harsh environments wearing gloves or working in noisy facilities where traditional data entry forms are cumbersome and slow. FieldOS transforms operations through voice intelligence:

1. **Vernacular Speech**: Technician records an issue naturally in Gujarati, Hindi, Hinglish, or English.
2. **Speech-to-Text**: Gnani Prisma ASR (`prisma-v2.5`) transcribes the speech into text.
3. **Operational Intelligence**: Intelligent reasoning engine extracts equipment, issue symptom, category, and severity.
4. **Follow-Up Clarification**: FieldOS detects missing fields (e.g. operating status) and asks targeted questions in the technician's language.
5. **Spoken Confirmation**: Gnani Timbre TTS (`timbre-v2.5`) synthesizes audio playback confirming work order details.
6. **Supervisor Dispatch**: The work order appears on the Supervisor Command Center for technician assignment and lifecycle tracking.

---

## 2. System Architecture & Workflow

```mermaid
flowchart TD
    subgraph Mobile["Technician Mobile App (:3001)"]
        Mic["Microphone Input (Gujarati / Hindi / English)"]
        Review["Interactive Extraction Review"]
        Confirm["Spoken Confirmation Audio"]
    end

    subgraph Backend["FastAPI Backend (:8000)"]
        AudioTranscode["FFmpeg 16kHz PCM Transcoder"]
        Reasoning["Operational Intelligence Extractor"]
        WorkOrderEngine["Workflow & Work Order Engine"]
        AuthModule["JWT Security & Auth Roster"]
    end

    subgraph Speech["Gnani AI Services / Mock Fallback"]
        Prisma["Gnani Prisma STT"]
        Timbre["Gnani Timbre TTS"]
    end

    subgraph Storage["PostgreSQL Database"]
        DB[(Users, Technicians, Reports, WorkOrders)]
    end

    subgraph Dashboard["Supervisor Command Center (:3002)"]
        OpsOverview["Operational KPIs & Metrics"]
        Dispatch["Technician Roster & Assignment"]
        Analytics["Resolution Tracking"]
    end

    Mic -->|Audio Blob| AudioTranscode
    AudioTranscode -->|WAV PCM| Prisma
    Prisma -->|Transcription| Reasoning
    Reasoning -->|Structured Report| Review
    Review -->|Confirmed Report| WorkOrderEngine
    WorkOrderEngine -->|Persist| DB
    Reasoning -->|Confirmation Text| Timbre
    Timbre -->|Audio Playback| Confirm
    DB -->|Work Orders & Rosters| Dashboard
    Dispatch -->|Assign Tech| WorkOrderEngine
```

---

## 3. Core Modules & Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Mobile Frontend** | Next.js 14 + Tailwind CSS | Responsive technician voice recording & work-order tracking ([http://localhost:3001](http://localhost:3001)) |
| **Supervisor Dashboard** | Next.js 14 + Recharts | Command center for work-order dispatch, technician monitoring & analytics ([http://localhost:3002](http://localhost:3002)) |
| **Backend API** | FastAPI + Python 3.12 | Async REST API orchestration, JWT authentication, and rate limiting ([http://localhost:8000](http://localhost:8000)) |
| **Speech-to-Text (STT)** | Gnani Prisma ASR (`prisma-v2.5`) | Indic multilingual transcription (Gujarati, Hindi, English, Hinglish) |
| **Text-to-Speech (TTS)** | Gnani Timbre TTS (`timbre-v2.5`) | Voice confirmation & conversational audio feedback |
| **Operational Intelligence** | Heuristic Extractor & Rule Engine | Structured entity extraction, severity assessment, missing field clarification |
| **Database** | PostgreSQL 15+ (Psycopg 3) / SQLite dev fallback | Relational storage for users, technicians, reports, and work orders |
| **Containerization** | Docker & Docker Compose | Multi-service orchestration and production deployment |

---

## 4. Project Structure

```text
FieldOS/
├── backend/                     # FastAPI + Python 3.12+ backend
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint & rate limiting
│   │   ├── api/v1/endpoints/    # REST API routes (auth, voice, reports, work-orders, technicians)
│   │   ├── services/            # Speech (Gnani, Mock), Intelligence (Extractor), Workflow
│   │   ├── models/              # SQLAlchemy DB models & Pydantic schemas
│   │   ├── core/                # Configuration, JWT security & CORS
│   │   └── db/                  # Session management & demo data seeding
│   ├── alembic/                 # Database migrations (Psycopg 3)
│   ├── tests/                   # Pytest test suite (auth, speech, intelligence, workflow)
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── mobile/                  # Next.js 14 technician voice & reporting interface (Port 3001)
│   ├── dashboard/               # Next.js 14 supervisor command center (Port 3002)
│   ├── shared/                  # Shared TypeScript types, API client, UI primitives & styles
│   ├── package.json             # NPM workspaces configuration
│   └── tailwind.preset.js
├── ai-engine/                   # Extensible standalone reasoning service
├── docs/
│   └── "Proposed Solution .md"  # Challenge design specification & scenario roadmap
├── docker-compose.yml           # Multi-container orchestration (PostgreSQL + FastAPI)
└── README.md
```

---

## 5. Getting Started

### Prerequisites
- Python 3.10+ (Python 3.12 recommended; `uv` supported)
- Node.js 18+ & npm 9+
- PostgreSQL 15+ (or automatic local SQLite fallback for dev)
- `ffmpeg` (for audio transcoding to 16kHz mono PCM WAV)
- Gnani AI API credentials (`GNANI_API_KEY`) or `SPEECH_PROVIDER=mock` for offline evaluation

---

### Backend Setup

```bash
cd backend

# 1. Copy sample environment and configure credentials
cp .env.example .env

# 2. Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# (or with uv: uv pip install -r requirements.txt)

# 3. Apply database migrations
alembic upgrade head

# 4. Start the API server (runs on http://localhost:8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Frontend Setup

The frontend is structured as an npm monorepo with workspaces (`shared`, `dashboard`, `mobile`).

```bash
cd frontend

# Install all workspace dependencies
npm install

# Start both applications concurrently
npm run dev
```

- **Technician Mobile App**: [http://localhost:3001](http://localhost:3001)
- **Supervisor Command Center**: [http://localhost:3002](http://localhost:3002)

To launch an individual app:
- Technician Mobile: `npm run dev:mobile` (Port 3001)
- Supervisor Dashboard: `npm run dev:dashboard` (Port 3002)

---

### 🧪 Offline / Demo Evaluation Mode (No API Keys Needed)

If you are evaluating without an active Gnani API key, FieldOS includes a built-in mock speech service and one-click sample scenarios:

1. In `backend/.env`, set:
   ```env
   SPEECH_PROVIDER=mock
   ```
2. In the mobile interface at [http://localhost:3001/record](http://localhost:3001/record), click any of the **Quick Sample Scenarios** (*Gujarati Overheating*, *Hindi Vibration*, *Hinglish Inspection*, *English Anomaly*) to instantly test speech processing, intelligence extraction, and work order creation.

---

### Demo Accounts

The backend automatically seeds demo accounts on startup (password: `demo1234`):

| Email | Role | Default Language | Portal Access |
|---|---|---|---|
| `tech.demo@fieldos.ai` | Technician | Hinglish | Mobile App (`:3001`) & Dashboard (`:3002`) |
| `supervisor.demo@fieldos.ai` | Supervisor | English | Supervisor Dashboard (`:3002`) |

Log in to either app at `/login`.

---

### Run with Docker Compose

To start PostgreSQL and the FastAPI backend in synchronized containers:

```bash
docker-compose up --build
```

The container automatically runs `alembic upgrade head` before serving traffic on port 8000.

---

## 6. API Reference

Interactive OpenAPI documentation is hosted at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status and database connectivity |
| `POST` | `/api/v1/auth/login` | Authenticate user and receive JWT bearer token |
| `POST` | `/api/v1/auth/register` | Register a new technician or supervisor account |
| `POST` | `/api/v1/voice/transcribe` | Transcribe voice recording via Gnani Prisma and extract structured data |
| `POST` | `/api/v1/voice/tts` | Synthesize confirmation audio using Gnani Timbre |
| `POST` | `/api/v1/voice/extract` | Heuristic / LLM operational intelligence extraction from text |
| `GET` | `/api/v1/reports` | List submitted field reports with pagination and filtering |
| `POST` | `/api/v1/reports` | Create new report and automatically link a work order |
| `GET` | `/api/v1/work-orders` | Query work orders with search, priority, and status filters |
| `POST` | `/api/v1/work-orders/{id}/assign` | Assign a work order to a technician |
| `PATCH` | `/api/v1/work-orders/{id}/status` | Transition status (`in_progress`, `resolved`, `cancelled`) |
| `GET` | `/api/v1/technicians` | Fetch technician roster with availability status |

---

## 7. Verification & Testing

### Running Backend Tests

Run all 26 unit and integration tests with `pytest`:

```bash
cd backend
source .venv/bin/activate
pytest -v
```

Test suite coverage:
- `tests/test_auth.py` — JWT authentication, registration, password hashing
- `tests/test_gnani_speech.py` — Gnani Prisma STT / Timbre TTS request handling & PCM transcoding
- `tests/test_voice_intelligence.py` — Multilingual extraction (Gujarati/Hindi/English) and clarification synthesis
- `tests/test_work_order.py` — Work order lifecycle, technician assignment, status updates
- `tests/test_main.py` — Health check and API routing

### Running Frontend Validation

```bash
cd frontend
# TypeScript type check across all workspaces
npx tsc -b shared dashboard mobile
```

---

## 8. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://dhairya:dhairya@localhost:5432/fieldos` | PostgreSQL connection string using Psycopg 3 |
| `GNANI_API_KEY` | `""` | Gnani AI API token for Prisma ASR and Timbre TTS |
| `GNANI_BASE_URL` | `https://api.vachana.ai` | Base URL for Gnani AI endpoints |
| `GNANI_TTS_VOICE` | `Pranav` | Timbre voice identifier |
| `GNANI_TTS_MODEL` | `timbre-v2.5` | Timbre model version |
| `GNANI_STT_MODEL` | `prisma-v2.5` | Prisma model version |
| `SPEECH_PROVIDER` | `gnani` | `gnani` for live AI, or `mock` for deterministic offline testing |
| `SECRET_KEY` | `dev-secret-change-me` | JWT HMAC secret key (≥32 chars required in production) |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Session token validity duration |
| `CORS_ORIGINS` | `http://localhost:3001,http://localhost:3002` | Permitted client origins |
| `ALLOW_SQLITE_FALLBACK` | `true` | Dev-only fallback to SQLite if PostgreSQL is unreachable |
| `SEED_DEMO_DATA` | `true` | Automatically populate demo accounts & technician roster on startup |
| `MAX_AUDIO_BYTES` | `10485760` | Maximum allowed audio upload size (10 MB) |
| `VOICE_RATE_LIMIT_PER_MINUTE` | `60` | In-memory sliding window rate limiter for voice routes |

---

## 9. Production & Security Checklist

1. Set `APP_ENV=production`.
2. Generate a unique secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
3. Set `CORS_ORIGINS` to production domains (wildcard `*` is explicitly disallowed).
4. Enforce `ALLOW_SQLITE_FALLBACK=false` and `SEED_DEMO_DATA=false`.
5. Run `alembic upgrade head` before starting the API.
6. Connect to managed PostgreSQL with automatic backups.

---

## 10. Troubleshooting & FAQ

| Issue | Cause | Resolution |
|---|---|---|
| **Microphone blocked in browser** | Browser permissions or HTTP origin | Allow microphone in site permissions, or use HTTPS / localhost. You can also click any "Quick Sample Scenario" chip to test without a microphone. |
| **Audio transcoding warning** | `ffmpeg` is not installed | Install `ffmpeg` via package manager (`sudo apt install ffmpeg` or `brew install ffmpeg`). |
| **PostgreSQL connection refused** | Database server not running | Start PostgreSQL (`docker-compose up postgres` or system service). If `ALLOW_SQLITE_FALLBACK=true`, the backend will fallback to local SQLite for development. |
| **Speech service 502 / key error** | Gnani quota or invalid API key | Set `SPEECH_PROVIDER=mock` in `backend/.env` for offline deterministic testing. |

---

## 11. License

MIT
