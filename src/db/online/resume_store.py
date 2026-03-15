"""
候選人履歷儲存層（Supabase online 版）。
函式 API 與 local 版完全相同。
每個 user 對應一筆 resumes 記錄。
"""
__all__ = ["load", "save", "update"]

import copy
from datetime import datetime, timezone

from src.db.context import current_user_id
from src.db.online.client import get_client

_EMPTY: dict = {
    "basic_info": {
        "name": "",
        "location": "",
        "languages": [],
        "hard_skills": [],
        "soft_skills": [],
    },
    "professional_summary": "",
    "interview_hooks": [],
    "work_experience": [],
    "education": [],
    "status": "draft",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load() -> dict:
    uid = current_user_id.get()
    sb = get_client()
    res = sb.table("resumes").select("*").eq("user_id", uid).execute()
    if not res.data:
        return copy.deepcopy(_EMPTY)
    row = res.data[0]
    return {
        "basic_info": row["basic_info"],
        "professional_summary": row["professional_summary"],
        "interview_hooks": row["interview_hooks"],
        "work_experience": row["work_experience"],
        "education": row["education"],
        "status": row["status"],
    }


def save(data: dict) -> dict:
    uid = current_user_id.get()
    sb = get_client()
    # ensure user exists
    sb.table("users").upsert({"id": uid}, on_conflict="id").execute()
    now = _now()
    record = {
        "user_id": uid,
        "basic_info": data.get("basic_info", {}),
        "professional_summary": data.get("professional_summary", ""),
        "interview_hooks": data.get("interview_hooks", []),
        "work_experience": data.get("work_experience", []),
        "education": data.get("education", []),
        "status": data.get("status", "draft"),
        "updated_at": now,
    }
    sb.table("resumes").upsert(record, on_conflict="user_id").execute()
    return data


def update(fields: dict) -> dict:
    current = load()
    current.update(fields)
    return save(current)
