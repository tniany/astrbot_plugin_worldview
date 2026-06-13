import pytest
import asyncio
from unittest.mock import MagicMock


class DummyContext:
    def __init__(self):
        self.tools = []

    def add_llm_tools(self, tool):
        self.tools.append(tool)


class DummyConfig(dict):
    pass


@pytest.fixture
def dummy_context():
    return DummyContext()


@pytest.fixture
def dummy_config():
    return DummyConfig(
        {
            "enabled": True,
            "search_api_url": "https://api.example.com/search",
            "api_key": "test-key",
            "max_results": 3,
            "timeout": 5,
        }
    )


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
