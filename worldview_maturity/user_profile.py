import json
import logging
import os
from typing import Any, Dict, Optional

try:
    from astrbot.api import logger
except Exception:
    logger = logging.getLogger(__name__)


DEFAULT_PROFILE = {
    "user_id": "",
    "facts": [],
    "preferences": {},
    "style_summary": "",
    "interaction_count": 0,
    "last_summary_text": "",
}


class UserProfileStore:
    def __init__(self, data_dir: str, max_facts: int = 50):
        self.data_dir = data_dir
        self.max_facts = max_facts
        os.makedirs(self.data_dir, exist_ok=True)

    def _profile_path(self, user_id: str) -> str:
        safe_id = "".join(c for c in user_id if c.isalnum() or c in ("-", "_"))
        return os.path.join(self.data_dir, f"{safe_id}.json")

    def get(self, user_id: str) -> Dict[str, Any]:
        path = self._profile_path(user_id)
        if not os.path.exists(path):
            profile = {**DEFAULT_PROFILE, "user_id": user_id}
            self._save(profile)
            return profile
        try:
            with open(path, "r", encoding="utf-8") as f:
                profile = json.load(f)
        except Exception as e:
            logger.error(f"读取用户档案失败 ({user_id}): {e}")
            profile = {**DEFAULT_PROFILE, "user_id": user_id}
        for key, value in DEFAULT_PROFILE.items():
            profile.setdefault(key, value)
        profile["user_id"] = user_id
        return profile

    def _save(self, profile: Dict[str, Any]) -> None:
        path = self._profile_path(profile["user_id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    def add_fact(
        self,
        user_id: str,
        fact: str,
        category: Optional[str] = None,
    ) -> str:
        if not fact or not fact.strip():
            return "记录失败：缺少有效事实内容。"

        profile = self.get(user_id)
        existing = [item["fact"] for item in profile["facts"]]
        if fact in existing:
            return "该事实已存在，未重复记录。"

        item = {"fact": fact, "category": category or "general"}
        profile["facts"].append(item)
        if len(profile["facts"]) > self.max_facts:
            profile["facts"] = profile["facts"][-self.max_facts:]

        try:
            self._save(profile)
            return "已记录用户事实。"
        except Exception as e:
            logger.error(f"写入用户档案失败 ({user_id}): {e}")
            return f"记录失败：{e}"

    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> None:
        profile = self.get(user_id)
        profile.update(updates)
        self._save(profile)
