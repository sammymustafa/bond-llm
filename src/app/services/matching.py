from sqlalchemy import text
from rapidfuzz import fuzz
import numpy as np

from ..data.embeddings import embed_texts
from ..data.patient_extract import build_patient_profile, summarize_profile
from ..llm.llm_client import generate
from ..llm.prompts import SYSTEM_MATCH, build_match_prompt


def _compute_score(profile: dict, eligibility_text: str):
    """
    Simple weighted scorer + list of ambiguous/missing items.
    """
    score = 0.0
    breakdown = {}
    uncertain = []

    # Diagnosis keyword fit
    diag = (profile.get("diagnosis_hint") or "").strip()
    if diag:
        dmatch = fuzz.partial_ratio(diag.lower(), (eligibility_text or "").lower())
        s = dmatch / 100 * 0.25
        breakdown["diagnosis"] = round(s, 3)
        score += s
    else:
        uncertain.append("diagnosis")

    # ECOG
    ecog = profile.get("ecog")
    if ecog is not None:
        if "ecog" in (eligibility_text or "").lower():
            if ecog in (0, 1):
                s = 0.15
            elif ecog == 2:
                s = 0.08
            else:
                s = 0.0
        else:
            s = 0.05  # soft credit if eligibility doesn't mention ECOG explicitly
        breakdown["ecog"] = round(s, 3)
        score += s
    else:
        uncertain.append("ECOG")

    # Biomarkers
    bms = profile.get("biomarkers") or []
    if bms:
        hits = sum(1 for b in bms if b.lower() in (eligibility_text or "").lower())
        s = min(0.2, 0.07 * hits)
        breakdown["biomarkers"] = round(s, 3)
        score += s

    # Age (very naive adult threshold for demo)
    if profile.get("age") is not None:
        s = 0.1 if profile["age"] >= 18 else 0.0
        breakdown["age"] = round(s, 3)
        score += s
    else:
        uncertain.append("age")

    # Gender (light credit when mentioned)
    if profile.get("gender"):
        if any(x in (eligibility_text or "").lower() for x in ["female", "women", "male", "men"]):
            s = 0.05
        else:
            s = 0.03
        breakdown["gender"] = round(s, 3)
        score += s

    # Fuzzy text fit with a compact patient summary
    fit = fuzz.token_set_ratio(
        summarize_profile(profile).lower(), (eligibility_text or "").lower()
    ) / 100.0
    s = 0.2 * fit
    breakdown["text_fit"] = round(s, 3)
    score += s

    score = min(1.0, score)
    return round(score, 3), breakdown, sorted(set(uncertain))


def match_for_patient_bundle(
    session,
    bundle: dict,
    notes: str,
    top_k: int = 10,
    cond_hint: str | None = None,
    country: str | None = "United States",
):
    """
    Build a patient profile, embed it, vector-retrieve candidate trials, score, and (optionally) LLM-rationalize.
    """
    profile = build_patient_profile(bundle, notes)
    patient_summary = summarize_profile(profile)

    # Embed summary -> vector literal for pgvector
    vec = embed_texts([patient_summary])[0]  # np.array (384,)
    vec_list = vec.tolist() if isinstance(vec, np.ndarray) else list(vec)
    vec_lit = "[" + ",".join(str(float(x)) for x in vec_list) + "]"

    # Vector similarity using pgvector's <=> operator; cast parameter to vector
    q = session.execute(
        text(
            """
        SELECT nct_id, title, eligibility, 1 - (embedding <=> (:v)::vector) AS sim
        FROM trials
        ORDER BY embedding <=> (:v)::vector
        LIMIT :k
        """
        ),
        {"v": vec_lit, "k": top_k},
    )
    rows = q.fetchall()

    results = []
    for nct_id, title, eligibility, sim in rows:
        elig_text = ""
        if isinstance(eligibility, dict):
            elig_text = eligibility.get("eligibilityCriteria", "") or ""

        score, breakdown, uncertain = _compute_score(profile, elig_text)

        # Try to get an LLM rationale if local model is available
        llm_expl = None
        try:
            messages = [
                {"role": "system", "content": SYSTEM_MATCH},
                {
                    "role": "user",
                    "content": build_match_prompt(
                        patient_summary, title or "", elig_text, nct_id
                    ),
                },
            ]
            llm_expl = generate(messages)
        except Exception:
            llm_expl = None  # keep going even if LLM isn't up

        results.append(
            {
                "nct_id": nct_id,
                "title": title,
                "score": score,
                "score_breakdown": breakdown,
                "uncertain_criteria": uncertain,
                "vector_similarity": round(float(sim or 0.0), 3),
                "llm_explanation": llm_expl,
            }
        )

    return results

