
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ..config import DATABASE_URL

_engine = None
_Session = None

def db_init():
    global _engine, _Session
    _engine = create_engine(DATABASE_URL, future=True)
    with _engine.connect() as con:
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
    _Session = sessionmaker(bind=_engine, future=True)

def get_session():
    if _Session is None:
        db_init()
    return _Session()
