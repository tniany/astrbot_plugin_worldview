import os
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock


def test_record_fact_tool_adds_fact(dummy_context, dummy_config):
    from main import WorldviewMaturityPlugin

    tmpdir = tempfile.mkdtemp()
    dummy_config["profile_data_dir"] = tmpdir
    try:
        plugin = WorldviewMaturityPlugin(dummy_context, dummy_config)
        record_tool = [t for t in dummy_context.tools if getattr(t, "name", "") == "record_user_fact"][0]

        async def run():
            result = await record_tool.run(MagicMock(), user_id="u1", fact="用户喜欢咖啡", category="兴趣")
            assert "已记录" in result

        import asyncio
        asyncio.run(run())
    finally:
        shutil.rmtree(tmpdir)


def test_record_fact_tool_requires_fact(dummy_context, dummy_config):
    from main import WorldviewMaturityPlugin

    tmpdir = tempfile.mkdtemp()
    dummy_config["profile_data_dir"] = tmpdir
    try:
        plugin = WorldviewMaturityPlugin(dummy_context, dummy_config)
        record_tool = [t for t in dummy_context.tools if getattr(t, "name", "") == "record_user_fact"][0]

        async def run():
            result = await record_tool.run(MagicMock(), user_id="u1", fact="", category="兴趣")
            assert "缺少" in result or "无效" in result

        import asyncio
        asyncio.run(run())
    finally:
        shutil.rmtree(tmpdir)
