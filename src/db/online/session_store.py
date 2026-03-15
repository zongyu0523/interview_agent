"""
Session 元資料儲存層（Supabase online 版）。
函式 API 與 local 版完全相同。

注意：本地 company_id ↔ DB application_id
回傳 dict 維持 company_id key 供 routes 使用。
"""
__all__ = ["list_sessions", "create_session", "get_session", "update_status", "delete_session", "get_tasks", "complete_current_task", "delete_sessions_by_company"]

import uuid
from datetime import datetime, timezone

from src.db.context import current_user_id
from src.db.online.client import get_client


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_session_id() -> str:
    date_str = datetime.now().strftime("%y%m%d")
    random_str = uuid.uuid4().hex[:6]
    return f"web_{date_str}_{random_str}"


def _row_to_session(row: dict, tasks: list[dict]) -> dict:
    """將 DB row 轉換成與 local 版相同的 dict 結構。"""
    return {
        "id": row["id"],
        "company_id": row["application_id"],  # 維持 company_id key
        "type": row["type"],
        "mode": row["mode"],
        "status": row["status"],
        "interviewer_name": row["interviewer_name"],
        "additional_notes": row["additional_notes"],
        "must_ask_questions": row["must_ask_questions"],
        "tasks": tasks,
        "current_task_index": row["current_task_index"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _load_tasks(session_id: str) -> list[dict]:
    sb = get_client()
    res = sb.table("session_tasks").select("*").eq("session_id", session_id).order("position").execute()
    return [
        {
            "topic": t["topic"],
            "instruction": t["instruction"],
            "status": t["status"],
            "score": t["score"],
            "evaluation": t["evaluation"],
        }
        for t in (res.data or [])
    ]


def list_sessions(company_id: str) -> list[dict]:
    sb = get_client()
    res = (
        sb.table("sessions")
        .select("*")
        .eq("application_id", company_id)
        .order("created_at", desc=True)
        .execute()
    )
    sessions = []
    for row in (res.data or []):
        tasks = _load_tasks(row["id"])
        sessions.append(_row_to_session(row, tasks))
    return sessions


def create_session(
    company_id: str,
    interview_type: str,
    mode: str,
    interviewer_name: str | None = None,
    additional_notes: str | None = None,
    must_ask_questions: list[str] | None = None,
    tasks: list[dict] | None = None,
) -> dict:
    uid = current_user_id.get()
    sb = get_client()
    now = _now()
    session_id = _make_session_id()
    task_list = tasks or []

    # 第一題標記 in_progress
    if task_list:
        task_list[0]["status"] = "in_progress"

    row = {
        "id": session_id,
        "user_id": uid,
        "application_id": company_id,
        "type": interview_type,
        "mode": mode,
        "status": "created",
        "interviewer_name": interviewer_name or "",
        "additional_notes": additional_notes or "",
        "must_ask_questions": must_ask_questions or [],
        "current_task_index": 0,
        "created_at": now,
        "updated_at": now,
    }
    sb.table("sessions").insert(row).execute()

    # 批次插入 tasks
    if task_list:
        task_rows = [
            {
                "session_id": session_id,
                "position": i,
                "topic": t.get("topic", ""),
                "instruction": t.get("instruction", ""),
                "status": t.get("status", "pending"),
                "score": t.get("score"),
                "evaluation": t.get("evaluation"),
            }
            for i, t in enumerate(task_list)
        ]
        sb.table("session_tasks").insert(task_rows).execute()

    return _row_to_session(row, task_list)


def get_session(session_id: str) -> dict | None:
    sb = get_client()
    res = sb.table("sessions").select("*").eq("id", session_id).execute()
    if not res.data:
        return None
    row = res.data[0]
    tasks = _load_tasks(session_id)
    return _row_to_session(row, tasks)


def update_status(session_id: str, status: str) -> dict | None:
    sb = get_client()
    res = (
        sb.table("sessions")
        .update({"status": status, "updated_at": _now()})
        .eq("id", session_id)
        .execute()
    )
    if not res.data:
        return None
    tasks = _load_tasks(session_id)
    return _row_to_session(res.data[0], tasks)


def delete_session(session_id: str) -> bool:
    uid = current_user_id.get()
    sb = get_client()
    res = sb.table("sessions").delete().eq("id", session_id).eq("user_id", uid).execute()
    return bool(res.data)


def get_tasks(session_id: str) -> list[dict]:
    return _load_tasks(session_id)


def complete_current_task(session_id: str, score: int, evaluation: str) -> bool:
    """
    將當前 in_progress 任務標記為 completed，
    並把下一題設為 in_progress。
    回傳 True 表示還有下一題，False 表示全部結束。
    """
    sb = get_client()

    # 取得目前 session
    res = sb.table("sessions").select("current_task_index").eq("id", session_id).execute()
    if not res.data:
        return False
    idx = res.data[0]["current_task_index"]

    # 計算 task 總數
    count_res = sb.table("session_tasks").select("id", count="exact").eq("session_id", session_id).execute()
    total = count_res.count or 0

    if idx >= total:
        return False

    # 更新當前 task
    sb.table("session_tasks").update({
        "status": "completed",
        "score": score,
        "evaluation": evaluation,
    }).eq("session_id", session_id).eq("position", idx).execute()

    next_idx = idx + 1
    if next_idx < total:
        sb.table("session_tasks").update({"status": "in_progress"}).eq("session_id", session_id).eq("position", next_idx).execute()

    sb.table("sessions").update({
        "current_task_index": next_idx,
        "updated_at": _now(),
    }).eq("id", session_id).execute()

    return next_idx < total


def delete_sessions_by_company(company_id: str) -> int:
    sb = get_client()
    res = sb.table("sessions").select("id").eq("application_id", company_id).execute()
    count = len(res.data or [])
    if count:
        sb.table("sessions").delete().eq("application_id", company_id).execute()
    return count
