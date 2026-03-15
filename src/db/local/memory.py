"""
JSONL 對話紀錄系統。
每個 Session 一個 .jsonl 檔案，存放完整對話歷史。

格式：
  {"role": "system",    "content": "你是面試官..."}
  {"role": "assistant", "content": "王小明你好，請自我介紹。"}
  {"role": "user",      "content": "你好，我有三年 Python 經驗。"}

特性：
- append-only：新對話直接追加到檔尾，速度快，不需讀入整個檔案
- Agent 甦醒時，load_conversation() 一次讀完，直接餵給 LLM
- 每個 session 有獨立的 threading.Lock，防止並發寫入造成資料損毀
"""
__all__ = ["init_conversation", "append_message", "load_conversation", "conversation_exists"]

import json
import threading
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SESSIONS_DIR = _PROJECT_ROOT / "data" / "sessions"

# 每個 session 一把鎖，防止並發讀寫衝突
_locks: dict[str, threading.Lock] = {}
_locks_mutex = threading.Lock()


def _get_lock(session_id: str) -> threading.Lock:
    with _locks_mutex:
        if session_id not in _locks:
            _locks[session_id] = threading.Lock()
        return _locks[session_id]


def _get_path(session_id: str) -> Path:
    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return _SESSIONS_DIR / f"{session_id}.jsonl"


def init_conversation(session_id: str, system_prompt: str) -> None:
    """建立 JSONL 檔，寫入 system prompt 作為第一行。"""
    path = _get_path(session_id)
    with _get_lock(session_id):
        with path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"role": "system", "content": system_prompt}, ensure_ascii=False) + "\n")


def append_message(session_id: str, role: str, content: str) -> None:
    """追加一條對話到檔尾（append-only，速度快）。"""
    path = _get_path(session_id)
    with _get_lock(session_id):
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"role": role, "content": content}, ensure_ascii=False) + "\n")


def load_conversation(session_id: str) -> list[dict]:
    """讀取完整對話歷史，回傳 messages list，可直接餵給 Claude API。"""
    path = _get_path(session_id)
    if not path.exists():
        return []
    with _get_lock(session_id):
        with path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]


def conversation_exists(session_id: str) -> bool:
    return _get_path(session_id).exists()
