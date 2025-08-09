from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .services.db import db_init, get_session
from .services.trials import refresh_trials_if_needed
from .services.matching import match_for_patient_bundle
from .data.patient_extract import summarize_profile, build_patient_profile
from .data.redact import scrub

app = FastAPI(title="Bond Health Trial Matcher (beta-ut)")
templates = Jinja2Templates(directory="src/app/templates")


class MatchRequest(BaseModel):
    patient_fhir: dict
    notes: str | None = None
    top_k: int = 10
    cond_hint: str | None = None
    country: str | None = "United States"


@app.on_event("startup")
def on_startup():
    db_init()


@app.get("/", response_class=HTMLResponse)
def home():
    # simple landing page with a quick link to an example report
    return """<html><body style="font-family:Inter,system-ui;margin:40px">
    <h2>Bond Trial Matcher</h2>
    <p>Try the example report: <a href="/report/patient_01" style="color:#2563eb">/report/patient_01</a></p>
    </body></html>"""


@app.get("/report/{patient_id}", response_class=HTMLResponse)
def report_example(request: Request, patient_id: str):
    """
    Renders a nice HTML report for one of the bundled example patients:
      e.g. /report/patient_01 (looks up examples/patients/patient_01.json + notes)
    """
    import json
    from pathlib import Path

    base = Path("examples")
    pfile = base / "patients" / f"{patient_id}.json"
    nfile = base / "notes" / f"{patient_id}.txt"
    if not pfile.exists():
        return HTMLResponse(f"<h3>Patient {patient_id} not found</h3>", status_code=404)

    patient_fhir = json.loads(pfile.read_text())
    notes = nfile.read_text() if nfile.exists() else ""

    with get_session() as s:
        refresh_trials_if_needed(s)
        matches = match_for_patient_bundle(s, patient_fhir, notes, top_k=10)

    profile = build_patient_profile(patient_fhir, notes)
    patient_summary = summarize_profile(profile)
    notes_preview = scrub(notes)[:800]

    return templates.TemplateResponse(
        "report.html",
        {
            "request": request,
            "patient_summary": patient_summary,
            "notes_preview": notes_preview,
            "matches": matches,
        },
    )


@app.post("/match/patient")
def match_patient(req: MatchRequest):
    """
    JSON API for programmatic use.
    Body: { "patient_fhir": {...}, "notes": "...", "top_k": 10, "cond_hint": null, "country": "United States" }
    """
    try:
        with get_session() as s:
            refresh_trials_if_needed(s)
            results = match_for_patient_bundle(
                s,
                req.patient_fhir,
                req.notes or "",
                top_k=req.top_k,
                cond_hint=req.cond_hint,
                country=req.country,
            )
        return {"matches": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

