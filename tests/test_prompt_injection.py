import pytest
import asyncio
from unittest.mock import MagicMock


class DummyProviderRequest:
    def __init__(self):
        self.system_prompt = "你是一个 helpful assistant。"


def test_on_llm_request_appends_search_hint(dummy_context, dummy_config):
    from main import WorldviewMaturityPlugin

    plugin = WorldviewMaturityPlugin(dummy_context, dummy_config)
    req = DummyProviderRequest()
    event = MagicMock()

    async def run():
        await plugin.on_llm_request(event, req)
        assert "联网搜索" in req.system_prompt or "实时" in req.system_prompt

    asyncio.run(run())


def test_on_llm_request_skips_when_disabled(dummy_context):
    from main import WorldviewMaturityPlugin

    config = {"enabled": False}
    plugin = WorldviewMaturityPlugin(dummy_context, config)
    req = DummyProviderRequest()
    original = req.system_prompt
    event = MagicMock()

    async def run():
        await plugin.on_llm_request(event, req)
        assert req.system_prompt == original

    asyncio.run(run())
