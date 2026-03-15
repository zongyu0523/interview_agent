"""
Speech routes — TTS & STT via LiteLLM.

TTS : POST /api/speech/synthesize   body: {text}          → streaming MP3
STT : POST /api/speech/transcribe   body: multipart audio  → {text}

OpenAI API Key 由前端透過 X-OpenAI-Key header 傳入。
"""
import io
import httpx

import litellm
from fastapi import APIRouter, Header, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.core import settings
from src.core.llm_client import get_model
from src.logger import get_logger

log = get_logger("speech")
router = APIRouter(prefix="/api/speech", tags=["speech"])


def _resolve_key(x_openai_key: str) -> str:
    """Header 優先；未提供則 fallback 到 settings / 環境變數。"""
    key = x_openai_key.strip() or settings.get_key("openai")
    if not key:
        raise HTTPException(status_code=401, detail="OpenAI key not set. Provide X-OpenAI-Key header or configure via /api/key.")
    return key


# ── TTS ───────────────────────────────────────────────────────────────────────

class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "alloy"


@router.post("/synthesize")
async def synthesize(
    body: SynthesizeRequest,
    x_openai_key: str = Header(default=""),
):
    model_name = get_model("tts")
    
    # browser/tts shouldn't reach the backend
    if model_name == "browser/tts":
        raise HTTPException(status_code=400, detail="browser/tts should be handled locally by the browser")
        
    api_key = _resolve_key(x_openai_key)
    log.info("tts request", extra={"chars": len(body.text), "voice": body.voice})

    # For OpenAI models, use httpx for streaming
    if model_name.startswith("openai/"):
        async def generate_audio_stream():
            try:
                async with httpx.AsyncClient() as client:
                    clean_model_name = model_name[7:]
                        
                    async with client.stream(
                        "POST",
                        "https://api.openai.com/v1/audio/speech",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": clean_model_name,
                            "input": body.text,
                            "voice": body.voice,
                            "response_format": "mp3"
                        }
                    ) as response:
                        if response.status_code != 200:
                            error_detail = await response.aread()
                            log.error("tts streaming error", extra={"error": error_detail.decode()})
                            return
                        
                        async for chunk in response.aiter_bytes(chunk_size=4096):
                            if chunk:
                                yield chunk
            except Exception as e:
                log.error("tts stream error", extra={"error": str(e)})

        return StreamingResponse(
            generate_audio_stream(),
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "no-cache",
                "Transfer-Encoding": "chunked"
            },
        )
    
    # Fallback to litellm for other TTS models (if any)
    try:
        response = litellm.speech(
            model=model_name,
            input=body.text,
            voice=body.voice,
            api_key=api_key,
        )
        audio_bytes = response.content
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-cache"},
        )
    except Exception as e:
        log.error("tts error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


# ── STT ───────────────────────────────────────────────────────────────────────

@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    x_openai_key: str = Header(default=""),
):
    model_name = get_model("stt")
    
    # browser/stt shouldn't reach the backend
    if model_name == "browser/stt":
        raise HTTPException(status_code=400, detail="browser/stt should be handled locally by the browser")
        
    api_key = _resolve_key(x_openai_key)
    audio_bytes = await audio.read()
    log.info("stt request", extra={"size": len(audio_bytes), "audio_file": audio.filename})

    try:
        audio_file = ("audio.webm", audio_bytes, "audio/webm")
        response = litellm.transcription(
            model=model_name,
            file=audio_file,
            api_key=api_key,
        )
        text = response.text
        log.info("stt result", extra={"chars": len(text)})
        return {"text": text}
    except Exception as e:
        log.error("stt error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))
