# AI Academic Intelligence Operating System — FastAPI AI service

Separate **Python/FastAPI** service that sits next to the **Laravel 12** application. Laravel’s **question bank AI generation** calls this service when `AI_SERVICE_URL` is set (`AI_GENERATION_DRIVER=auto` or `fastapi`).

## Features (current)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness — `{ "status": "ok" }` |
| `POST` | `/generate-questions` | OpenAI-powered question generation |

Planned extensions (architecture is ready for new routers): `/mark-answer`, `/analyze-exam-fairness`, `/generate-revision-plan`, `/predict-performance-risk`, `/oral-examiner`.

## Requirements

- Python **3.11+**
- An [OpenAI](https://platform.openai.com/) API key

## Setup

```bash
cd ai-service

# Virtual environment
python -m venv .venv
# Windows:
# .venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

```bash
cp .env.example .env
# Edit .env — set OPENAI_API_KEY and optionally OPENAI_MODEL, CORS_ORIGINS
```

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Secret key for OpenAI |
| `OPENAI_MODEL` | Default `gpt-4o-mini` |
| `CORS_ORIGINS` | Comma-separated origins allowed to call this API (Laravel + Vite URLs) |

## Run (development)

From `ai-service/` with the virtual environment activated:

```bash
# Option A — uvicorn directly (port 8088 avoids clash with Laravel :8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8088
```

```bash
# Option B — helper script (expects .venv)
chmod +x start.sh
./start.sh
```

Interactive docs: **http://127.0.0.1:8088/docs**

## Test `/health`

```bash
curl -s http://127.0.0.1:8088/health
# {"status":"ok"}
```

## Test `/generate-questions`

```bash
curl -s -X POST http://127.0.0.1:8088/generate-questions \
  -H "Content-Type: application/json" \
  -d '{
    "course": "Database Systems",
    "topic": "Normalization",
    "difficulty": "medium",
    "question_type": "mcq",
    "number_of_questions": 3,
    "lecture_notes": "1NF: each cell is atomic. 2NF: no partial dependencies on composite keys. 3NF: no transitive dependencies on non-key attributes.",
    "learning_outcome": "Students can explain normal forms in their own words."
  }'
```

Optional fields: `lecture_notes` (grounding text; long notes are truncated server-side), `question_types` (round-robin mix), `question_type_offset` (for chunked calls), `learning_outcome`.

Supported `question_type` values: `mcq`, `fill_in`, `short_answer`, `theory`.

## Laravel integration

1. Set **`AI_SERVICE_URL`** in `laravel-app/.env` to the same host/port as Uvicorn (e.g. `http://127.0.0.1:8088`).
2. Use **`AI_GENERATION_DRIVER=auto`** (default) to prefer FastAPI when that URL is set, then fall back to `OPENAI_API_KEY` / `GEMINI_API_KEY` on Laravel. If every provider fails, the request returns an error (no offline stub questions).
3. Use **`AI_GENERATION_DRIVER=fastapi`** to require the microservice (no silent fallback to heuristic if the call fails).
4. The Python service needs **`OPENAI_API_KEY`** in `ai-service/.env` (Laravel’s key is not forwarded automatically).

CORS is pre-configured for typical local Laravel (`:8000`) and Vite (`:5173`) origins; add production domains to `CORS_ORIGINS` when deploying.

## Project layout

```
ai-service/
├── app/
│   ├── main.py                 # FastAPI app, CORS, lifespan
│   ├── config/settings.py      # Pydantic settings / env
│   ├── routers/
│   │   └── question_generation.py
│   ├── services/openai_service.py
│   ├── schemas/question_schema.py
│   ├── prompts/question_prompt.py
│   └── utils/
├── .env.example
├── .env                        # local only (gitignored)
├── requirements.txt
├── start.sh
└── README.md
```
