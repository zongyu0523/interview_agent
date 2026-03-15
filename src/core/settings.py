"""
全域設定管理。

- API Keys：從 .env 讀取；anthropic/openai 優先讀 per-request ContextVar（from header）
- Models：從 per-request ContextVar 讀取（前端 localStorage → X-Models header），fallback hardcoded defaults
"""
import os

_KEY_ENV_MAP: dict[str, str] = {
    "anthropic":            "ANTHROPIC_API_KEY",
    "openai":               "OPENAI_API_KEY",
    "supabase_url":         "SUPABASE_URL",
    "supabase_service_key": "SUPABASE_SERVICE_KEY",
}

_DEFAULT_MODELS: dict[str, str] = {
    "chat_agent":     "anthropic/claude-sonnet-4-6",
    "task_generator": "anthropic/claude-sonnet-4-6",
    "resume_parser":  "anthropic/claude-sonnet-4-6",
    "scorer":         "anthropic/claude-haiku-4-5-20251001",
    "match_analyzer": "anthropic/claude-haiku-4-5-20251001",
    "tts":            "openai/tts-1",
    "stt":            "openai/whisper-1",
}


# ── Keys ──────────────────────────────────────────────────────────────────────

def get_key(provider: str) -> str:
    """回傳指定 provider 的 key。
    anthropic/openai：優先讀 per-request ContextVar（from header），fallback os.environ。
    supabase_*：只讀 os.environ。
    """
    if provider == "anthropic":
        from src.db.context import current_anthropic_key
        return current_anthropic_key.get() or os.getenv("ANTHROPIC_API_KEY", "")
    if provider == "openai":
        from src.db.context import current_openai_key
        return current_openai_key.get() or os.getenv("OPENAI_API_KEY", "")
    return os.getenv(_KEY_ENV_MAP.get(provider, ""), "")


def get_stored_keys() -> dict[str, str]:
    """回傳所有 key 的當前 os.environ 值（供 GET /api/key 狀態顯示）。"""
    return {provider: os.getenv(env_var, "") for provider, env_var in _KEY_ENV_MAP.items()}


# ── Models ────────────────────────────────────────────────────────────────────

def get_model(role: str) -> str:
    """讀 per-request X-Models header（前端 localStorage），fallback hardcoded defaults。"""
    from src.db.context import current_models
    models = current_models.get()
    return models.get(role) or _DEFAULT_MODELS.get(role, "")
