import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core import memory
from src.core.interview_agent import run_agent_async
from src.core.prompts.chat_agent import build_chat_agent_prompt
from src.db import session_store, company_store
from src.logger import get_logger

log = get_logger("chat")

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ── Response models ────────────────────────────────────────────────────────────

class ChatResult(BaseModel):
    response: str
    finished: bool
    total_round: int
    task_topic: str
    task_instruction: str


class ChatHistoryResult(BaseModel):
    messages: list[dict]
    total_round: int


class SendMessageRequest(BaseModel):
    message: str


# ── Helpers ────────────────────────────────────────────────────────────────────

def _count_rounds(messages: list[dict]) -> int:
    return sum(1 for m in messages if m.get("role") == "user")


def _current_task_info(session_id: str) -> tuple[str, str]:
    """回傳當前任務的 (topic, instruction)，找不到回傳空字串。"""
    tasks = session_store.get_tasks(session_id)
    session = session_store.get_session(session_id)
    if not session or not tasks:
        return "", ""
    idx = session.get("current_task_index", 0)
    if idx < len(tasks):
        t = tasks[idx]
        return t.get("topic", ""), t.get("instruction", "")
    return "", ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/{session_id}/start", response_model=ChatResult)
async def start_interview(session_id: str):
    """
    POST /api/chat/{session_id}/start
    初始化面試，取得 AI 開場白。
    """
    session = await asyncio.to_thread(session_store.get_session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 已有對話，直接回傳第一則 assistant 訊息
    if await asyncio.to_thread(memory.conversation_exists, session_id):
        msgs = await asyncio.to_thread(memory.load_conversation, session_id)
        first_ai = next((m["content"] for m in msgs if m["role"] == "assistant"), "")
        return ChatResult(
            response=first_ai,
            finished=session.get("status") == "completed",
            total_round=_count_rounds(msgs),
            task_topic="",
            task_instruction="",
        )

    company = await asyncio.to_thread(company_store.get_application, session["company_id"])
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    system_prompt = build_chat_agent_prompt(company, session)
    await asyncio.to_thread(memory.init_conversation, session_id, system_prompt)

    # 開場白：不走 tool loop，直接讓 agent 說第一句
    opening_history = [
        {"role": "user", "content": "Please begin the interview with a brief welcome and your first question."}
    ]
    try:
        opening, _ = await run_agent_async(session_id, system_prompt, opening_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    await asyncio.to_thread(memory.append_message, session_id, "assistant", opening)
    await asyncio.to_thread(session_store.update_status, session_id, "active")
    log.info("interview started", extra={"session_id": session_id})

    topic, instruction = await asyncio.to_thread(_current_task_info, session_id)
    return ChatResult(
        response=opening,
        finished=False,
        total_round=0,
        task_topic=topic,
        task_instruction=instruction,
    )


@router.post("/{session_id}", response_model=ChatResult)
async def send_message(session_id: str, body: SendMessageRequest):
    """
    POST /api/chat/{session_id}
    傳送使用者訊息，執行 agent loop，回傳 AI 回覆。
    """
    session = await asyncio.to_thread(session_store.get_session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") == "completed":
        raise HTTPException(status_code=409, detail="Session already completed")
    if not await asyncio.to_thread(memory.conversation_exists, session_id):
        raise HTTPException(status_code=409, detail="Session not started. Call /start first.")

    await asyncio.to_thread(memory.append_message, session_id, "user", body.message)

    # 載入歷史（排除 system），傳給 agent
    all_msgs = await asyncio.to_thread(memory.load_conversation, session_id)
    system_prompt = next((m["content"] for m in all_msgs if m["role"] == "system"), "")
    history = [m for m in all_msgs if m["role"] != "system"]

    try:
        reply, all_done = await run_agent_async(session_id, system_prompt, history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    await asyncio.to_thread(memory.append_message, session_id, "assistant", reply)

    if all_done:
        await asyncio.to_thread(session_store.update_status, session_id, "completed")
        log.info("interview completed", extra={"session_id": session_id})

    topic, instruction = await asyncio.to_thread(_current_task_info, session_id)
    return ChatResult(
        response=reply,
        finished=all_done,
        total_round=_count_rounds(all_msgs),
        task_topic=topic,
        task_instruction=instruction,
    )


@router.get("/{session_id}/history", response_model=ChatHistoryResult)
async def get_history(session_id: str):
    """
    GET /api/chat/{session_id}/history
    回傳對話歷史（排除 system prompt）。
    """
    if not await asyncio.to_thread(memory.conversation_exists, session_id):
        return ChatHistoryResult(messages=[], total_round=0)

    all_msgs = await asyncio.to_thread(memory.load_conversation, session_id)
    visible = [m for m in all_msgs if m["role"] != "system"]

    return ChatHistoryResult(
        messages=visible,
        total_round=_count_rounds(all_msgs),
    )
