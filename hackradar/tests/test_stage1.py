import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from hackradar.config import settings
from hackradar.providers import (
    get_providers,
    MockSearchProvider,
    RealSearchProvider,
    MockFetchProvider,
    MockLLMProvider,
)

@pytest.mark.anyio
async def test_stage1():
    print("USE_MOCKS setting:", settings.use_mocks)
    
    mock_search = MockSearchProvider()
    mock_fetch = MockFetchProvider()
    mock_llm = MockLLMProvider()
    
    hits = await mock_search.search("AI hackathons Bengaluru")
    print(f"Hits found: {len(hits)}")
    assert len(hits) > 0
    print(f"Top hit: {hits[0].title} -> {hits[0].url}")
    
    content = await mock_fetch.fetch(hits[0].url)
    print(f"Fetched page length: {len(content)}")
    assert len(content) > 0
    
    extracted = await mock_llm.extract_json(content, {})
    print(f"Extracted event name: {extracted.get('name')}")
    assert extracted.get("name") is not None
    
    # Test real provider instance with empty key
    real = RealSearchProvider(api_key="")
    empty_hits = await real.search("test")
    assert isinstance(empty_hits, list)
    
    print("Stage 1 verification PASSED!")

if __name__ == "__main__":
    asyncio.run(test_stage1())
