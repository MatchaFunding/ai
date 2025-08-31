from fastapi import FastAPI
from datetime import datetime, timezone

from app.api import ideas
from app.api import ia


app = FastAPI(title="IA Service", version="0.1.0")
API_PREFIX = "/api/v1"

@app.get(f"{API_PREFIX}/health")
def health():
    return {
        "status": "ok",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
        "service": app.title,
    }


app.include_router(ideas.router, prefix=API_PREFIX)
app.include_router(ia.router, prefix="/api/v1")
