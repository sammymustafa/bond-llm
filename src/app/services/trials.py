
from sqlalchemy import text
from ..data.ctgov_ingest import fetch_trials, upsert_trials

def refresh_trials_if_needed(session, force=False):
    n = session.execute(text("SELECT count(*) FROM trials")).scalar_one()
    if n == 0 or force:
        trials = fetch_trials(cond="lymphoma", country="United States", max_pages=1)
        upsert_trials(session, trials)
