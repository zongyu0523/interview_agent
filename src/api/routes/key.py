"""
API key 端點。

GET  /api/key                  — 回傳伺服器 .env 中的 key 狀態（遮罩）
POST /api/key/verify           — 驗證 OpenAI API Key
POST /api/key/verify/anthropic — 驗證 Anthropic API Key
"""
import litellm
import openai
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.core import settings

router = APIRouter(prefix="/api/key", tags=["key"])


def _mask(key: str) -> str:
    key = key.strip()
    if not key:
        return ""
    return f"{'*' * (len(key) - 4)}{key[-4:]}" if len(key) > 4 else "****"


class KeySettings(BaseModel):
    anthropic: str | None = None
    openai: str | None = None


@router.get("")
def get_keys():
    """回傳伺服器 .env 中的 key 狀態（遮罩）。本地模式用來確認 .env 設定正確。"""
    stored = settings.get_stored_keys()
    return {
        "anthropic": _mask(stored.get("anthropic", "")),
        "openai": _mask(stored.get("openai", "")),
    }


# ── 驗證 ──────────────────────────────────────────────────────────────────────

@router.post("/verify")
async def verify_openai_key(body: KeySettings):
    key = (body.openai or "").strip()
    if not key:
        return JSONResponse(status_code=400, content={"valid": False, "detail": "No key provided"})
    try:
        client = openai.OpenAI(api_key=key)
        client.models.list()
        return {"valid": True}
    except openai.AuthenticationError:
        return JSONResponse(status_code=401, content={"valid": False, "detail": "Invalid API key."})
    except Exception:
        return JSONResponse(status_code=401, content={"valid": False, "detail": "Connection failed. Please try again."})


@router.post("/verify/anthropic")
async def verify_anthropic_key(body: KeySettings):
    key = (body.anthropic or "").strip()
    if not key:
        return JSONResponse(status_code=400, content={"valid": False, "detail": "No key provided"})
    try:
        litellm.completion(
            model="anthropic/claude-haiku-4-5-20251001",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
            api_key=key,
        )
        return {"valid": True}
    except litellm.AuthenticationError:
        return JSONResponse(status_code=401, content={"valid": False, "detail": "Invalid API key."})
    except Exception:
        return JSONResponse(status_code=401, content={"valid": False, "detail": "Connection failed. Please try again."})
