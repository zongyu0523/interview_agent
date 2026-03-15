import os
if os.getenv("STORAGE_MODE", "local") == "online":
    from src.db.online.memory import *
else:
    from src.db.local.memory import *
