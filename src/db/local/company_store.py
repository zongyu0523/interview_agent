"""
公司資訊儲存層。
每間公司一個 JSON 檔，存在 data/companies/{id}.json。

手動新增：直接放一個 .json 進去
手動刪除：直接刪掉 .json
手動修改：直接編輯 .json

格式：
{
  "id": "uuid",
  "company_name": "Google",
  "job_title": "Software Engineer",
  "industry": "Technology",
  "job_description": "...",
  "job_grade": "",
  "created_at": "2024-01-01T00:00:00+00:00",
  "updated_at": "2024-01-01T00:00:00+00:00"
}
"""
__all__ = ["list_applications", "create_application", "get_application", "delete_application"]

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_COMPANIES_DIR = _PROJECT_ROOT / "data" / "companies"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    _COMPANIES_DIR.mkdir(parents=True, exist_ok=True)


def _file(application_id: str) -> Path:
    return _COMPANIES_DIR / f"{application_id}.json"


def _load_file(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def list_applications() -> list[dict]:
    """列出所有公司記錄。"""
    _ensure_dir()
    results = [
        record
        for path in _COMPANIES_DIR.glob("*.json")
        if (record := _load_file(path)) is not None
    ]
    results.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return results


def create_application(
    company_name: str,
    job_title: str,
    job_description: str | None = None,
    industry: str | None = None,
    job_grade: str | None = None,
) -> dict:
    """新增一間公司，建立對應的 JSON 檔。"""
    _ensure_dir()
    now = _now()
    record = {
        "id": str(uuid.uuid4()),
        "company_name": company_name,
        "job_title": job_title,
        "job_description": job_description or "",
        "industry": industry or "",
        "job_grade": job_grade or "",
        "created_at": now,
        "updated_at": now,
    }
    _file(record["id"]).write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return record


def get_application(application_id: str) -> dict | None:
    """取得單一公司記錄。"""
    return _load_file(_file(application_id))


def delete_application(application_id: str) -> bool:
    """刪除公司記錄（刪除對應 JSON 檔）。"""
    path = _file(application_id)
    if not path.exists():
        return False
    path.unlink()
    return True
