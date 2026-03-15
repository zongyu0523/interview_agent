"""
對話紀錄系統（Supabase online 版）。
API 與 src/core/memory.py 完全相同。
對話存入 chat_messages 表。
"""
__all__ = ["init_conversation", "append_message", "load_conversation", "conversation_exists"]

from src.db.online.client import get_client


def init_conversation(session_id: str, system_prompt: str) -> None:
    """清除舊對話並寫入 system prompt。"""
    sb = get_client()
    sb.table("chat_messages").delete().eq("session_id", session_id).execute()
    sb.table("chat_messages").insert({
        "session_id": session_id,
        "role": "system",
        "content": system_prompt,
    }).execute()


def append_message(session_id: str, role: str, content: str) -> None:
    sb = get_client()
    sb.table("chat_messages").insert({
        "session_id": session_id,
        "role": role,
        "content": content,
    }).execute()


def load_conversation(session_id: str) -> list[dict]:
    sb = get_client()
    res = sb.table("chat_messages").select("role,content").eq("session_id", session_id).order("id").execute()
    return [{"role": r["role"], "content": r["content"]} for r in (res.data or [])]


def conversation_exists(session_id: str) -> bool:
    sb = get_client()
    res = sb.table("chat_messages").select("id").eq("session_id", session_id).limit(1).execute()
    return bool(res.data)
