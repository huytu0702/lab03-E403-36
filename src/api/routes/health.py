from fastapi import APIRouter

from src.db.session import is_database_available

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck():
    db_available = is_database_available(force_refresh=True)
    return {
        "status": "ok",
        "database": {
            "available": db_available,
            "mode": "postgres" if db_available else "fallback-seed",
        },
    }
