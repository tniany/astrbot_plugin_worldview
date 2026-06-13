# AstrBot 文档知识库

> 整合自：https://github.com/AstrBotDevs/AstrBot/tree/master/docs

---

## 目录

1. [插件开发指南](#插件开发指南)
2. [消息事件与消息链](#消息事件与消息链)
3. [平台适配矩阵](#平台适配矩阵)
4. [事件监听器](#事件监听器)
5. [消息发送](#消息发送)
6. [插件配置](#插件配置)
7. [AI 与 LLM 调用](#ai-与-llm-调用)
8. [会话控制](#会话控制)

---

## 插件开发指南

### 最小实例

```python
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star
from astrbot.api import logger

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        '''这是一个 hello world 指令'''
        user_name = event.get_sender_name()
        message_str = event.message_str
        logger.info("触发hello world指令!")
        yield event.plain_result(f"Hello, {user_name}!")

    async def terminate(self):
        '''插件卸载时调用'''
```

### 插件结构说明

1. 插件继承自 `Star` 基类
2. `__init__` 方法接收 `Context` 对象，包含 AstrBot 大多数组件
3. Handler 必须在插件类中定义，前两个参数为 `self` 和 `event`
4. 插件主文件命名为 `main.py`

### metadata.yaml

```yaml
name: 插件名称
description: 插件描述
version: 1.0.0
author: 作者名
display_name: 展示名  # 可选
support_platforms:    # 可选
  - telegram
  - aiocqhttp
astrbot_version: ">=4.16,<5"  # 可选
```

---

## 消息事件与消息链

### AstrMessageEvent

消息事件对象，获取发送者、消息内容等信息。

### AstrBotMessage

```python
class AstrBotMessage:
    type: MessageType          # 消息类型
    self_id: str               # 机器人ID
    session_id: str            # 会话ID
    message_id: str            # 消息ID
    group_id: str              # 群组ID（私聊为空）
    sender: MessageMember      # 发送者
    message: List[BaseMessageComponent]  # 消息链
    message_str: str           # 纯文本消息
    raw_message: object        # 原始消息对象
    timestamp: int             # 时间戳
```

### 消息链

```python
import astrbot.api.message_components as Comp

chain = [
    Comp.Plain(text="Hello"),
    Comp.At(qq=123456),
    Comp.Image(file="https://example.com/image.jpg")
]
```

**消息类型**：

| 类型 | 说明 |
|------|------|
| `Plain` | 文本消息 |
| `At` | @某人 |
| `Image` | 图片 |
| `Record` | 语音 |
| `Video` | 视频 |
| `Face` | QQ表情 |
| `Reply` | 回复消息 |
| `File` | 文件 |

---

## 平台适配矩阵

| 平台 | At | Plain | Image | Record | Video | Reply | 主动消息 |
|------|----|----|----|----|----|----|----|
| QQ个人号(aiocqhttp) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Telegram | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| QQ官方接口 | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 飞书 | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 企业微信 | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 钉钉 | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 事件监听器

### 指令注册

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("echo")
async def echo(self, event: AstrMessageEvent, message: str):
    yield event.plain_result(f"你发了: {message}")
```

### 带参指令

```python
@filter.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a + b}")
```

### 指令组

```python
@filter.command_group("math")
def math(self):
    pass

@math.command("add")
async def add(self, event: AstrMessageEvent, a: int, b: int):
    yield event.plain_result(f"结果是: {a + b}")
```

### 事件类型过滤

```python
# 接收所有消息
@filter.event_message_type(filter.EventMessageType.ALL)
async def on_all_message(self, event: AstrMessageEvent):
    yield event.plain_result("收到了一条消息。")

# 仅私聊
@filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
async def on_private_message(self, event: AstrMessageEvent):
    yield event.plain_result("收到了一条私聊消息。")

# 指定平台
@filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
async def on_aiocqhttp(self, event: AstrMessageEvent):
    yield event.plain_result("收到了QQ消息")

# 管理员指令
@filter.permission_type(filter.PermissionType.ADMIN)
@filter.command("admin_cmd")
async def admin_cmd(self, event: AstrMessageEvent):
    pass
```

### 事件钩子

```python
# Bot 初始化完成
@filter.on_astrbot_loaded()
async def on_astrbot_loaded(self):
    print("AstrBot 初始化完成")

# LLM 请求前
@filter.on_llm_request()
async def my_hook(self, event: AstrMessageEvent, req: ProviderRequest):
    req.system_prompt += "自定义内容"

# LLM 响应后
@filter.on_llm_response()
async def on_llm_resp(self, event: AstrMessageEvent, resp: LLMResponse):
    print(resp)

# 发送消息前
@filter.on_decorating_result()
async def on_decorating_result(self, event: AstrMessageEvent):
    result = event.get_result()
    result.chain.append(Comp.Plain("!"))

# 发送消息后
@filter.after_message_sent()
async def after_message_sent(self, event: AstrMessageEvent):
    pass
```

---

## 消息发送

### 被动消息

```python
@filter.command("test")
async def test(self, event: AstrMessageEvent):
    yield event.plain_result("Hello!")
    yield event.image_result("path/to/image.jpg")
    yield event.image_result("https://example.com/image.jpg")
```

### 主动消息

```python
from astrbot.api.event import MessageChain

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    umo = event.unified_msg_origin
    message_chain = MessageChain().message("Hello!").file_image("path/to/image.jpg")
    await self.context.send_message(umo, message_chain)
```

### 富媒体消息

```python
import astrbot.api.message_components as Comp

@filter.command("test")
async def test(self, event: AstrMessageEvent):
    chain = [
        Comp.At(qq=event.get_sender_id()),
        Comp.Plain("来看这个图："),
        Comp.Image.fromURL("https://example.com/image.jpg"),
        Comp.Plain("这是一个图片。")
    ]
    yield event.chain_result(chain)
```

### 控制事件传播

```python
@filter.command("check")
async def check(self, event: AstrMessageEvent):
    ok = self.check()
    if not ok:
        yield event.plain_result("检查失败")
        event.stop_event()  # 停止事件传播
```

---

## 插件配置

### Schema 定义

在插件目录下创建 `_conf_schema.json`：

```json
{
  "token": {
    "description": "Bot Token",
    "type": "string",
    "hint": "测试醒目提醒",
    "obvious_hint": true
  },
  "sub_config": {
    "description": "嵌套配置",
    "type": "object",
    "items": {
      "name": {
        "description": "名称",
        "type": "string"
      },
      "enabled": {
        "description": "是否启用",
        "type": "bool",
        "default": true
      }
    }
  }
}
```

### 使用配置

```python
from astrbot.api import AstrBotConfig

class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        print(self.config["token"])
```

---

## AI 与 LLM 调用

### 获取提供商

```python
# 当前使用的 LLM 提供商
prov = self.context.get_using_provider(umo=event.unified_msg_origin)

# 根据 ID 获取
prov = self.context.get_provider_by_id(provider_id="xxxx")

# 获取所有
provs = self.context.get_all_providers()
```

### 调用 LLM

```python
@filter.command("test")
async def test(self, event: AstrMessageEvent):
    prov = self.context.get_using_provider(umo=event.unified_msg_origin)
    if prov:
        llm_resp = await prov.text_chat(
            prompt="Hi!",
            context=[
                {"role": "user", "content": "balabala"},
                {"role": "assistant", "content": "response"}
            ],
            system_prompt="You are a helpful assistant."
        )
        print(llm_resp)
```

### 函数工具

```python
from astrbot.api import FunctionTool
from dataclasses import dataclass, field

@dataclass
class HelloWorldTool(FunctionTool):
    name: str = "hello_world"
    description: str = "Say hello to the world."
    parameters: dict = field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "greeting": {"type": "string", "description": "The greeting message."}
        },
        "required": ["greeting"]
    })

    async def run(self, event: AstrMessageEvent, greeting: str):
        return f"{greeting}, World!"
```

注册工具：

```python
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.context.add_llm_tools(HelloWorldTool())
```

---

## 会话控制

用于需要多次对话的场景（如成语接龙）。

```python
from astrbot.core.utils.session_waiter import session_waiter, SessionController

@filter.command("成语接龙")
async def handle(self, event: AstrMessageEvent):
    yield event.plain_result("请发送一个成语~")

    @session_waiter(timeout=60, record_history_chains=False)
    async def waiter(controller: SessionController, event: AstrMessageEvent):
        idiom = event.message_str

        if idiom == "退出":
            await event.send(event.plain_result("已退出"))
            controller.stop()
            return

        if len(idiom) != 4:
            await event.send(event.plain_result("成语必须是四个字"))
            return

        await event.send(event.plain_result("先见之明"))
        controller.keep(timeout=60, reset_timeout=True)

    try:
        await waiter(event)
    except TimeoutError:
        yield event.plain_result("你超时了！")
    finally:
        event.stop_event()
```

### SessionController 方法

| 方法 | 说明 |
|------|------|
| `keep(timeout, reset_timeout)` | 保持会话 |
| `stop()` | 结束会话 |
| `get_history_chains()` | 获取历史消息链 |

---

## 开发原则

1. 功能需经过测试
2. 包含良好的注释
3. 持久化数据存储于 `data` 目录
4. 良好的错误处理机制
5. 使用 `ruff` 格式化代码
6. 使用 `aiohttp`/`httpx` 而非 `requests`
7. 优先给原插件提交 PR 而非新建插件