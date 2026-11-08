# Maa Diagnose

在失败原因仍然未知时，只读地驱动外部诊断运行时（[MaaEvidenceKit](https://github.com/Windsland52/MaaEvidenceKit)，原名 MaaDiagnosticExpert），把 MaaFramework 日志、项目静态定义和运行上下文汇聚成规范化证据与唯一失败责任方。

## 适用场景

- 运行、任务或测试已经失败，但责任方尚未确定。
- 资源或 schema 加载失败、环境或依赖问题、设备错误、运行超时、分支走错、Custom 异常。
- 大体量 MaaFramework 日志需要时间线与节点级关联。
- 需要在重新规划前检索本地 MaaFramework 文档与仓库说明。

## 不适用场景

- `$maa-pipeline-testing` 已经定位到责任方时，直接把证据交给该责任方，不要再触发广义诊断。
- 项目脚手架与受管文件健康检查属于 `$maa-project-create` 的 doctor。
- Project Interface schema 审查属于 `$maa-interface-guide`。
- 日志解析、可视化与统计属于 MaaLogAnalyzer，本仓库通过诊断运行时消费，不重复实现。

## 名称选择

最终名称为 `maa-diagnose`，与 `maa-project-create` 的 `doctor` 用语不重叠：`doctor` 面向项目脚手架健康，`maa-diagnose` 面向失败后的跨工具取证与责任归属。

## 权威指引定位

- 诊断命令拼装前，先运行 `skills/maa-diagnose/scripts/find-maa-evidence-skill.mjs`。
- 显式提供的 checkout、包根目录或 Skill 路径优先；随后查找已安装的独立 `maa-evidence` Skill、项目/用户安装与 npm/pnpm 全局包。
- 无论 locator 找到什么本地候选，都读取最新正式 Release 的集成 Skill，缺失时回退 README；只有无正式版本才回退默认分支并说明该回退。
- 本地 Skill 与包路径只作为 locator 诊断结果，不覆盖 latest upstream handoff。
- 无法读取完整权威 Skill 或 README 时安全停止，不根据记忆拼装 MaaEvidenceKit 命令。

## 运行时契约

- 每次会话先执行发现（`--version` 与 `--help`），不缓存命令目录；上游已经改名并变更过命令名。
- 单一优先级策略：仅当本地 MCP 已配置且包元数据与 npm latest 一致时使用；随后使用按需执行的 `npx --yes --package maa-evidence-kit@latest maa-evidence`；最后才是用户明确授权且版本能证明与 npm latest 完全一致的 checkout，否则停止。绝不使用裸 `PATH` 可执行文件或旧版本。
- 只解析结构化 JSON 输出，不把人类可读文本或图形渲染当作主契约。
- 运行时缺失或契约不兼容时安全失败，不安装、不构建、不升级。
- latest 指引加载与契约变更行为见 `skills/maa-diagnose/references/runtime-discovery.md`。

## 输出

```yaml
status: success | warning | error
summary: one-line diagnostic result
findings: []
evidence: []
artifacts: []
next_actions: []
failure_owner: generate | option | testing | workflow-design | workflow-implement | project-create | user
stop_reason: null
```

结果返回 `$maa-workflow-build` 的 `RECOVER` 阶段，由其决定重试、重新设计、委派修复、请求用户操作还是停止。本 skill 只给出建议，绝不自动执行修复。

实现位于 `skills/maa-diagnose/SKILL.md`，权威 Skill 定位器位于 `skills/maa-diagnose/scripts/find-maa-evidence-skill.mjs`，责任映射位于 `skills/maa-diagnose/references/failure-map.md`，MaaHub 发布元信息位于 `adapters/maahub/skills/maa-diagnose.json`。
