from fastapi import APIRouter, HTTPException

from src.db import session_store

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def list_sessions(status: str | None = None, company_id: str | None = None):
    """列出面試 session，可用 ?status=active 或 ?company_id=xxx 篩選。"""
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id query param is required")
        
    sessions = session_store.list_sessions(company_id)
    if status:
        sessions = [s for s in sessions if s.get("status") == status]
    return sessions


@router.get("/{session_id}")
def get_session(session_id: str):
    """取得單一 session 的後設資料。"""
    record = session_store.get_session(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return record
