import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.db import company_store, resume_store, match_store
from src.core import match_analyzer

router = APIRouter(prefix="/api/match", tags=["match"])


class AnalyzeRequest(BaseModel):
    application_id: str
    user_id: str = ""  # reserved, not used yet


@router.get("/{application_id}")
def get_match(application_id: str):
    """GET /api/match/{application_id} — 取得已儲存的匹配分析，無則 404。"""
    result = match_store.get(application_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No match analysis found")
    return result


@router.post("")
async def analyze_match(body: AnalyzeRequest):
    """POST /api/match — 執行履歷與職位描述匹配分析並儲存結果。"""
    company = await asyncio.to_thread(company_store.get_application, body.application_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Application not found")

    resume = await asyncio.to_thread(resume_store.load)
    if not resume.get("professional_summary") and not resume.get("work_experience"):
        raise HTTPException(
            status_code=422,
            detail="Resume is empty. Please upload your resume before analyzing."
        )

    try:
        result = await match_analyzer.analyze_async(resume, company)
    except Exception as e:
        from src.core.llm_client import check_auth_error
        check_auth_error(e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}") from e

    saved = await asyncio.to_thread(match_store.save, body.application_id, result.model_dump())
    return saved


@router.delete("/{application_id}")
def delete_match(application_id: str):
    """DELETE /api/match/{application_id} — 清除已儲存的匹配分析。"""
    match_store.delete(application_id)
    return {"deleted": application_id}
