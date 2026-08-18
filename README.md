# Zomato AI Recommendation

Hybrid restaurant recommender: hard-filter a real Zomato catalog, then rank and explain with Groq. If the model is down or the key is missing, Phase 1 rule ranking still returns a usable list.

**Current milestone:** Phase 4 — Tablepick frontend (Next.js) wired to `/recommend`.

Docs: [problem statement](docs/problemStatement.md) · [architecture](docs/architecture.md) · [implementation plan](docs/implementation-plan.md) · [edge cases](docs/edge-case.md)

UI spec: `stitch_tablepick_ai_dining_guide/` (Find a table + Results). Restaurant photos are omitted in v1.

---

## Setup

Python 3.9+. From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Add a Groq key to `.env` (create one at [console.groq.com/keys](https://console.groq.com/keys)):

```bash
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=gsk_your_key_here
```

`GROQ_API_KEY` is preferred for Groq. `LLM_API_KEY` is accepted as a fallback. Without a key, `/recommend` still works using rule-based ranking (`source: fallback`).

Load the catalog once (Hugging Face or the offline fixture):

```bash
python -m src.data.ingest
# or: python -m src.data.ingest --source tests/fixtures/restaurants_sample.csv
python -m src.data.profile
```

The API **fails to start** if `data/processed/` is missing. Ingest first.

Frontend (Node 18+):

```bash
cd frontend
npm install
```

---

## Demo walkthrough

Fixed sample preference requests (Bangalore Italian mid-budget, multi-cuisine, free-text extras, empty state):

```bash
python -m src.demo
python -m src.demo --list
python -m src.demo --scenario bangalore-italian-medium
```

This uses the processed catalog. Groq ranks when a key is set; otherwise you still get rule-based cards.

In the UI, the empty-canvas pill loads **Indiranagar · Italian · medium · Romantic rooftop**.

---

## Run the API and UI

Two processes. LLM keys stay on the API; the browser only talks to Next.js (`localhost:3000`), which rewrites `/api/*` to FastAPI.

```bash
# terminal 1 — API
PYTHONPATH=. python3 -m uvicorn src.app.main:app --reload --port 8000
```

```bash
# terminal 2 — Tablepick (uses project-local Node at .tools/node if system Node is missing)
./scripts/dev-frontend.sh
```

Or, if Node 18+ is already on your PATH:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Both processes must be running; otherwise the browser shows “connection failed”.

Optional Streamlit (legacy): `streamlit run src/ui/app.py`

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Catalog status, LLM config, success/fallback/empty counters |
| `GET` | `/meta/filters` | Distinct neighbourhoods (`location` column), cities, cuisines, budget bounds for dropdowns |
| `POST` | `/recommend` | Ranked list with `source: llm` or `source: fallback` |

The Next.js app calls these as `/api/health`, `/api/meta/filters`, `/api/recommend`.

Example:

```bash
curl -s http://127.0.0.1:8000/recommend \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: demo-1' \
  -d '{
    "location": "Bangalore",
    "budget": "medium",
    "cuisine": ["Italian"],
    "min_rating": 4.0,
    "additional_preferences": "family-friendly",
    "top_k": 5
  }'
```

Invalid payloads return **400**. Missing catalog returns **503** on `/recommend` and `/meta/filters`. Hallucinated restaurant IDs are dropped. Timeouts or invalid JSON fall back to the Phase 1 scorer.

The Tablepick UI is driven from catalog chips/autocomplete (location + cuisine), with a demo preset, a results skeleton while Groq runs, gold AI quotes, and tips when nothing matches.

---

## How the pipeline works

**normalize → filter/score (15–30 candidates) → Groq rank/explain → ground IDs to the catalog → respond**

Structured fields (name, cuisine, rating, cost) always come from the catalog, not from free-form model text.

Logs include request id, filter-stage counts, relaxation events, LLM vs fallback, empty results, and latency (`filter_ms` / `llm_ms` / `total_ms`). Watch `/health` → `metrics` for fallback and empty-result rates during a demo.

Optional identical-request cache: set `RECOMMEND_CACHE_TTL_SECONDS=60` in `.env`.

---

## Budget bands

Cost is treated as **INR approximate cost for two** (dataset scale). Thresholds are configurable in `.env`:

| Band | Default |
|---|---|
| `low` | ≤ 500 |
| `medium` | 501–1500 |
| `high` | > 1500 |
| `unknown` | missing / unparseable cost |

If too few restaurants match, the engine may include an **adjacent** budget band and records that in `meta.relaxations_applied` (also logged).

---

## Tests

```bash
pytest
```

CI uses `tests/fixtures/restaurants_sample.csv` and **mocked Groq responses** (no live API, no Hugging Face download).

---

## Project layout

```text
src/config.py              settings from .env (Groq key, model, caps, cache TTL, CORS)
src/observability.py       request id, counters, short-TTL cache
src/data/                  ingest, clean, catalog, facets for dropdowns
src/preferences/           normalize user input + keyword dictionary
src/filtering/             hard filters + pre-rank scorer + empty-state tips
src/llm/                   prompts, Groq client, JSON parser
src/engine/recommend.py    orchestrator (filter → LLM → fallback)
src/demo.py                fixed walkthrough scenarios
src/app/main.py            FastAPI: /health, /meta/filters, /recommend
src/ui/app.py              legacy Streamlit
frontend/                  Tablepick Next.js app (Phase 4)
data/processed/            parquet cache (gitignored)
tests/fixtures/            offline sample CSV
stitch_tablepick_ai_dining_guide/  Stitch visual reference
```
