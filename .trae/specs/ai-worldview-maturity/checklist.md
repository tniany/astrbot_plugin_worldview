# Checklist

- [ ] 用户档案系统已按 Spec 实现，支持读取、创建、安全写入
- [ ] `record_user_fact` 工具已注册，支持记录、去重、`max_profile_facts` 限制
- [ ] `record_user_fact` 工具对写入失败、参数缺失有稳定处理
- [ ] 人格风格学习模块已按 `style_window_size` 分析用户最近消息并生成提示
- [ ] `auto_learn_enabled` 为 false 时不注入风格提示
- [ ] 自动总结机制通过 `on_llm_response` 触发，按 `summary_interval` 更新档案
- [ ] `on_llm_request` 按序注入档案摘要、风格提示、联网搜索引导
- [ ] `_conf_schema.json` 已包含新增配置项
- [ ] `README.md` 已更新新能力说明
- [ ] 所有新增测试在实现前先失败、实现后通过（TDD）
- [ ] 代码通过 py_compile / lint 检查
- [ ] 修改已提交并推送到 GitHub
