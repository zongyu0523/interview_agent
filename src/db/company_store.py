import os
if os.getenv("STORAGE_MODE", "local") == "online":
    from src.db.online.company_store import *
else:
    from src.db.local.company_store import *
