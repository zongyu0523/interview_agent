from pathlib import Path

from dotenv import load_dotenv

# 在所有 src.* import 之前載入 .env，確保環境變數對所有模組都可見
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=True)

from src.logger import setup_logging
setup_logging()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.db.context import current_user_id, current_anthropic_key, current_openai_key, current_models

from src.api.routes import chat, reports, company, session, resume, speech, key, match, feedback

app = FastAPI(title="Interview Agent API", version="0.1.0")

_NO_KEY_MSG = "Please set your LLM API Key in the top-right corner before starting an interview."

@app.exception_handler(Exception)
async def llm_auth_error_handler(request: Request, exc: Exception):
    import litellm
    if isinstance(exc, litellm.AuthenticationError):
        return JSONResponse(status_code=400, content={"detail": _NO_KEY_MSG})
    raise exc

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.openagentsbox.com",
        "https://openagentsbox.com",
        "https://interview-agent-rho.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


_USER_REQUIRED_PREFIXES = ("/api/company", "/api/session", "/api/resume", "/api/match", "/api/chat")

@app.middleware("http")
async def inject_context(request: Request, call_next):
    import os
    from fastapi.responses import JSONResponse as _JSONResponse
    import json as _json
    uid           = request.headers.get("X-User-Id", "")
    anthropic_key = request.headers.get("X-Anthropic-Key", "") or os.getenv("ANTHROPIC_API_KEY", "")
    openai_key    = request.headers.get("X-OpenAI-Key", "")    or os.getenv("OPENAI_API_KEY", "")
    try:
        models_header = request.headers.get("X-Models", "")
        models_dict: dict = _json.loads(models_header) if models_header else {}
    except Exception:
        models_dict = {}

    if (
        not uid
        and request.method != "OPTIONS"
        and os.getenv("STORAGE_MODE", "local") == "online"
        and request.url.path.startswith(_USER_REQUIRED_PREFIXES)
    ):
        return _JSONResponse(status_code=401, content={"detail": "X-User-Id header required"})

    t0 = current_user_id.set(uid)
    t1 = current_anthropic_key.set(anthropic_key)
    t2 = current_openai_key.set(openai_key)
    t3 = current_models.set(models_dict)
    try:
        return await call_next(request)
    finally:
        current_models.reset(t3)
        current_openai_key.reset(t2)
        current_anthropic_key.reset(t1)
        current_user_id.reset(t0)

app.include_router(chat.router)
app.include_router(reports.router)
app.include_router(company.router)
app.include_router(session.router)
app.include_router(resume.router)
app.include_router(speech.router)
app.include_router(key.router)
app.include_router(match.router)
app.include_router(feedback.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Standalone 模式：serve 前端靜態檔案 ──────────────────────────────────────
from pathlib import Path as _Path

_static_dir = _Path(__file__).resolve().parents[2] / "static"
if _static_dir.exists():
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, RedirectResponse

    app.mount("/interview/assets", StaticFiles(directory=_static_dir / "assets"), name="assets")

    @app.get("/")
    def root_redirect():
        return RedirectResponse(url="/interview")

    @app.get("/interview/{full_path:path}")
    def serve_frontend(full_path: str):
        return FileResponse(_static_dir / "index.html")

