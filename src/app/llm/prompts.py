
SYSTEM_MATCH = """
You are a clinical trial matching copilot for coordinators.
Return compact JSON with keys:
- nct_id
- rationale: 1-2 sentences linked to inclusion/exclusion
- clarify: array of missing/uncertain criteria needed to confirm eligibility
Do not include PHI.
"""

def build_match_prompt(patient_summary, trial_title, eligibility_text, nct_id):
    user = f"""
Patient summary:
{patient_summary}

Trial {nct_id}: {trial_title}

Eligibility:
{eligibility_text}

Task:
Assess fit. Give a short rationale tied to criteria and list items to clarify.
Return JSON with nct_id, rationale, clarify.
"""
    return user
