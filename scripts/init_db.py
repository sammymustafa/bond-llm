
from sqlalchemy import create_engine, text
from src.app.config import DATABASE_URL

def main():
    engine = create_engine(DATABASE_URL, future=True)
    with engine.connect() as con:
        con.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        con.execute(text("""
        CREATE TABLE IF NOT EXISTS trials (
            nct_id text primary key,
            title text,
            conditions text,
            eligibility jsonb,
            locations jsonb,
            payload jsonb,
            embedding vector(384)
        )
        """))
        con.execute(text("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id text primary key,
            payload jsonb,
            embedding vector(384)
        )
        """))
        con.commit()
    print("DB initialized")

if __name__ == "__main__":
    main()
