"""
候選人履歷儲存層。
個人助手 → 單一使用者 → 一個 JSON 檔。

路徑：data/interview/resume.json
直接手動編輯即可，不需要 DB。
"""
__all__ = ["load", "save", "update"]

import copy
import json
import threading
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_RESUME_FILE = _PROJECT_ROOT / "data" / "interview" / "resume.json"

_lock = threading.Lock()

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


def load() -> dict:
    """讀取履歷，檔案不存在時回傳空白模板。"""
    with _lock:
        if not _RESUME_FILE.exists():
            return copy.deepcopy(_EMPTY)
        try:
            return json.loads(_RESUME_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return copy.deepcopy(_EMPTY)


def save(data: dict) -> dict:
    """覆寫整份履歷。"""
    with _lock:
        _RESUME_FILE.parent.mkdir(parents=True, exist_ok=True)
        _RESUME_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return data


def update(fields: dict) -> dict:
    """部分更新履歷（只更新傳入的 key）。"""
    current = load()
    current.update(fields)
    return save(current)
