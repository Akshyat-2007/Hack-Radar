# HackRadar 🎯

An intelligent hackathon finder web app that scans, verifies, eligibility-checks, and ranks hackathons based on user academic profile, skills, and location.

---

## 5-Line Architecture

1. **Profile-to-Queries**: Generates 5–6 targeted queries across online, city, stream, skill, and national scopes using system date.
2. **Parallel Provider Adapters**: Searches and fetches candidates via abstract `SearchProvider` and `FetchProvider` interfaces with URL deduplication.
3. **Structured Extraction**: Extracts validated Pydantic schemas via `LLMProvider` without hallucinating missing fields.
4. **Filtering & Normalization**: Prunes expired deadlines, foreign in-person events, and location mismatches while deduplicating cross-platform mirrors.
5. **Scoring & SSE Streaming**: Evaluates academic/theme/location fit (0–100) and streams real-time progress and cards directly to the frontend.

---

## Quickstart & Setup

### 1. Prerequisites
- Python 3.11+
- Virtual environment with dependencies (`pip install -e .` or `pip install fastapi uvicorn pydantic httpx python-dotenv pytest`)

### 2. Environment Configuration
Copy `.env.example` to `.env` (preconfigured to run offline with sample data):
```bash
cp hackradar/.env.example .env
```
Default setting:
```bash
USE_MOCKS=true
```

### 3. Run the App (One Command)
Start the FastAPI server:
```bash
uvicorn hackradar.main:app --reload
```
Then open your browser at:
**[http://localhost:8000](http://localhost:8000)**

---

## Testing

Run the automated test suite covering deduplication, filters, and end-to-end streaming:
```bash
# Run pytest on dedupe and filter logic
pytest hackradar/tests/test_dedupe_and_filters.py

# Run end-to-end server & SSE streaming verification
python hackradar/tests/test_server_e2e.py
```

---

## Swapping in Real APIs
See [INTEGRATION.md](file:///c:/Users/akshy/OneDrive/Desktop/quad%20ai/INTEGRATION.md) for a checklist of method signatures and how to flip `USE_MOCKS=false`.
