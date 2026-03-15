import os
if os.getenv("STORAGE_MODE", "local") == "online":
    from src.db.online.resume_store import *
else:
    from src.db.local.resume_store import *
