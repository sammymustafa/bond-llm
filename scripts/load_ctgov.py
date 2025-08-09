
import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.config import DATABASE_URL
from src.app.data.ctgov_ingest import fetch_trials, upsert_trials

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cond", type=str, default="lymphoma")
    p.add_argument("--terms", type=str, default=None)
    p.add_argument("--country", type=str, default="United States")
    p.add_argument("--state", type=str, default=None)
    p.add_argument("--statuses", type=str, default="RECRUITING,NOT_YET_RECRUITING")
    p.add_argument("--page_size", type=int, default=100)
    p.add_argument("--max_pages", type=int, default=1)
    args = p.parse_args()

    statuses = [s.strip() for s in args.statuses.split(",") if s.strip()]
    engine = create_engine(DATABASE_URL, future=True)
    Session = sessionmaker(bind=engine, future=True)
    with Session() as s:
        trials = fetch_trials(cond=args.cond, terms=args.terms, country=args.country, state=args.state,
                              statuses=statuses, page_size=args.page_size, max_pages=args.max_pages)
        upsert_trials(s, trials)
    print(f"Loaded {len(trials)} trials")

if __name__ == "__main__":
    main()
