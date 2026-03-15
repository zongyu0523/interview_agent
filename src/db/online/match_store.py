"""
匹配度分析儲存層（Supabase online 版）。
函式 API 與 local 版完全相同。
"""
__all__ = ["get", "save", "delete"]

from datetime import datetime, timezone

from src.db.online.client import get_client


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get(application_id: str) -> dict | None:
    sb = get_client()
    res = sb.table("match_analyses").select("*").eq("application_id", application_id).execute()
    if not res.data:
        return None
    row = res.data[0]
    return {
        "score": row["score"],
        "label": row["label"],
        "score_reason": row["score_reason"],
        "analyzed_at": row["analyzed_at"],
    }


def save(application_id: str, data: dict) -> dict:
    sb = get_client()
    now = _now()
    record = {
        "application_id": application_id,
        "score": data["score"],
        "label": data["label"],
        "score_reason": data["score_reason"],
        "analyzed_at": now,
    }
    sb.table("match_analyses").upsert(record, on_conflict="application_id").execute()
    return {**data, "analyzed_at": now}


def delete(application_id: str) -> None:
    sb = get_client()
    sb.table("match_analyses").delete().eq("application_id", application_id).execute()
