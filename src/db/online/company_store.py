"""
公司資訊儲存層（Supabase online 版）。
函式 API 與 local 版完全相同。
"""
__all__ = ["list_applications", "create_application", "get_application", "delete_application"]

from datetime import datetime, timezone

from src.db.context import current_user_id
from src.db.online.client import get_client


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_user(uid: str) -> None:
    """確保 users 表中有此 user，不存在則插入。"""
    sb = get_client()
    sb.table("users").upsert({"id": uid}, on_conflict="id").execute()


def list_applications() -> list[dict]:
    uid = current_user_id.get()
    sb = get_client()
    res = sb.table("applications").select("*").eq("user_id", uid).order("created_at", desc=True).execute()
    return res.data or []


def create_application(
    company_name: str,
    job_title: str,
    job_description: str | None = None,
    industry: str | None = None,
    job_grade: str | None = None,
) -> dict:
    uid = current_user_id.get()
    _ensure_user(uid)
    sb = get_client()
    now = _now()
    record = {
        "user_id": uid,
        "company_name": company_name,
        "job_title": job_title,
        "job_description": job_description or "",
        "industry": industry or "",
        "job_grade": job_grade or "",
        "created_at": now,
        "updated_at": now,
    }
    res = sb.table("applications").insert(record).execute()
    return res.data[0]


def get_application(application_id: str) -> dict | None:
    sb = get_client()
    res = sb.table("applications").select("*").eq("id", application_id).execute()
    if res.data:
        return res.data[0]
    return None


def delete_application(application_id: str) -> bool:
    uid = current_user_id.get()
    sb = get_client()
    res = sb.table("applications").delete().eq("id", application_id).eq("user_id", uid).execute()
    return bool(res.data)
