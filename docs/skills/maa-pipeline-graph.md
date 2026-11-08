# Maa Pipeline Graph

分析 MaaFramework 主 Interface / import 声明、声明资源中的 Pipeline 和 Python 调用关系，生成状态机视图并发现孤立节点、未解析引用和跨文件流程问题。

## 适用场景

- 重构前梳理 Pipeline 架构。
- 检查 `next`、`on_error`、中断与跳转关系。
- 对齐 interface 入口、Pipeline 节点和 Python `run_task` 调用。

实现位于 `skills/maa-pipeline-graph/SKILL.md`，MaaHub 发布元信息位于 `adapters/maahub/skills/maa-pipeline-graph.json`。
