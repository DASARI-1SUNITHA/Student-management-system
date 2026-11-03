import os

from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

url = settings.sqlalchemy_url
is_sqlite = url.startswith("sqlite")

kwargs: dict = {}
if is_sqlite:
    kwargs["connect_args"] = {"check_same_thread": False}
else:
    kwargs["connect_args"] = {"prepare_threshold": None}  # required for Neon's PgBouncer pooler
    if os.environ.get("VERCEL"):
        kwargs["poolclass"] = NullPool  # serverless: open/close per request; the Neon pooler shares connections
    else:
        kwargs.update(pool_pre_ping=True, pool_recycle=300)

engine = create_engine(url, **kwargs)

if is_sqlite:  # only used by the local smoke test

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
