from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import os
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_NAME = os.getenv("DB_NAME", "jobs")
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, poolclass=NullPool)
def execute(query: str, params: dict | None = None):
    with engine.begin() as conn:
        return conn.execute(text(query), params or {})
def fetchall(query: str, params: dict | None = None):
    with engine.begin() as conn:
        res = conn.execute(text(query), params or {})
        return [dict(r._mapping) for r in res]
def fetchone(query: str, params: dict | None = None):
    with engine.begin() as conn:
        res = conn.execute(text(query), params or {})
        row = res.fetchone()
        return dict(row._mapping) if row else None
