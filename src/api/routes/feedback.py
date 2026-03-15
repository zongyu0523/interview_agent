"""
Feedback routes — 答案評分與語法修正。

POST /api/feedback/score   → {score, reasoning, better_version}
POST /api/feedback/grammar → {corrected_version}
"""
import asyncio

from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException

from src.core import llm_client
from src.core.prompts.reviewer import build_score_prompt
from src.db import session_store
from src.logger import get_logger

log = get_logger("feedback")
router = APIRouter(prefix="/api/feedback", tags=["feedback"])


# ── Pydantic models ────────────────────────────────────────────────────────────

class ScoreRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    task_topic: str = ""
    task_instruction: str = ""


class ScoreResult(BaseModel):
    score: int = Field(ge=1, le=10)
    reasoning: str
    better_version: str


class GrammarRequest(BaseModel):
    text: str


class GrammarResult(BaseModel):
    corrected_version: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/score", response_model=ScoreResult)
async def score_answer(body: ScoreRequest):
    """
    POST /api/feedback/score
    評分候選人的回答，並提供改進版本。
    """
    session = await asyncio.to_thread(session_store.get_session, body.session_id)
    interview_type = session.get("type", "recruiter") if session else "recruiter"

    prompt = build_score_prompt(
        interview_type=interview_type,
        question=body.question,
        answer=body.answer,
        task_topic=body.task_topic,
        task_instruction=body.task_instruction,
    )

    try:
        client = llm_client.get_async_instructor_client()
        result: ScoreResult = await client.chat.completions.create(
            model=llm_client.get_model("scorer"),
            response_model=ScoreResult,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
        )
        log.info("score generated", extra={"session_id": body.session_id, "score": result.score})
        return result
    except HTTPException:
        raise
    except Exception as e:
        from src.core.llm_client import check_auth_error
        check_auth_error(e)
        log.error("score error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grammar", response_model=GrammarResult)
async def grammar_check(body: GrammarRequest):
    """
    POST /api/feedback/grammar
    修正語法錯誤，保留原意。
    """
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Text is empty")

    prompt = (
        "Fix any grammar, spelling, or punctuation errors in the following text. "
        "Preserve the original meaning and tone. Return only the corrected text, nothing else.\n\n"
        f"{body.text}"
    )

    try:
        response = await llm_client.acompletion(
            model=llm_client.get_model("scorer"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
        )
        corrected = response.choices[0].message.content.strip()
        return GrammarResult(corrected_version=corrected)
    except HTTPException:
        raise
    except Exception as e:
        from src.core.llm_client import check_auth_error
        check_auth_error(e)
        log.error("grammar error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))
