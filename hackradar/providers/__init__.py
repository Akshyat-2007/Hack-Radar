"""Providers factory.

Returns either Mock or Real provider implementations based on USE_MOCKS setting.
Nothing outside providers/ needs to know which implementation is active.
"""
from __future__ import annotations

from typing import NamedTuple

from hackradar.config import settings
from hackradar.providers.base import (
    AgentProvider,
    FetchProvider,
    LLMProvider,
    SearchProvider,
)
from hackradar.providers.mock_agent import MockAgentProvider
from hackradar.providers.mock_fetch import MockFetchProvider
from hackradar.providers.mock_llm import MockLLMProvider
from hackradar.providers.mock_search import MockSearchProvider
from hackradar.providers.real_agent import RealAgentProvider
from hackradar.providers.real_fetch import RealFetchProvider
from hackradar.providers.real_llm import RealLLMProvider
from hackradar.providers.real_search import RealSearchProvider


class Providers(NamedTuple):
    search: SearchProvider
    fetch: FetchProvider
    llm: LLMProvider
    agent: AgentProvider


def get_search_provider() -> SearchProvider:
    if settings.use_mocks:
        return MockSearchProvider()
    return RealSearchProvider(api_key=settings.search_api_key, endpoint=settings.search_endpoint)


def get_fetch_provider() -> FetchProvider:
    if settings.use_mocks:
        return MockFetchProvider()
    return RealFetchProvider(api_key=settings.fetch_api_key, endpoint=settings.fetch_endpoint)


def get_llm_provider() -> LLMProvider:
    if settings.use_mocks:
        return MockLLMProvider()
    return RealLLMProvider(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        endpoint=settings.llm_endpoint,
    )


def get_agent_provider() -> AgentProvider:
    if settings.use_mocks:
        return MockAgentProvider()
    return RealAgentProvider(api_key=settings.agent_api_key, endpoint=settings.agent_endpoint)


def get_providers() -> Providers:
    """Return all configured providers as a tuple."""
    return Providers(
        search=get_search_provider(),
        fetch=get_fetch_provider(),
        llm=get_llm_provider(),
        agent=get_agent_provider(),
    )


__all__ = [
    "SearchProvider",
    "FetchProvider",
    "LLMProvider",
    "AgentProvider",
    "Providers",
    "get_search_provider",
    "get_fetch_provider",
    "get_llm_provider",
    "get_agent_provider",
    "get_providers",
]
