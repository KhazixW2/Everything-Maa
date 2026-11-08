# Maa Project Create

通过外部 create-maa-project 生命周期引擎创建、扩展、诊断和更新 MaaFramework 项目，不复制其 AGPL 模板或源码。

## 适用场景

- 创建 Pipeline 或 Python Agent 项目。
- 添加开发工具、GitHub workflows、Agent 或资源包。
- 运行 doctor、sync、显式 update、备份检查和恢复预演。
- 创建完成后衔接 Maa Project Init。

## 上游 Skill 定位

- 首次组 MCP/CLI 操作前，先运行 `skills/maa-project-create/scripts/find-create-maa-project-skill.mjs`。
- locator 会报告显式 checkout、独立 Skill、项目 npm 包与 npm/pnpm 全局包候选，但这些候选不覆盖权威指引。
- 无论 locator 结果如何，都解析最新正式 Release，优先读取其集成的上游 Skill，缺失时回退 README。
- 无法读取完整权威指引时安全停止；运行时始终通过未锁定版本的 latest 引用解析。

实现位于 `skills/maa-project-create/SKILL.md`，MaaHub 发布元信息位于 `adapters/maahub/skills/maa-project-create.json`。
