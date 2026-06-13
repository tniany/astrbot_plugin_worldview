# Tasks

- [ ] Task 1: 建立测试基础并先写失败测试
  - [ ] SubTask 1.1: 编写用户档案读写失败测试
  - [ ] SubTask 1.2: 编写 `record_user_fact` 工具失败测试（正常记录、去重、写入失败）
  - [ ] SubTask 1.3: 编写人格风格学习提示生成失败测试
  - [ ] SubTask 1.4: 编写自动总结触发失败测试
  - [ ] SubTask 1.5: 运行测试确认因功能缺失而失败

- [ ] Task 2: 实现用户档案系统
  - [ ] SubTask 2.1: 创建 `UserProfileStore` 类，管理 `data/worldview_maturity/users/{user_id}.json`
  - [ ] SubTask 2.2: 实现档案读取、创建默认值、安全写入
  - [ ] SubTask 2.3: 实现事实去重与 `max_profile_facts` 限制

- [ ] Task 3: 实现 `record_user_fact` 函数工具
  - [ ] SubTask 3.1: 定义 `RecordUserFactTool` 并注册到 AstrBot 上下文
  - [ ] SubTask 3.2: 工具接收 `fact` 与可选 `category`，写入用户档案
  - [ ] SubTask 3.3: 处理写入失败与参数缺失

- [ ] Task 4: 实现人格风格自适应
  - [ ] SubTask 4.1: 创建 `PersonalityLearner`，分析用户最近 `style_window_size` 条消息
  - [Task 4.2: 生成简短风格适配提示，追加到 system_prompt
  - [ ] SubTask 4.3: 支持 `auto_learn_enabled` 开关

- [ ] Task 5: 实现自动总结机制
  - [ ] SubTask 5.1: 使用 `@filter.on_llm_response()` 监听回复
  - [ ] SubTask 5.2: 维护每用户对话轮数计数
  - [ ] SubTask 5.3: 达到 `summary_interval` 时触发轻量总结并更新档案

- [ ] Task 6: 扩展插件主类与配置
  - [ ] SubTask 6.1: 将 `RealtimeSearchPlugin` 扩展/重命名为 `WorldviewMaturityPlugin`
  - [ ] SubTask 6.2: 在 `on_llm_request` 中按序注入档案摘要、风格提示、联网搜索引导
  - [ ] SubTask 6.3: 更新 `_conf_schema.json` 新增配置项
  - [ ] SubTask 6.4: 更新 `README.md` 说明新能力

- [ ] Task 7: 跑通 TDD 验证与代码质量检查
  - [ ] SubTask 7.1: 运行目标测试，确认先前失败测试已通过
  - [ ] SubTask 7.2: 运行可用 lint/type 检查或至少保证 py_compile 通过
  - [ ] SubTask 7.3: 提交并推送代码到 GitHub

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 1
- Task 5 depends on Task 2
- Task 6 depends on Task 2, Task 3, Task 4
- Task 7 depends on Task 6
