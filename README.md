
# Bond Health — Open-weight LLM Clinical Trial Matcher (beta-ut API)

Matches synthetic patient EHRs to ClinicalTrials.gov trials using the **beta-ut API** (`https://beta-ut.clinicaltrials.gov/api/v2`). 
Parses structured and unstructured data, computes a **match score** with a **breakdown** and **uncertain criteria**, and optionally asks a **local open-weight LLM** for a concise rationale.

> For local evaluation only. Deploy to a compliant environment before handling PHI.

## Quick start

Prereqs
- Docker Desktop
- Python 3.10+
- Optional: [Ollama](https://ollama.com) with `llama3.1:instruct`

Setup
```bash
cp .env.example .env
docker compose up -d db

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m scripts.init_db
python -m scripts.load_ctgov --cond "Hodgkin Lymphoma" --country "United States" --max_pages 1

uvicorn src.app.main:app --reload
```

Test a patient
```bash
curl -X POST http://localhost:8000/match/patient   -H "Content-Type: application/json"   -d @examples/patients/patient_01.json
```

Add notes to the request:
```bash
curl -X POST http://localhost:8000/match/patient   -H "Content-Type: application/json"   -d '{"patient_fhir": '$(cat examples/patients/patient_01.json)',
       "notes": '$(python - <<'PY'
print(repr(open("examples/notes/patient_01.txt").read()))
PY
)'}'
```

## What it does
- Fetches trials via **beta-ut** `/api/v2/studies` with Search Areas: `query.cond`, `query.locn`, `filter.overallStatus`
- Builds embeddings with sentence-transformers and stores trial vectors in Postgres (pgvector)
- Extracts patient features from structured JSON and free-text notes
- Computes a weighted score and lists criteria that need clarification
- Calls a local open-weight LLM (if running) for a succinct rationale JSON

