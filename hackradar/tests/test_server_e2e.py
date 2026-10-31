"""End-to-end test for FastAPI server and SSE streaming using AsyncClient."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import httpx
import pytest
from hackradar.main import app


@pytest.mark.anyio
async def test_fastapi_server() -> None:
    print("=" * 60)
    print("FASTAPI SERVER & SSE STREAMING END-TO-END TEST")
    print("=" * 60)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Test GET /api/health
        health_resp = await client.get("/api/health")
        print(f"[1] GET /api/health: status={health_resp.status_code}")
        assert health_resp.status_code == 200
        health_json = health_resp.json()
        print(f"    Health payload: {health_json}")
        assert health_json["status"] == "ok"
        assert "mocks" in health_json

        # 2. Test GET / (index.html)
        index_resp = await client.get("/")
        print(f"[2] GET /: status={index_resp.status_code}, content-type={index_resp.headers.get('content-type')}")
        assert index_resp.status_code == 200
        assert "HackRadar" in index_resp.text
        assert "profileForm" in index_resp.text
        print("    Successfully served static index.html with frontend app!")

        # 3. Test POST /api/search (SSE Stream)
        profile_data = {
            "degree": "B.Tech",
            "stream": "CSE",
            "year": "3",
            "skills": ["Python", "AI"],
            "interests": ["Generative AI", "Web3"],
            "city": "Bengaluru",
            "state": "Karnataka",
            "country": "India",
            "mode": "both"
        }

        print("[3] POST /api/search: Connecting to SSE stream...")
        progress_events = []
        result_events = []
        done_event = None

        async with client.stream("POST", "/api/search", json=profile_data) as stream_resp:
            print(f"    Stream status={stream_resp.status_code}, media_type={stream_resp.headers.get('content-type')}")
            assert stream_resp.status_code == 200
            assert "text/event-stream" in stream_resp.headers.get("content-type", "")

            buffer = ""
            async for chunk in stream_resp.aiter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    part, buffer = buffer.split("\n\n", 1)
                    line = part.strip()
                    if line.startswith("data: "):
                        payload = json.loads(line[6:])
                        event_type = payload.get("type")
                        if event_type == "progress":
                            progress_events.append(payload.get("message"))
                        elif event_type == "result":
                            result_events.append(payload.get("event"))
                        elif event_type == "done":
                            done_event = payload

        print(f"    Received {len(progress_events)} progress messages:")
        for p in progress_events[:3]:
            print(f"      > {p}")
        print(f"    Received {len(result_events)} result cards:")
        for r in result_events[:3]:
            print(f"      * {r['name']} ({r['fit_score']}% fit) - {r['flags']}")
        print(f"    Done event: {done_event}")

        assert len(progress_events) > 0, "Should have received progress messages"
        assert len(result_events) > 0, "Should have received result cards"
        assert done_event is not None, "Should have received done event"
        assert done_event.get("total") == len(result_events)

    print("\nALL SERVER ENDPOINTS & SSE STREAMING TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_fastapi_server())
