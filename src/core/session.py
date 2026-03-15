"""
Session 初始化協調者。
流程：ID 生成 → DB 建立紀錄 → JSONL 初始化 → 取得 AI 開場白 → 狀態更新為 active
"""
import uuid
from datetime import datetime

from src.core import memory
from src.core.llm_client import get_opening_message
from src.core.prompts.interviewer import build_system_prompt
from src.db import models


def create_session_id(source: str = "web") -> str:
    date_str = datetime.now().strftime("%y%m%d")
    random_str = uuid.uuid4().hex[:6]
    return f"{source}_{date_str}_{random_str}"


def init_session(
    candidate_name: str,
    position: str,
    source: str = "web",
    extra_context: str = "",
) -> dict:
    """
    建立新面試 Session。

    1. 生成 session_id
    2. DB 寫入 sessions 表（status='created'）
    3. 建立 JSONL 檔，寫入 system prompt
    4. 呼叫 Claude 取得開場白
    5. 開場白 append 進 JSONL
    6. DB 狀態改為 'active'

    Returns:
        {"session_id": str, "first_message": str}
    """
    session_id = create_session_id(source)
    system_prompt = build_system_prompt(candidate_name, position, extra_context)

    # 1. DB 建立紀錄
    models.create_session_record(session_id, candidate=candidate_name, job_role=position)

    # 2. JSONL 初始化（寫入 system prompt）
    memory.init_conversation(session_id, system_prompt)

    # 3. 呼叫 Claude 取得開場白
    first_message = get_opening_message(system_prompt, candidate_name, position)

    # 4. 開場白寫入 JSONL
    memory.append_message(session_id, "assistant", first_message)

    # 5. DB 狀態 created → active
    models.activate_session(session_id)

    return {
        "session_id": session_id,
        "first_message": first_message,
    }
