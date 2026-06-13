import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import aiohttp
except Exception:
    aiohttp = None

try:
    from astrbot.api import logger
    from astrbot.api.star import Context, Star
    from astrbot.api import FunctionTool
    from astrbot.api.event import filter
except Exception:
    logger = logging.getLogger(__name__)

    class Star:
        def __init__(self, context):
            self.context = context

    class FunctionTool:
        pass

    class filter:
        @staticmethod
        def on_llm_request():
            def decorator(fn):
                return fn
            return decorator

        @staticmethod
        def on_llm_response():
            def decorator(fn):
                return fn
            return decorator

    class Context:
        pass


@dataclass
class WebSearchTool(FunctionTool):
    name: str = "web_search"
    description: str = (
        "当用户问题涉及最新资讯、热梗、时事、网络流行内容等时效性信息时，"
        "调用此工具进行联网搜索，补全对现实世界的认知。"
    )
    parameters: dict = field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用于搜索实时资讯的关键词。",
            }
        },
        "required": ["query"],
    })

    def __init__(self, config: dict):
        super().__init__()
        self.config = config

    async def run(self, event, query: str) -> str:
        if not self.config.get("enabled", True):
            return "联网搜索功能已禁用。"

        url = self.config.get("search_api_url", "").strip()
        api_key = self.config.get("api_key", "").strip()
        max_results = int(self.config.get("max_results", 3))
        timeout = aiohttp.ClientTimeout(total=int(self.config.get("timeout", 5))) if aiohttp else None

        if not url:
            return "搜索失败：未配置搜索 API 地址。"

        if aiohttp is None:
            return "搜索失败：aiohttp 未安装。"

        headers = {}
        params = {"q": query, "num": max_results}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            params["key"] = api_key

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        return f"搜索失败：HTTP {resp.status}"
                    data = await resp.json()
        except asyncio.TimeoutError:
            return "搜索失败：请求超时。"
        except Exception as e:
            logger.error(f"联网搜索出错: {e}")
            return f"搜索失败：{e}"

        return self._refine(data, max_results)

    def _refine(self, data: dict, max_results: int) -> str:
        results = data.get("results", []) if isinstance(data, dict) else []
        if not results:
            return "未找到相关实时信息。"

        lines = []
        for item in results[:max_results]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("url", "")
            if title or snippet:
                lines.append(f"- {title}: {snippet} ({link})")

        if not lines:
            return "未找到可读的实时信息。"

        return "\n".join(["实时检索结果："] + lines)


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
        if not safe_id:
            safe_id = "unknown"
        return os.path.join(self.data_dir, f"{safe_id}.json")

    def get(self, user_id: str) -> Dict[str, Any]:
        path = self._profile_path(user_id)
        if not os.path.exists(path):
            profile = {**DEFAULT_PROFILE, "user_id": user_id, "facts": []}
            self._save(profile)
            return profile
        try:
            with open(path, "r", encoding="utf-8") as f:
                profile = json.load(f)
        except Exception as e:
            logger.error(f"读取用户档案失败 ({user_id}): {e}")
            profile = {**DEFAULT_PROFILE, "user_id": user_id, "facts": []}
        for key, value in DEFAULT_PROFILE.items():
            if key == "facts":
                profile.setdefault(key, [])
            else:
                profile.setdefault(key, value)
        profile["user_id"] = user_id
        return profile

    def _save(self, profile: Dict[str, Any]) -> None:
        path = self._profile_path(profile["user_id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    def add_fact(self, user_id: str, fact: str, category: Optional[str] = None) -> str:
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


class PersonalityLearner:
    def __init__(self, window_size: int = 10):
        self.window_size = window_size

    def generate_hint(self, user_messages: List[str]) -> str:
        messages = [m for m in user_messages if isinstance(m, str) and m.strip()]
        if len(messages) < 2:
            return ""

        recent = messages[-self.window_size:]
        hints = []

        emoji_ratio = sum(1 for m in recent if self._has_emoji(m)) / len(recent)
        if emoji_ratio > 0.3:
            hints.append("用户喜欢使用表情符号，可适当使用 emoji 回应")

        short_ratio = sum(1 for m in recent if len(m) <= 15) / len(recent)
        if short_ratio > 0.5:
            hints.append("用户习惯简短回复，回答宜简洁")
        elif sum(len(m) for m in recent) / len(recent) > 80:
            hints.append("用户倾向完整表达，回答可适当详细")

        if any(m.endswith(("~", "～", "!", "！")) for m in recent):
            hints.append("用户语气较活泼，可保持轻松亲切")

        if not hints:
            return ""

        return "风格适配提示（在保持原有人设基础上）：" + "；".join(hints) + "。"

    def _has_emoji(self, text: str) -> bool:
        for char in text:
            if ord(char) > 0x1F300:
                return True
        return False


@dataclass
class RecordUserFactTool(FunctionTool):
    name: str = "record_user_fact"
    description: str = (
        "当你认为用户表达了值得长期记忆的信息（如兴趣、偏好、重要经历、关系、习惯等）时，"
        "调用此工具将其记录到用户档案中，以便后续对话更了解用户。"
    )
    parameters: dict = field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "用户唯一标识。",
            },
            "fact": {
                "type": "string",
                "description": "需要记录的用户事实，用简洁的一句话描述。",
            },
            "category": {
                "type": "string",
                "description": "事实类别，如兴趣、偏好、关系、经历等。",
            },
        },
        "required": ["user_id", "fact"],
    })

    def __init__(self, profile_store: UserProfileStore):
        super().__init__()
        self.profile_store = profile_store

    async def run(self, event, user_id: str, fact: str, category: Optional[str] = None) -> str:
        return self.profile_store.add_fact(user_id, fact, category)


class WorldviewMaturityPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.enabled = bool(config.get("enabled", True))
        self.user_profile_enabled = bool(config.get("user_profile_enabled", True))
        self.auto_learn_enabled = bool(config.get("auto_learn_enabled", True))
        self.summary_interval = int(config.get("summary_interval", 5))
        self.style_window_size = int(config.get("style_window_size", 10))

        data_dir = config.get("profile_data_dir") or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "data", "worldview_maturity", "users"
        )
        self.profile_store = UserProfileStore(
            data_dir,
            max_facts=int(config.get("max_profile_facts", 50)),
        )
        self.personality_learner = PersonalityLearner(window_size=self.style_window_size)

        self._recent_messages: Dict[str, List[str]] = {}
        self._interaction_counts: Dict[str, int] = {}

        if self.enabled:
            self.context.add_llm_tools(WebSearchTool(config))
            if self.user_profile_enabled:
                self.context.add_llm_tools(RecordUserFactTool(self.profile_store))
            logger.info("WorldviewMaturityPlugin 已启用。")

    def _get_user_id(self, event) -> Optional[str]:
        try:
            user_id = event.get_sender_id()
            return str(user_id) if user_id is not None else None
        except Exception:
            return None

    @filter.on_llm_request()
    async def on_llm_request(self, event, req):
        if not self.enabled:
            return

        user_id = self._get_user_id(event)
        extras = []

        if user_id and self.user_profile_enabled:
            profile = self.profile_store.get(user_id)
            if profile["facts"]:
                facts_text = "\n".join(f"- {item['fact']}（{item['category']}）" for item in profile["facts"])
                extras.append(f"[用户档案] 关于该用户的已知事实：\n{facts_text}")

            if self.auto_learn_enabled and user_id in self._recent_messages:
                style_hint = self.personality_learner.generate_hint(self._recent_messages[user_id])
                if style_hint:
                    extras.append(style_hint)

        extras.append(
            "[系统提示] 你正在与真实世界交互。"
            "当用户提到最新资讯、时事、热梗、网络流行语或任何可能超出你训练数据的内容时，"
            "请主动调用 `web_search` 联网搜索工具获取实时信息，并将结果融入回答，"
            "使你的回复更贴近当下、更有人格温度。"
        )

        req.system_prompt += "\n\n" + "\n\n".join(extras)

    @filter.on_llm_response()
    async def on_llm_response(self, event, resp):
        if not self.enabled or not self.user_profile_enabled:
            return

        user_id = self._get_user_id(event)
        if not user_id:
            return

        user_text = getattr(event, "message_str", "") or ""
        if user_text:
            self._recent_messages.setdefault(user_id, [])
            self._recent_messages[user_id].append(user_text)
            self._recent_messages[user_id] = self._recent_messages[user_id][-self.style_window_size * 2:]

        self._interaction_counts[user_id] = self._interaction_counts.get(user_id, 0) + 1

        if self._interaction_counts[user_id] % self.summary_interval == 0:
            self._auto_summarize(user_id, user_text, getattr(resp, "completion", ""))

    def _auto_summarize(self, user_id: str, user_text: str, assistant_text: str):
        if not user_text and not assistant_text:
            return
        summary = f"最近对话：用户说「{user_text[:80]}」，助手回应「{assistant_text[:80]}」。"
        self.profile_store.update_profile(user_id, {
            "last_summary_text": summary,
            "interaction_count": self._interaction_counts.get(user_id, 0),
        })

    async def terminate(self):
        pass
