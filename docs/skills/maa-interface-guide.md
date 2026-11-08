# Maa Interface Guide

审查、诊断和修改已有的 MaaFramework Project Interface V2。

## 适用场景

- 解释现有 `interface.json`、import、controller、resource 和 task 的关系。
- 修改 group、option、preset、setting 或国际化声明。
- 检查 schema、路径、task entry 和跨文件引用。
- 使用项目已有工具或经用户许可的 `npx @nekosu/maa-tools` 做增强诊断。

## 边界

本 skill 不支持 Project Interface v1，也不从零创建 Interface。项目或 Interface 不存在时应先使用 `maa-project-create`。它可以维护 Interface 侧的 option 声明；涉及 `pipeline_override` 行为、Pipeline 节点或 Python 读取时，由 `maa-pipeline-option` 负责闭环。

实现位于 `skills/maa-interface-guide/SKILL.md`，MaaHub 发布元信息位于 `adapters/maahub/skills/maa-interface-guide.json`。
