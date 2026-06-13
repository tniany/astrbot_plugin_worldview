import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock


def test_web_search_tool_returns_refined_results(dummy_context, dummy_config):
    from main import WorldviewMaturityPlugin

    plugin = WorldviewMaturityPlugin(dummy_context, dummy_config)
    tool = [t for t in dummy_context.tools if getattr(t, "name", "") == "web_search"][0]

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={
        "results": [
            {"title": "热点 A", "snippet": "摘要 A", "url": "https://a.com"},
            {"title": "热点 B", "snippet": "摘要 B", "url": "https://b.com"},
        ]
    })

    async def run():
        with patch("aiohttp.ClientSession.get", return_value=AsyncContextManager(mock_resp)):
            result = await tool.run(MagicMock(), query="今天的热点")
            assert "热点 A" in result
            assert "摘要 A" in result
            assert "热点 B" in result

    asyncio.run(run())


class AsyncContextManager:
    def __init__(self, obj):
        self.obj = obj

    async def __aenter__(self):
        return self.obj

    async def __aexit__(self, *args):
        pass


def test_web_search_tool_handles_empty_results(dummy_context, dummy_config):
    from main import WorldviewMaturityPlugin

    plugin = WorldviewMaturityPlugin(dummy_context, dummy_config)
    tool = [t for t in dummy_context.tools if getattr(t, "name", "") == "web_search"][0]

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"results": []})

    async def run():
        with patch("aiohttp.ClientSession.get", return_value=AsyncContextManager(mock_resp)):
            result = await tool.run(MagicMock(), query="无结果词")
            assert "未找到" in result or "no results" in result.lower()

    asyncio.run(run())


def test_web_search_tool_handles_request_failure(dummy_context, dummy_config):
    from main import WorldviewMaturityPlugin

    plugin = WorldviewMaturityPlugin(dummy_context, dummy_config)
    tool = [t for t in dummy_context.tools if getattr(t, "name", "") == "web_search"][0]

    async def run():
        with patch("aiohttp.ClientSession.get", side_effect=Exception("network down")):
            result = await tool.run(MagicMock(), query="任意")
            assert "搜索失败" in result or "error" in result.lower()

    asyncio.run(run())
