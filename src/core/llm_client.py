"""
LiteLLM wrapper。
所有模型與 API key 設定集中在 config/settings.json，透過 src.core.settings 管理。
環境變數由 src/api/main.py 在啟動時統一載入，此處不重複呼叫 load_dotenv。
"""
import instructor
import litellm

from src.core import settings


def get_model(role: str) -> str:
    """回傳 settings.json 中對應 role 的 model string。"""
    return settings.get_model(role)


_ANTHROPIC_NO_KEY_MSG = "Please set your Anthropic API Key in the top-right corner before starting an interview."
_ANTHROPIC_BAD_KEY_MSG = "Your Anthropic API Key is invalid. Please check the key in the top-right corner."
_OPENAI_NO_KEY_MSG = "Please set your OpenAI API Key in the top-right corner before starting an interview."
_OPENAI_BAD_KEY_MSG = "Your OpenAI API Key is invalid. Please check the key in the top-right corner."
_NO_KEY_MSG = "Please set your LLM API Key in the top-right corner before starting an interview."


def _no_key_msg(model: str) -> str:
    if model.startswith("anthropic/"):
        return _ANTHROPIC_NO_KEY_MSG
    if model.startswith("openai/"):
        return _OPENAI_NO_KEY_MSG
    return _NO_KEY_MSG


def _bad_key_msg(model: str) -> str:
    if model.startswith("anthropic/"):
        return _ANTHROPIC_BAD_KEY_MSG
    if model.startswith("openai/"):
        return _OPENAI_BAD_KEY_MSG
    return _NO_KEY_MSG


def check_auth_error(e: Exception):
    """如果 Exception 包含 key 相關訊息，直接丟出 400，避免被 instructor 包裝後回傳 500。"""
    from fastapi import HTTPException
    s = str(e)
    for msg in (
        _ANTHROPIC_NO_KEY_MSG, _ANTHROPIC_BAD_KEY_MSG,
        _OPENAI_NO_KEY_MSG, _OPENAI_BAD_KEY_MSG,
        _NO_KEY_MSG,
    ):
        if msg in s:
            raise HTTPException(status_code=400, detail=msg)


def completion(**kwargs):
    """litellm.completion 的薄包裝；自動注入 per-request api_key，key 未設定時回傳 400。"""
    from fastapi import HTTPException
    from src.db.context import current_anthropic_key, current_openai_key

    model = kwargs.get("model", "")
    if "api_key" not in kwargs:
        if model.startswith("anthropic/"):
            key = current_anthropic_key.get() or settings.get_key("anthropic")
            if not key:
                raise HTTPException(status_code=400, detail=_ANTHROPIC_NO_KEY_MSG)
            kwargs["api_key"] = key
        elif model.startswith("openai/"):
            key = current_openai_key.get() or settings.get_key("openai")
            if not key:
                raise HTTPException(status_code=400, detail=_OPENAI_NO_KEY_MSG)
            kwargs["api_key"] = key

    try:
        return litellm.completion(**kwargs)
    except litellm.AuthenticationError:
        raise HTTPException(status_code=400, detail=_bad_key_msg(model))


def get_instructor_client():
    """回傳 instructor client，使用有 key 檢查的 completion 包裝。"""
    return instructor.from_litellm(completion)


async def acompletion(**kwargs):
    """litellm.acompletion 的非同步薄包裝，含 API key 注入。"""
    from fastapi import HTTPException
    from src.db.context import current_anthropic_key, current_openai_key

    model = kwargs.get("model", "")
    if "api_key" not in kwargs:
        if model.startswith("anthropic/"):
            key = current_anthropic_key.get() or settings.get_key("anthropic")
            if not key:
                raise HTTPException(status_code=400, detail=_ANTHROPIC_NO_KEY_MSG)
            kwargs["api_key"] = key
        elif model.startswith("openai/"):
            key = current_openai_key.get() or settings.get_key("openai")
            if not key:
                raise HTTPException(status_code=400, detail=_OPENAI_NO_KEY_MSG)
            kwargs["api_key"] = key

    try:
        return await litellm.acompletion(**kwargs)
    except litellm.AuthenticationError:
        raise HTTPException(status_code=400, detail=_bad_key_msg(model))


def get_async_instructor_client():
    """回傳 AsyncInstructor（instructor 自動偵測 async callable）。"""
    return instructor.from_litellm(acompletion)


# ── 高階函式（原 agent.py）────────────────────────────────────────────────────

def get_opening_message(system_prompt: str, candidate_name: str, position: str) -> str:
    """呼叫 LLM，取得面試開場白。"""
    prompt = (
        f"請用繁體中文，以面試官身份，向應徵「{position}」的候選人「{candidate_name}」"
        f"說一句簡短的歡迎詞，並請對方做自我介紹。只說一句話，不要多問。"
    )
    response = completion(
        model=get_model("chat_agent"),
        max_tokens=256,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
