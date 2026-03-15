from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.db import company_store, session_store, match_store

router = APIRouter(prefix="/api/company", tags=["company"])


class CreateApplicationRequest(BaseModel):
    company_name: str
    job_title: str
    job_description: str | None = None
    industry: str | None = None
    job_grade: str | None = None


@router.get("")
def list_applications():
    """GET /api/company — 取得所有公司記錄"""
    return company_store.list_applications()


@router.post("")
def create_application(body: CreateApplicationRequest):
    """POST /api/company — 新增公司資訊"""
    return company_store.create_application(
        company_name=body.company_name,
        job_title=body.job_title,
        job_description=body.job_description,
        industry=body.industry,
        job_grade=body.job_grade,
    )


@router.delete("/{application_id}")
def delete_application(application_id: str):
    """DELETE /api/company/{application_id} — 刪除公司記錄與旗下所有 session"""
    ok = company_store.delete_application(application_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Application not found")
    deleted_sessions = session_store.delete_sessions_by_company(application_id)
    match_store.delete(application_id)
    return {"deleted": application_id, "deleted_sessions": deleted_sessions}
