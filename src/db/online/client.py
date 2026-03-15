from supabase import create_client, Client
from src.core import settings

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = settings.get_key("supabase_url")
        key = settings.get_key("supabase_service_key")
        if not url or not key:
            raise RuntimeError("Supabase URL/Key not configured. Set them in Models & Keys settings.")
        _client = create_client(url, key)
    return _client


def reset_client() -> None:
    """憑證更新後呼叫，重建 client。"""
    global _client
    _client = None
