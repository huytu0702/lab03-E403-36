from fastapi import APIRouter, HTTPException

from src.telemetry.trace_store import trace_store

router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("/{trace_id}")
def get_trace(trace_id: str):
    try:
        return trace_store.load(trace_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Trace not found") from exc
