# Checklist

- [ ] 联网搜索函数工具已按 Spec 注册到 AstrBot 上下文
- [ ] LLM 在时效性问题上能按需触发联网搜索（工具可被调用）
- [ ] 搜索工具对成功返回、空结果、请求失败三种场景均有稳定处理
- [ ] `@filter.on_llm_request()` 钩子正确向 system_prompt 追加检索引导
- [ ] 禁用插件配置时不再注入提示、不执行检索
- [ ] `metadata.yaml` 与 `_conf_schema.json` 已创建且字段完整
- [ ] 配置项包含启用开关、搜索 API 地址、API Key、返回条数、超时时间
- [ ] 所有新增测试在实现前先失败、实现后通过（TDD）
- [ ] 测试全部通过，无新增 lint/type 错误
