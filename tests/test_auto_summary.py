import os
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock


class DummyLLMResponse:
    def __init__(self, completion=""):
        self.completion = completion


class DummyEvent:
    def __init__(self, user_id, message_text):
        self.unified_msg_origin = f"private:{user_id}"
        self.message_str = message_text
        self.get_sender_id = lambda: user_id


def test_auto_summary_updates_profile_after_interval(dummy_context, dummy_config):
    from main import WorldviewMaturityPlugin, UserProfileStore

    tmpdir = tempfile.mkdtemp()
    dummy_config["profile_data_dir"] = tmpdir
    dummy_config["summary_interval"] = 2
    try:
        plugin = WorldviewMaturityPlugin(dummy_context, dummy_config)
        for i in range(2):
            event = DummyEvent("u1", f"消息 {i}")
            resp = DummyLLMResponse("回复")
            import asyncio
            asyncio.run(plugin.on_llm_response(event, resp))

        store = UserProfileStore(tmpdir, max_facts=dummy_config["max_profile_facts"])
        profile = store.get("u1")
        assert profile["interaction_count"] >= 2
    finally:
        shutil.rmtree(tmpdir)


def test_auto_summary_disabled_when_user_profile_off(dummy_context):
    from main import WorldviewMaturityPlugin

    tmpdir = tempfile.mkdtemp()
    config = {
        "enabled": True,
        "user_profile_enabled": False,
        "auto_learn_enabled": False,
        "profile_data_dir": tmpdir,
    }
    try:
        plugin = WorldviewMaturityPlugin(dummy_context, config)
        event = DummyEvent("u1", "消息")
        resp = DummyLLMResponse("回复")
        import asyncio
        asyncio.run(plugin.on_llm_response(event, resp))
        assert plugin.user_profile_enabled is False
    finally:
        shutil.rmtree(tmpdir)
