import asyncio
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import aiohttp

from astrbot.api import logger
from astrbot.api.star import Context, Star
from astrbot.api import FunctionTool
from astrbot.api.event import filter

from worldview_maturity.user_profile import UserProfileStore
from worldview_maturity.personality import PersonalityLearner


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
        timeout = aiohttp.ClientTimeout(total=int(self.config.get("timeout", 5)))

        if not url:
            return "搜索失败：未配置搜索 API 地址。"

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
            return event.get_sender_id()
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
