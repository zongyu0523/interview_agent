"""
Session 元資料儲存層。
每個 session 一個 .meta.json，存在 data/sessions/{session_id}.meta.json。
對話歷史另存 data/sessions/{session_id}.jsonl（由 src.core.memory 負責）。

手動操作：
  - 改狀態：直接編輯 .meta.json 的 "status"
  - 刪 session：刪掉對應的 .meta.json 和 .jsonl

格式：
{
  "id": "web_260307_a1b2c3",
  "company_id": "uuid-of-company",
  "type": "technical",          # recruiter | technical | behavioral | hiring_manager
  "mode": "practice",           # practice | real
  "status": "created",          # created | active | completed | abandoned
  "interviewer_name": "",
  "additional_notes": "",
  "must_ask_questions": [],
  "created_at": "...",
  "updated_at": "..."
}
"""
__all__ = ["list_sessions", "create_session", "get_session", "update_status", "delete_session", "get_tasks", "complete_current_task", "delete_sessions_by_company"]

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SESSIONS_DIR = _PROJECT_ROOT / "data" / "sessions"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _meta_file(session_id: str) -> Path:
    return _SESSIONS_DIR / f"{session_id}.meta.json"


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _save(session: dict) -> None:
    _meta_file(session["id"]).write_text(
        json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _make_session_id() -> str:
    date_str = datetime.now().strftime("%y%m%d")
    random_str = uuid.uuid4().hex[:6]
    return f"web_{date_str}_{random_str}"


# ── CRUD ──────────────────────────────────────────────────────────────────────

def list_sessions(company_id: str) -> list[dict]:
    """列出某公司底下所有 session，依建立時間倒序。"""
    _ensure_dir()
    results = [
        s
        for path in _SESSIONS_DIR.glob("*.meta.json")
        if (s := _load(path)) is not None and s.get("company_id") == company_id
    ]
    results.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return results


def create_session(
    company_id: str,
    interview_type: str,
    mode: str,
    interviewer_name: str | None = None,
    additional_notes: str | None = None,
    must_ask_questions: list[str] | None = None,
    tasks: list[dict] | None = None,
) -> dict:
    """建立新 session，寫入 .meta.json，初始狀態 'created'。"""
    _ensure_dir()
    now = _now()
    task_list = tasks or []
    # 第一題標記 in_progress
    if task_list:
        task_list[0]["status"] = "in_progress"

    session = {
        "id": _make_session_id(),
        "company_id": company_id,
        "type": interview_type,
        "mode": mode,
        "status": "created",
        "interviewer_name": interviewer_name or "",
        "additional_notes": additional_notes or "",
        "must_ask_questions": must_ask_questions or [],
        "tasks": task_list,
        "current_task_index": 0,
        "created_at": now,
        "updated_at": now,
    }
    _save(session)
    return session


def get_session(session_id: str) -> dict | None:
    """取得單一 session 元資料。"""
    return _load(_meta_file(session_id))


def update_status(session_id: str, status: str) -> dict | None:
    """更新 session 狀態（created → active → completed / abandoned）。"""
    session = get_session(session_id)
    if session is None:
        return None
    session["status"] = status
    session["updated_at"] = _now()
    _save(session)
    return session


def delete_session(session_id: str) -> bool:
    """刪除 session 的 .meta.json 與對話歷史 .jsonl。"""
    path = _meta_file(session_id)
    if not path.exists():
        return False
    path.unlink()
    jsonl = _SESSIONS_DIR / f"{session_id}.jsonl"
    if jsonl.exists():
        jsonl.unlink()
    return True


def get_tasks(session_id: str) -> list[dict]:
    """回傳任務清單（含目前 index）。"""
    session = get_session(session_id)
    if not session:
        return []
    return session.get("tasks", [])


def complete_current_task(session_id: str, score: int, evaluation: str) -> bool:
    """
    將當前 in_progress 任務標記為 completed，
    並把下一題設為 in_progress。
    回傳 True 表示還有下一題，False 表示全部結束。
    """
    session = get_session(session_id)
    if not session:
        return False
    tasks = session.get("tasks", [])
    idx = session.get("current_task_index", 0)
    if idx >= len(tasks):
        return False

    tasks[idx]["status"] = "completed"
    tasks[idx]["score"] = score
    tasks[idx]["evaluation"] = evaluation

    next_idx = idx + 1
    session["current_task_index"] = next_idx
    if next_idx < len(tasks):
        tasks[next_idx]["status"] = "in_progress"

    session["tasks"] = tasks
    session["updated_at"] = _now()
    _save(session)
    return next_idx < len(tasks)


def delete_sessions_by_company(company_id: str) -> int:
    """刪除某公司底下所有 session（.meta.json + .jsonl），回傳刪除數量。"""
    sessions = list_sessions(company_id)
    for s in sessions:
        delete_session(s["id"])
    return len(sessions)
