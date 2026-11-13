# Maa CLI Operate

通过默认解析 latest 的 maafw-cli，以严格 JSON 输出执行 MaaFramework 设备发现、命名会话、识别、动作与 Pipeline 操作；用户明确指定版本时仍可固定该版本。

## 适用场景

- 在 CI 或脚本中验证 Pipeline。
- 用低上下文命令完成“观察—动作—验证”。
- 管理 ADB、Win32、PlayCover 或 wlroots 控制器会话。
- 在 maafw-cli 与持续会话型 MaaMCP 之间选择合适运行时。

实现位于 `skills/maa-cli-operate/SKILL.md`，MaaHub 发布元信息位于 `adapters/maahub/skills/maa-cli-operate.json`。
