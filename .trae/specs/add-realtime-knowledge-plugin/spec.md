# 实时资讯联网检索插件 Spec

## Why
一般人格的 bot 受限于模型训练截止时间，对最新资讯、热梗等"地球 Online"实时动态理解不足，回复显得冰冷、机械、脱节。需要让 LLM 能够按需自主联网检索实时信息，并把检索结果融入回复，让人设更鲜活、贴近当下。

## What Changes
- 新增一个 AstrBot 插件，向 LLM 注册一个"联网搜索"函数工具（FunctionTool），由 LLM 在需要时自主决定调用。
- 通过 `@filter.on_llm_request()` 钩子，在系统提示中告知 LLM：当遇到可能涉及最新资讯、热梗、时效性内容时，应主动调用联网搜索工具补全认知。
- 搜索工具使用 `aiohttp`/`httpx` 异步请求一个可配置的搜索 API，返回精炼后的实时信息供 LLM 参考。
- 通过 `_conf_schema.json` 暴露可配置项（搜索 API 地址、API Key、返回条数、超时时间、是否启用等）。
- 检索结果按需注入对话上下文，让 LLM 持续迭代完善对现实世界的认知。

## Impact
- Affected specs: 联网检索能力、LLM 函数工具能力、插件配置能力
- Affected code:
  - `main.py`(新建，插件主文件)
  - `metadata.yaml`(新建，插件元数据)
  - `_conf_schema.json`(新建，插件配置 Schema)
  - `tests/`(新建，TDD 测试)

## ADDED Requirements

### Requirement: 联网搜索函数工具
The system SHALL 向 LLM 注册一个联网搜索函数工具，使 LLM 能够在对话中按需自主检索实时资讯。

#### Scenario: LLM 主动检索最新资讯
- **WHEN** 用户询问涉及最新资讯或热梗等时效性内容
- **THEN** LLM 调用联网搜索工具，工具异步请求搜索 API 并返回精炼后的实时结果

#### Scenario: 搜索结果为空或失败
- **WHEN** 搜索 API 返回空结果或请求失败
- **THEN** 工具返回明确的无结果/错误提示，而不抛出未捕获异常

### Requirement: LLM 请求提示注入
The system SHALL 通过 LLM 请求钩子提示 LLM 在遇到时效性内容时优先使用联网搜索工具。

#### Scenario: 注入引导提示
- **WHEN** 触发一次 LLM 请求
- **THEN** 在 system_prompt 中追加引导文本，告知 LLM 可调用联网搜索工具补全实时认知

### Requirement: 插件配置
The system SHALL 提供可配置项以控制搜索行为。

#### Scenario: 读取配置
- **WHEN** 插件初始化
- **THEN** 从 AstrBotConfig 读取搜索 API 地址、API Key、返回条数、超时时间、启用开关等配置
