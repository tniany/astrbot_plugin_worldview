import os
import pytest
import tempfile
import shutil


def test_profile_store_creates_default_profile():
    from main import UserProfileStore

    tmpdir = tempfile.mkdtemp()
    try:
        store = UserProfileStore(tmpdir, max_facts=5)
        profile = store.get("user_create")
        assert profile["user_id"] == "user_create"
        assert profile["facts"] == []
        assert profile["preferences"] == {}
        assert os.path.exists(os.path.join(tmpdir, "user_create.json"))
    finally:
        shutil.rmtree(tmpdir)


def test_profile_store_saves_and_reads_fact():
    from main import UserProfileStore

    tmpdir = tempfile.mkdtemp()
    try:
        store = UserProfileStore(tmpdir, max_facts=5)
        store.add_fact("user_save", "用户喜欢猫", category="兴趣")
        profile = store.get("user_save")
        assert any(item["fact"] == "用户喜欢猫" for item in profile["facts"])
    finally:
        shutil.rmtree(tmpdir)


def test_profile_store_deduplicates_facts():
    from main import UserProfileStore

    tmpdir = tempfile.mkdtemp()
    try:
        store = UserProfileStore(tmpdir, max_facts=5)
        store.add_fact("user_dedup", "用户喜欢猫")
        store.add_fact("user_dedup", "用户喜欢猫")
        profile = store.get("user_dedup")
        assert len(profile["facts"]) == 1
    finally:
        shutil.rmtree(tmpdir)


def test_profile_store_enforces_max_facts():
    from main import UserProfileStore

    tmpdir = tempfile.mkdtemp()
    try:
        store = UserProfileStore(tmpdir, max_facts=3)
        for i in range(5):
            store.add_fact("user_max", f"事实 {i}")
        profile = store.get("user_max")
        assert len(profile["facts"]) == 3
    finally:
        shutil.rmtree(tmpdir)
