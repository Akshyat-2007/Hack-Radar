# HackRadar - API Integration Checklist

HackRadar is built on a clean provider adapter architecture. To transition from the mock implementation to live external APIs, follow the checklist below. **No changes to pipeline, schemas, or frontend code are needed.**

---

## 1. How to Switch to Live APIs

In your `.env` file, change:
```bash
USE_MOCKS=false
```
And add your API keys:
```bash
SEARCH_API_KEY=your_search_api_key_here
FETCH_API_KEY=your_reader_api_key_here
LLM_API_KEY=your_llm_api_key_here
LLM_MODEL=gpt-4o-mini # or gemini-2.5-flash / claude-3-5-sonnet
```

---

## 2. Files to Implement

### `hackradar/providers/real_search.py`
- **Class**: `RealSearchProvider(SearchProvider)`
- **Recommended API**: Serper (`https://google.serper.dev/search`), Brave Search API, or Tavily.
- **Method Signature**:
  ```python
  async def search(self, query: str) -> list[SearchHit]:
  ```
- **Expected Return Shape**:
  List of `SearchHit` instances:
  ```python
  [
      SearchHit(
          title="Bengaluru AI Buildathon",
          url="https://techsparks.in/bengaluru-ai-buildathon-2026",
          snippet="48-hour in-person hackathon in Bengaluru..."
      ),
      ...
  ]
  ```

---

### `hackradar/providers/real_fetch.py`
- **Class**: `RealFetchProvider(FetchProvider)`
- **Recommended API**: Jina Reader (`https://r.jina.ai/{url}`) or Firecrawl (`https://api.firecrawl.dev/v1/scrape`).
- **Method Signature**:
  ```python
  async def fetch(self, url: str) -> str:
  ```
- **Expected Return Shape**:
  `str` containing clean markdown text of the webpage. If the request fails, return `""` (empty string) so the pipeline continues gracefully.

---

### `hackradar/providers/real_llm.py`
- **Class**: `RealLLMProvider(LLMProvider)`
- **Recommended API**: OpenAI (`gpt-4o-mini` with `response_format={"type": "json_object"}`), Google Gemini (`response_mime_type="application/json"`), or Anthropic Claude.
- **Method Signature**:
  ```python
  async def extract_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
  ```
- **Expected Return Shape**:
  A Python `dict` strictly matching `ExtractedEvent`:
  ```json
  {
    "name": "Hackathon Name",
    "organizer": "Organizer or null",
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null",
    "registration_deadline": "YYYY-MM-DD or null",
    "mode": "online | in-person | hybrid",
    "city": "City or null",
    "country": "Country or null",
    "eligibility_text": "Exact rules text from page or null",
    "student_only": true,
    "allowed_streams": ["CSE", "IT"],
    "allowed_years": ["3", "4"],
    "team_size_min": 1,
    "team_size_max": 4,
    "themes": ["AI", "Web3"],
    "prize": "₹5,00,000",
    "url": "https://..."
  }
  ```

---

### `hackradar/providers/real_agent.py` (Optional)
- **Class**: `RealAgentProvider(AgentProvider)`
- **Method Signature**:
  ```python
  async def run(self, goal: str, url: str) -> dict[str, Any]:
  ```
- **Expected Return Shape**:
  `{"status": "success", "url": url, "findings": {...}}`

---

## 3. Provider Factory Verification

`hackradar/providers/__init__.py` automatically inspects `USE_MOCKS`:
- When `USE_MOCKS=true`: loads `Mock*Provider` reading local fixtures.
- When `USE_MOCKS=false`: loads `Real*Provider` calling your newly implemented APIs.
