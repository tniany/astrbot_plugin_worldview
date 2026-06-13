# AI 世界观成熟与人格自适应 Spec

## Why

现有插件已能让 LLM 联网检索实时资讯，但 AI 的"成熟"不应止于一次性的信息检索。用户希望 AI 在持续聊天中记住用户偏好、学习用户表达风格、积累专属知识，并在 AstrBot 原有人格基础上自动微调语气，让 AI 越来越像一个真正了解用户、与时俱进的对话伙伴。

## What Changes

- 扩展现有插件为 `WorldviewMaturityPlugin`（保留原有联网搜索能力）。
- 新增用户档案系统，为每个用户持久化偏好、专属事实、表达风格摘要。
- 新增 `record_user_fact` 函数工具，由 LLM 主动选择记录关键信息。
- 新增自动总结机制，每隔若干轮对话自动提炼档案更新。
- 新增人格/风格自适应：分析用户最近发言，生成风格提示追加到 system_prompt，不覆盖 AstrBot 原有人格。
- 新增配置项控制档案、自动学习、自动总结开关及相关参数。
- 更新 `_conf_schema.json`、`README.md` 与测试用例。

## Impact

- Affected specs: 联网检索能力、LLM 函数工具、插件配置、用户画像持久化
- Affected code:
  - `main.py`（扩展主类，新增档案/学习/总结逻辑）
  - `_conf_schema.json`（新增配置项）
  - `README.md`（更新使用说明）
  - `tests/`（新增失败测试）
  - `data/worldview_maturity/users/`（运行时生成的用户档案目录）

## ADDED Requirements

### Requirement: 用户档案持久化
The system SHALL 为每个用户维护一个本地 JSON 档案，记录其偏好、专属事实与互动摘要。

#### Scenario: 读取用户档案
- **WHEN** 触发 LLM 请求
- **THEN** 插件根据用户 ID 读取对应档案；若不存在则创建空档案

#### Scenario: 档案写入
- **WHEN** LLM 调用 `record_user_fact` 或自动总结产生更新
- **THEN** 插件安全地写入 `data/worldview_maturity/users/{user_id}.json`

### Requirement: 主动事实记录工具
The system SHALL 向 LLM 注册 `record_user_fact` 工具，允许 LLM 主动记录用户相关信息。

#### Scenario: 记录重要事实
- **WHEN** LLM 判断某条用户信息值得长期记忆
- **THEN** 调用 `record_user_fact`，写入用户档案的 `facts` 列表，并去重/限制数量

#### Scenario: 记录失败处理
- **WHEN** 写入失败或参数无效
- **THEN** 返回明确错误提示，不抛出未捕获异常

### Requirement: 自动总结与学习
The system SHALL 在每次对话后自动触发轻量总结，更新用户档案。

#### Scenario: 触发自动总结
- **WHEN** 一轮用户-助手对话完成
- **THEN** 若达到配置的 `summary_interval`，基于最近对话提炼新的偏好/事实并更新档案

### Requirement: 人格风格自适应
The system SHALL 根据用户最近发言风格生成适配提示，追加到 system_prompt，且不覆盖 AstrBot 原有人格。

#### Scenario: 生成风格提示
- **WHEN** 触发 LLM 请求
- **THEN** 若启用自动学习，分析用户最近 `style_window_size` 条消息，生成简短的风格适配提示追加到 system_prompt

#### Scenario: 禁用时不影响原人格
- **WHEN** `auto_learn_enabled` 为 false
- **THEN** 不注入任何风格适配提示

### Requirement: 配置扩展
The system SHALL 暴露新的配置项以控制档案、学习与总结行为。

#### Scenario: 读取配置
- **WHEN** 插件初始化
- **THEN** 读取 `user_profile_enabled`、`auto_learn_enabled`、`max_profile_facts`、`style_window_size`、`summary_interval` 等配置

## MODIFIED Requirements

### Requirement: 联网搜索引导提示
原提示仅强调实时资讯检索。修改后，system_prompt 中除联网搜索引导外，还将包含用户档案摘要与风格适配提示，位置在原有引导之前。

## REMOVED Requirements

无
