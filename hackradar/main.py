"""FastAPI application for HackRadar with SSE streaming and static frontend."""
from __future__ import annotations

import json
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from hackradar.config import settings
from hackradar.pipeline.orchestrator import run_search_pipeline
from hackradar.schemas import Profile

app = FastAPI(
    title="HackRadar API",
    description="Hackathon finder with ranked, eligibility-checked results.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
INDEX_HTML = STATIC_DIR / "index.html"


@app.get("/api/health")
async def health_check() -> dict:
    """Return health status and mock provider status."""
    return {
        "status": "ok",
        "mocks": settings.use_mocks,
        "app": "HackRadar",
        "version": "0.1.0",
    }


@app.post("/api/search")
async def search_hackathons(profile: Profile) -> StreamingResponse:
    """Run search pipeline and stream SSE events (progress, result, done, error)."""

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for event_dict in run_search_pipeline(profile):
                payload = json.dumps(event_dict)
                yield f"data: {payload}\n\n"
        except Exception as e:
            err_payload = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/", response_class=HTMLResponse)
async def serve_index() -> HTMLResponse:
    """Serve the static frontend."""
    if not INDEX_HTML.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return HTMLResponse(content=INDEX_HTML.read_text(encoding="utf-8"))


# Mount static assets if any
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def main() -> None:
    """Run server via CLI entry point."""
    import uvicorn
    uvicorn.run("hackradar.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
