"""
匹配度分析儲存層。
每個 application 一個 JSON 檔，存在 data/matches/{application_id}.json。
"""
__all__ = ["get", "save", "delete"]

import json
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_MATCHES_DIR = _PROJECT_ROOT / "data" / "matches"


def _file(application_id: str) -> Path:
    return _MATCHES_DIR / f"{application_id}.json"


def get(application_id: str) -> dict | None:
    path = _file(application_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save(application_id: str, data: dict) -> dict:
    _MATCHES_DIR.mkdir(parents=True, exist_ok=True)
    record = {**data, "analyzed_at": datetime.now(timezone.utc).isoformat()}
    _file(application_id).write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return record


def delete(application_id: str) -> None:
    path = _file(application_id)
    if path.exists():
        path.unlink()
