import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.config import get_settings


settings = get_settings()
engine_kwargs = {"future": True, "echo": False, "pool_pre_ping": True}
if settings.database_url.startswith("postgresql"):
    engine_kwargs["connect_args"] = {"connect_timeout": 2}

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
_db_status_cache = {"available": None, "checked_at": 0.0}


def is_database_available(force_refresh: bool = False, ttl_seconds: float = 15.0) -> bool:
    available = _db_status_cache["available"]
    now = time.monotonic()
    if not force_refresh and available is not None and (now - _db_status_cache["checked_at"]) < ttl_seconds:
        return bool(available)

    db = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        available = True
    except SQLAlchemyError:
        available = False
    finally:
        if db is not None:
            db.close()

    _db_status_cache["available"] = available
    _db_status_cache["checked_at"] = now
    return bool(available)
