import os
import json
import pytest
import tempfile
import shutil


def test_profile_store_creates_default_profile():
    from worldview_maturity.user_profile import UserProfileStore

    tmpdir = tempfile.mkdtemp()
    try:
        store = UserProfileStore(tmpdir, max_facts=5)
        profile = store.get("user_001")
        assert profile["user_id"] == "user_001"
        assert profile["facts"] == []
        assert profile["preferences"] == {}
        assert os.path.exists(os.path.join(tmpdir, "user_001.json"))
    finally:
        shutil.rmtree(tmpdir)


def test_profile_store_saves_and_reads_fact():
    from worldview_maturity.user_profile import UserProfileStore

    tmpdir = tempfile.mkdtemp()
    try:
        store = UserProfileStore(tmpdir, max_facts=5)
        store.add_fact("user_001", "用户喜欢猫", category="兴趣")
        profile = store.get("user_001")
        assert any(item["fact"] == "用户喜欢猫" for item in profile["facts"])
    finally:
        shutil.rmtree(tmpdir)


def test_profile_store_deduplicates_facts():
    from worldview_maturity.user_profile import UserProfileStore

    tmpdir = tempfile.mkdtemp()
    try:
        store = UserProfileStore(tmpdir, max_facts=5)
        store.add_fact("user_001", "用户喜欢猫")
        store.add_fact("user_001", "用户喜欢猫")
        profile = store.get("user_001")
        assert len(profile["facts"]) == 1
    finally:
        shutil.rmtree(tmpdir)


def test_profile_store_enforces_max_facts():
    from worldview_maturity.user_profile import UserProfileStore

    tmpdir = tempfile.mkdtemp()
    try:
        store = UserProfileStore(tmpdir, max_facts=3)
        for i in range(5):
            store.add_fact("user_001", f"事实 {i}")
        profile = store.get("user_001")
        assert len(profile["facts"]) == 3
    finally:
        shutil.rmtree(tmpdir)
