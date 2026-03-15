"""
統一 logging 設定。
在 src/api/main.py 啟動時呼叫 setup_logging() 一次即可。
其他模組用 get_logger("subsystem") 取得 logger。

輸出：
  console — 彩色人類可讀格式
  file    — logs/agent-YYYY-MM-DD.log，JSON lines，7 天 rolling
"""
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = _PROJECT_ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Standard LogRecord attrs to exclude from JSON extra ──────────────────────

_STANDARD_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "taskName", "message",
})


# ── File handler: JSON lines, daily rolling ───────────────────────────────────

class _JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time":      datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level":     record.levelname.lower(),
            "subsystem": record.name,
            "message":   record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k not in _STANDARD_ATTRS and not k.startswith("_"):
                payload[k] = v
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _file_handler() -> logging.Handler:
    today = datetime.now().strftime("%Y-%m-%d")
    h = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / f"agent-{today}.log",
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    h.setFormatter(_JsonLineFormatter())
    return h


# ── Console handler: colored ─────────────────────────────────────────────────

def _console_handler() -> logging.Handler:
    try:
        import colorlog
        fmt = colorlog.ColoredFormatter(
            "%(log_color)s[%(name)s]%(reset)s %(message)s",
            log_colors={
                "DEBUG":    "cyan",
                "INFO":     "white",
                "WARNING":  "yellow",
                "ERROR":    "red",
                "CRITICAL": "bold_red",
            },
        )
    except ImportError:
        fmt = logging.Formatter("[%(name)s] %(levelname)s %(message)s")

    h = logging.StreamHandler()
    h.setFormatter(fmt)
    return h


# ── Public API ────────────────────────────────────────────────────────────────

def setup_logging(level: str = "DEBUG") -> None:
    """啟動時呼叫一次。第三方套件保持 WARNING，只有 'agent' namespace 提升到 level。"""
    import os
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    if not root.handlers:
        # 雲端環境（Railway / Render 等）只用 stdout，不寫檔
        if not os.getenv("RAILWAY_ENVIRONMENT") and not os.getenv("RENDER"):
            root.addHandler(_file_handler())
        root.addHandler(_console_handler())
    logging.getLogger("agent").setLevel(level)


def get_logger(subsystem: str) -> logging.Logger:
    """
    Usage:
        log = get_logger("interview_agent")
        log.info("tool called", extra={"tool": "read_interview_plan"})
    """
    return logging.getLogger(f"agent.{subsystem}")
