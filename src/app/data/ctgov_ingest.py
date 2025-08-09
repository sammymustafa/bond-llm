
import json
import requests, time
from sqlalchemy import text
from ..config import CTGOV_BASE_URL, DEFAULT_STATUSES
from .embeddings import embed_texts

def fetch_trials(cond=None, terms=None, country=None, state=None, statuses=None, page_size=100, max_pages=1):
    statuses = statuses or DEFAULT_STATUSES
    params_base = {
        "pageSize": page_size,
        "countTotal": "true",
        "filter.overallStatus": ",".join(statuses)
    }
    if cond: params_base["query.cond"] = cond
    if terms: params_base["query.term"] = terms
    if country and state:
        params_base["query.locn"] = f"{state}, {country}"
    elif country:
        params_base["query.locn"] = country

    trials, page_token = [], None
    for _ in range(max_pages):
        params = dict(params_base)
        if page_token: params["pageToken"] = page_token
        r = requests.get(f"{CTGOV_BASE_URL}/studies", params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        trials.extend(data.get("studies", []))
        page_token = data.get("nextPageToken")
        if not page_token: break
        time.sleep(0.2)
    return trials

def _trial_text(t):
    ps = t.get("protocolSection", {})
    ident = ps.get("identificationModule", {})
    nct_id = ident.get("nctId", "")
    title = ident.get("briefTitle", "") or ident.get("officialTitle", "")
    conditions = ", ".join((ps.get("conditionsModule", {}) or {}).get("conditions", []) or [])
    elig = ps.get("eligibilityModule", {}) or {}
    criteria = elig.get("eligibilityCriteria", "") or ""
    text_blob = f"{title}. Conditions: {conditions}. Eligibility: {criteria}"
    return nct_id, title, conditions, elig, text_blob

def upsert_trials(session, trials):
    if not trials:
        return
    batches = 200
    for i in range(0, len(trials), batches):
        chunk = trials[i:i+batches]
        vectors_text, rows = [], []
        for t in chunk:
            nct_id, title, conditions, elig, text_blob = _trial_text(t)
            if not nct_id:
                continue
            vectors_text.append(text_blob)
            rows.append((nct_id, title, conditions, elig, t))
        if not rows:
            continue
        vecs = embed_texts(vectors_text)
        for (nct_id, title, conditions, elig, payload), emb in zip(rows, vecs):
            session.execute(text("""
            INSERT INTO trials (nct_id, title, conditions, eligibility, locations, payload, embedding)
            VALUES (:nct_id, :title, :conditions, :eligibility, :locations, :payload, :embedding)
            ON CONFLICT (nct_id) DO UPDATE SET
              title = EXCLUDED.title,
              conditions = EXCLUDED.conditions,
              eligibility = EXCLUDED.eligibility,
              locations = EXCLUDED.locations,
              payload = EXCLUDED.payload,
              embedding = EXCLUDED.embedding
            """),
            {
                "nct_id": nct_id,
                "title": title,
                "conditions": conditions,
                # Serialize dicts to JSON strings so psycopg adapts them to JSONB
                "eligibility": json.dumps(elig or {}),
                "locations": json.dumps(payload.get("protocolSection", {}).get("contactsLocationsModule", {}) or {}),
                "payload": json.dumps(payload or {}),
                "embedding": list(emb)
            })
        session.commit()