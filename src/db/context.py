import contextvars
from typing import Dict

current_user_id:       contextvars.ContextVar[str]           = contextvars.ContextVar("current_user_id",       default="")
current_anthropic_key: contextvars.ContextVar[str]           = contextvars.ContextVar("current_anthropic_key", default="")
current_openai_key:    contextvars.ContextVar[str]           = contextvars.ContextVar("current_openai_key",    default="")
current_models:        contextvars.ContextVar[Dict[str, str]] = contextvars.ContextVar("current_models",        default={})
