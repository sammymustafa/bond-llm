
import os
from dotenv import load_dotenv
load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "bond_trials")
POSTGRES_USER = os.getenv("POSTGRES_USER", "bond_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "devpassword")
DATABASE_URL = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:instruct")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

CTGOV_BASE_URL = os.getenv("CTGOV_BASE_URL", "https://beta-ut.clinicaltrials.gov/api/v2")
DEFAULT_STATUSES = [s.strip() for s in os.getenv("DEFAULT_STATUSES", "RECRUITING,NOT_YET_RECRUITING").split(",") if s.strip()]
