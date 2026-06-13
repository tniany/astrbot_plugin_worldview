# Tasks

- [ ] Task 1: 建立测试基础并先写失败测试
  - [ ] SubTask 1.1: 确认项目可用的 Python 测试方式，优先使用已有测试框架；若无现成配置，则使用最小 `pytest` 风格测试
  - [ ] SubTask 1.2: 编写联网搜索工具的失败测试，覆盖成功返回、空结果、请求失败三个行为
  - [ ] SubTask 1.3: 编写 LLM 请求提示注入的失败测试，验证 system_prompt 会追加时效性检索引导
  - [ ] SubTask 1.4: 运行测试并确认这些测试因功能尚未实现而失败

- [ ] Task 2: 实现联网搜索工具最小可用能力
  - [ ] SubTask 2.1: 创建 AstrBot 插件主类并继承 `Star`
  - [ ] SubTask 2.2: 实现 `FunctionTool`，支持按查询词异步请求配置的搜索 API
  - [ ] SubTask 2.3: 将 API 响应精炼为 LLM 易读的文本结果
  - [ ] SubTask 2.4: 处理空结果、超时、网络错误和无效响应，返回安全可读的提示
  - [ ] SubTask 2.5: 注册联网搜索工具到 AstrBot 上下文

- [ ] Task 3: 实现 LLM 时效性提示注入
  - [ ] SubTask 3.1: 使用 `@filter.on_llm_request()` 监听 LLM 请求
  - [ ] SubTask 3.2: 在 system_prompt 中追加简洁人设与联网检索引导
  - [ ] SubTask 3.3: 确保禁用插件配置时不注入提示、不注册或不执行检索能力

- [ ] Task 4: 增加插件元数据与配置 Schema
  - [ ] SubTask 4.1: 创建 `metadata.yaml`，声明插件名称、描述、版本、作者和 AstrBot 版本范围
  - [ ] SubTask 4.2: 创建 `_conf_schema.json`，包含启用开关、搜索 API 地址、API Key、返回条数、超时时间等字段
  - [ ] SubTask 4.3: 确保配置项有合理默认值，敏感字段不被日志输出

- [ ] Task 5: 跑通 TDD 验证与代码质量检查
  - [ ] SubTask 5.1: 运行目标测试，确认先前失败测试已经通过
  - [ ] SubTask 5.2: 运行项目可用的 lint/typecheck/格式化检查；若项目没有命令，则说明缺失并至少运行可用测试
  - [ ] SubTask 5.3: 修复测试或检查发现的问题，保持实现最小且符合规格

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 can run after Task 1 and may与 Task 2/Task 3 并行
- Task 5 depends on Task 2, Task 3, and Task 4
