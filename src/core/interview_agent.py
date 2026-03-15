"""
主面試 Agent — while True tool loop。

工具：
  - read_interview_plan   : 查看目前任務清單與進度
  - update_interview_task : 完成當前任務，記錄分數與評語

流程：
  user message → [loop] → tool calls → … → end_turn → text reply
"""
import asyncio
import json

import litellm

from src.core.llm_client import get_model, acompletion
from src.db import session_store
from src.logger import get_logger

log = get_logger("interview_agent")

# ── Tool 定義（OpenAI function format）────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_interview_plan",
            "description": (
                "Read the current interview task list. "
                "Returns all tasks with their status (pending / in_progress / completed) "
                "and which task is currently active."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_interview_task",
            "description": (
                "Mark the current in-progress task as completed. "
                "Call this only when the candidate has sufficiently answered the current topic."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "integer",
                        "description": "Score 1–10 for the candidate's answer on this task.",
                    },
                    "evaluation": {
                        "type": "string",
                        "description": "Private one-sentence evaluation of the candidate's answer.",
                    },
                },
                "required": ["score", "evaluation"],
            },
        },
    },
]

# ── Tool 執行 ──────────────────────────────────────────────────────────────────

def _exec_read_plan(session_id: str) -> str:
    tasks = session_store.get_tasks(session_id)
    session = session_store.get_session(session_id)
    idx = session.get("current_task_index", 0) if session else 0

    summary = []
    for i, t in enumerate(tasks):
        marker = " ← current" if i == idx and t.get("status") == "in_progress" else ""
        summary.append({
            "index": i,
            "topic": t.get("topic", ""),
            "instruction": t.get("instruction", ""),
            "status": t.get("status", "pending"),
            "note": marker.strip(),
        })

    return json.dumps({"tasks": summary, "current_index": idx}, ensure_ascii=False)


def _exec_update_task(session_id: str, score: int, evaluation: str) -> str:
    has_next = session_store.complete_current_task(session_id, score, evaluation)
    if has_next:
        return json.dumps({"result": "task completed", "next": "more tasks remaining"})
    else:
        return json.dumps({"result": "task completed", "next": "all tasks done"})


# ── Cache helper ──────────────────────────────────────────────────────────────

def _mark_last_user_cache(messages: list[dict]) -> list[dict]:
    """
    把最後一則 user message 的 content 標上 cache_control。
    Anthropic 會 cache 截至該 block 的所有 tokens。
    """
    for i in reversed(range(len(messages))):
        if messages[i]["role"] == "user":
            content = messages[i]["content"]
            if isinstance(content, str):
                messages[i]["content"] = [
                    {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
                ]
            elif isinstance(content, list) and content:
                last = content[-1]
                if isinstance(last, dict) and "cache_control" not in last:
                    last["cache_control"] = {"type": "ephemeral"}
            break
    return messages


# ── 主 Agent Loop ──────────────────────────────────────────────────────────────

def run_agent(
    session_id: str,
    system: str,
    history: list[dict],
    api_key: str | None = None,
) -> tuple[str, bool]:
    """
    執行 agent loop，直到 end_turn。

    Args:
        session_id : 用來讀寫任務狀態
        system     : system prompt 字串
        history    : 已過濾掉 system role 的對話歷史（role: user/assistant）

    Returns:
        (reply_text, all_finished)
    """
    loop = 0

    # System prompt 以 content list 方式傳入，附加 cache_control（LiteLLM Anthropic caching）
    cached_system = {
        "role": "system",
        "content": [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ],
    }
    # History: 把最後一則 user message 標上 cache_control
    messages = [cached_system] + _mark_last_user_cache(list(history))

    log.info("agent start", extra={"session_id": session_id})

    while True:
        loop += 1
        log.debug("loop", extra={"loop": loop})

        response = litellm.completion(
            model=get_model("chat_agent"),
            max_tokens=8192,
            messages=messages,
            tools=TOOLS,
            **({"api_key": api_key} if api_key else {}),
        )

        finish_reason = response.choices[0].finish_reason
        log.debug("llm response", extra={"finish_reason": finish_reason})

        if finish_reason == "tool_calls":
            # 將 assistant message 轉成 dict 放入歷史（避免物件序列化問題）
            msg = response.choices[0].message
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in (msg.tool_calls or [])
                ],
            })

            for tool_call in response.choices[0].message.tool_calls:
                name = tool_call.function.name
                inp  = json.loads(tool_call.function.arguments)
                log.info("tool call", extra={"tool": name, "input": inp})

                if name == "read_interview_plan":
                    result = _exec_read_plan(session_id)
                elif name == "update_interview_task":
                    result = _exec_update_task(
                        session_id,
                        score=int(inp.get("score", 5)),
                        evaluation=str(inp.get("evaluation", "")),
                    )
                else:
                    result = json.dumps({"error": f"unknown tool: {name}"})

                log.debug("tool result", extra={"tool": name, "result": result[:200]})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            continue

        # end_turn
        text = response.choices[0].message.content or ""

        tasks = session_store.get_tasks(session_id)
        all_done = bool(tasks) and all(t.get("status") == "completed" for t in tasks)

        log.info("agent reply", extra={"loops": loop, "all_done": all_done, "reply_preview": text[:80]})
        return text, all_done


async def run_agent_async(
    session_id: str,
    system: str,
    history: list[dict],
    api_key: str | None = None,
) -> tuple[str, bool]:
    """
    非同步版 agent loop，使用 litellm.acompletion。
    """
    loop = 0

    cached_system = {
        "role": "system",
        "content": [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ],
    }
    messages = [cached_system] + _mark_last_user_cache(list(history))

    log.info("agent start (async)", extra={"session_id": session_id})

    while True:
        loop += 1
        log.debug("loop", extra={"loop": loop})

        response = await acompletion(
            model=get_model("chat_agent"),
            max_tokens=8192,
            messages=messages,
            tools=TOOLS,
            **({"api_key": api_key} if api_key else {}),
        )

        finish_reason = response.choices[0].finish_reason
        log.debug("llm response", extra={"finish_reason": finish_reason})

        if finish_reason == "tool_calls":
            msg = response.choices[0].message
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in (msg.tool_calls or [])
                ],
            })

            for tool_call in response.choices[0].message.tool_calls:
                name = tool_call.function.name
                inp  = json.loads(tool_call.function.arguments)
                log.info("tool call", extra={"tool": name, "input": inp})

                if name == "read_interview_plan":
                    result = await asyncio.to_thread(_exec_read_plan, session_id)
                elif name == "update_interview_task":
                    result = await asyncio.to_thread(
                        _exec_update_task,
                        session_id,
                        int(inp.get("score", 5)),
                        str(inp.get("evaluation", "")),
                    )
                else:
                    result = json.dumps({"error": f"unknown tool: {name}"})

                log.debug("tool result", extra={"tool": name, "result": result[:200]})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            continue

        text = response.choices[0].message.content or ""

        tasks = await asyncio.to_thread(session_store.get_tasks, session_id)
        all_done = bool(tasks) and all(t.get("status") == "completed" for t in tasks)

        log.info("agent reply", extra={"loops": loop, "all_done": all_done, "reply_preview": text[:80]})
        return text, all_done
