# Maa Pipeline History Audit

审计 Maa 系列项目的 Git 历史，追踪主 Interface 与 import 声明、声明资源中的 Pipeline、数据表和 Python Agent 自定义实现如何演进。

## 适用场景

- 从初始提交到目标提交总结项目演进。
- 映射 `action: Custom` 与 AgentServer 注册实现。
- 查找历史回归、约定变化和可沉淀的 skill 改进。

历史路径从目标提交的主 Interface、`import[]` 与 `resource[].path` 推导，不假设 `assets/...` 布局；验证命令优先使用目标项目锁定的脚本。

实现位于 `skills/maa-pipeline-history-audit/SKILL.md`，MaaHub 发布元信息位于 `adapters/maahub/skills/maa-pipeline-history-audit.json`。
