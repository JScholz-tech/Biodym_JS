import os

import uvicorn

# Auto-reload is OFF by default. On Windows the reloader spawns a worker
# subprocess that can outlive its parent (e.g. when the terminal is closed),
# keeping port 8001 bound and serving stale code. For normal use (defining
# systems, importing Excel) reload is unnecessary. Developers editing the app
# can opt in with:  SYSTEMDEFINER_RELOAD=1 uv run python -m systemdefiner
_reload = os.environ.get("SYSTEMDEFINER_RELOAD", "").lower() in ("1", "true", "yes")

uvicorn.run("systemdefiner.main:app", host="127.0.0.1", port=8001, reload=_reload)
