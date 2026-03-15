import os
if os.getenv("STORAGE_MODE", "local") == "online":
    from src.db.online.session_store import *
else:
    from src.db.local.session_store import *
