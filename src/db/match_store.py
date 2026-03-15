import os
if os.getenv("STORAGE_MODE", "local") == "online":
    from src.db.online.match_store import *
else:
    from src.db.local.match_store import *
