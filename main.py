import asyncio
import aiohttp
from dataclasses import dataclass, field

from astrbot.api import logger
from astrbot.api.star import Context, Star
from astrbot.api import FunctionTool
from astrbot.api.event import filter


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


class RealtimeSearchPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.enabled = bool(config.get("enabled", True))

        if self.enabled:
            self.context.add_llm_tools(WebSearchTool(config))
            logger.info("RealtimeSearchPlugin 已启用，联网搜索工具已注册。")

    @filter.on_llm_request()
    async def on_llm_request(self, event, req):
        if not self.enabled:
            return

        hint = (
            "\n\n[系统提示] 你正在与真实世界交互。"
            "当用户提到最新资讯、时事、热梗、网络流行语或任何可能超出你训练数据的内容时，"
            "请主动调用 `web_search` 联网搜索工具获取实时信息，并将结果融入回答，"
            "使你的回复更贴近当下、更有人格温度。"
        )
        req.system_prompt += hint

    async def terminate(self):
        pass
