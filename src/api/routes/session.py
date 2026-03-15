import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.db import session_store, company_store, resume_store
from src.core.task_generator import generate_tasks_async
from src.logger import get_logger

log = get_logger("session")

router = APIRouter(prefix="/api/session", tags=["session"])

InterviewType = Literal["recruiter", "technical", "behavioral", "hiring_manager"]
SessionMode = Literal["practice", "real"]


class CreateSessionRequest(BaseModel):
    company_id: str
    type: InterviewType
    mode: SessionMode
    interviewer_name: str | None = None
    additional_notes: str | None = None
    must_ask_questions: list[str] = []


@router.get("/company/{company_id}")
def list_sessions(company_id: str):
    """GET /api/session/company/{company_id} — 取得某公司底下所有 session"""
    return session_store.list_sessions(company_id)


@router.post("")
async def create_session(body: CreateSessionRequest):
    """POST /api/session — 建立新 session，並生成面試任務清單"""
    company = await asyncio.to_thread(company_store.get_application, body.company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    resume = await asyncio.to_thread(resume_store.load)
    log.info("creating session", extra={"type": body.type, "company_id": body.company_id})

    # init_task_generate_node：生成任務清單
    try:
        tasks = await generate_tasks_async(
            interview_type=body.type,
            resume=resume,
            company_name=company.get("company_name", ""),
            job_title=company.get("job_title", ""),
            industry=company.get("industry", ""),
            job_description=company.get("job_description", ""),
            additional_notes=body.additional_notes or "",
            must_ask_questions=body.must_ask_questions or [],
        )
    except Exception as e:
        from src.core.llm_client import check_auth_error
        check_auth_error(e)
        log.error("generate_tasks failed", extra={"error": str(e)}, exc_info=True)
        tasks = []

    return await asyncio.to_thread(
        lambda: session_store.create_session(
            company_id=body.company_id,
            interview_type=body.type,
            mode=body.mode,
            interviewer_name=body.interviewer_name,
            additional_notes=body.additional_notes,
            must_ask_questions=body.must_ask_questions,
            tasks=tasks,
        )
    )


@router.delete("/{session_id}")
def delete_session(session_id: str):
    """DELETE /api/session/{session_id} — 刪除 session"""
    ok = session_store.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": session_id}
