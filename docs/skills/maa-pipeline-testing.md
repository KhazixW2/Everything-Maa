# Maa Pipeline Testing

本目录包含 MaaFramework pipeline 节点测试指南。

## 包含内容

- `SKILL.md`: testing 说明文档
- `adapters/maahub/skills/maa-pipeline-testing.json`: MaaHub 发布元信息

## 作用

本 skill 介绍如何使用 `run_pipeline` 测试 pipeline 节点、判断识别结果、以及处理跨页面导航测试风险。测试对象从主 Interface 的 `import[]` 与 `resource[].path` 发现，不假设 `assets/...` 布局；项目锁定检查优先，例如 M9A 使用 `pnpm check`。
