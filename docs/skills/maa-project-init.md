# Maa Project Init

扫描已有 MaaFramework 项目，生成结构化 `basic_info.md`，把主 Interface、Interface import、声明资源包、Pipeline、Python Agent 和入口关系交给后续工作流。

## 适用场景

- 第一次接手陌生 Maa 项目。
- 在修改 Pipeline 前建立项目事实基线。
- 为 graph、guide、option、testing 等 skills 准备统一上下文。

## 发现规则

- 主 `interface.json` / `interface.jsonc` 是项目结构事实来源。
- `import[]` 与 `resource[].path` 都相对主 Interface 目录解析。
- Interface import 顶层只贡献协议允许的任务、选项和预设声明；资源根仍由主 Interface 声明。
- 根目录与 `assets/` 下的主 Interface 都是常见有效布局；两者同时存在时优先根目录，仅作为确定性选择规则。
- Task 数量表示 import 合并后 Interface bundle 顶层 `task[]` 的总数；分隔线等展示用途条目也计入，另报“功能性任务数”时必须说明过滤规则。

实现位于 `skills/maa-project-init/SKILL.md`，MaaHub 发布元信息位于 `adapters/maahub/skills/maa-project-init.json`。
