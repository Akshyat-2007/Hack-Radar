"""Production LLMProvider powered by Google Gemini API."""
from __future__ import annotations

import json
import logging
from typing import Any
import httpx

from hackradar.providers.base import LLMProvider

logger = logging.getLogger("hackradar.llm.gemini")

# Priority list of Gemini models to support high-throughput, low-latency structured output
FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
]


class RealLLMProvider(LLMProvider):
    """Production LLM provider using Google Gemini structured JSON outputs."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "gemini-flash-lite-latest",
        endpoint: str = "",
    ) -> None:
        self.api_key = api_key
        self.model = model or "gemini-flash-lite-latest"
        self.endpoint = endpoint or "https://generativelanguage.googleapis.com/v1beta"
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def extract_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Extract structured JSON adhering strictly to schema using Gemini."""
        if not self.api_key:
            raise RuntimeError("Gemini API key is not configured in LLM_API_KEY / GEMINI_API_KEY.")

        client = self._get_client()
        system_instruction = (
            "You are a structured hackathon data extractor. "
            "You MUST reply with ONLY valid JSON adhering strictly to the requested schema. "
            "Do not include explanation or markdown formatting."
        )

        full_prompt = (
            f"{system_instruction}\n\n"
            f"SCHEMA:\n{json.dumps(schema, indent=2)}\n\n"
            f"{prompt}"
        )

        payload = {
            "contents": [
                {
                    "parts": [{"text": full_prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
            },
        }

        # Try active model then fallbacks if demand is high
        models_to_try = [self.model] + [m for m in FALLBACK_MODELS if m != self.model]
        last_error = ""

        for m in models_to_try:
            url = f"{self.endpoint}/models/{m}:generateContent?key={self.api_key}"
            try:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    resp_json = res.json()
                    candidates = resp_json.get("candidates", [])
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts or "text" not in parts[0]:
                        continue
                    raw_text = parts[0]["text"].strip()
                    # Strip any accidental ```json ... ``` wrapper
                    if raw_text.startswith("```json"):
                        raw_text = raw_text[7:]
                    elif raw_text.startswith("```"):
                        raw_text = raw_text[3:]
                    if raw_text.endswith("```"):
                        raw_text = raw_text[:-3]
                    raw_text = raw_text.strip()
                    return json.loads(raw_text)
                else:
                    last_error = f"HTTP {res.status_code}: {res.text[:200]}"
                    logger.warning(f"Gemini model {m} returned {last_error}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Gemini call to {m} failed: {e}")

        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
