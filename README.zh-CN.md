# Everything Maa

Everything Maa 是一个严格面向 MaaFramework 项目的 AI skills 工具集。核心范围包括从意图到工作流的编排、项目创建与发现、Project Interface 维护、Pipeline 编写与生成、选项接线、节点图谱、测试、历史审计、受控 CLI 操作和官方 Maa 知识路由。

> 当前状态：已发布基线。规范化 skills、原生插件清单、MCP profiles 和安装器都有本地与 CI 检查；npm 包与 GitHub 仓库已公开。

## 安装

可用下面任一命令安装到当前项目：

```bash
npx everything-maa@latest install --target claude
npx everything-maa@latest install --target codex
```

在本地仓库试用时，将 `npx everything-maa@latest` 替换为 `node packages/cli/bin/everything-maa.js`。

Claude Code 也可以通过自托管 marketplace 安装原生插件：

```text
/plugin marketplace add https://github.com/KhazixW2/Everything-Maa
/plugin install everything-maa@everything-maa
```

默认 `core` profile 会安装全部 13 个 skills 并配置 MaaMCP。四个 profile 的边界是固定且版本化的：

| Profile | 安装内容 |
| --- | --- |
| `skills-only` | 仅 Maa skills |
| `core` | Maa skills + MaaMCP |
| `authoring` | Core + create-maa-project 项目生命周期 MCP |
| `full` | Authoring + 隔离模式 Playwright MCP |

常用操作：

```bash
npx everything-maa list
npx everything-maa doctor
npx everything-maa install --target codex --profile authoring
npx everything-maa install --target codex --profile full --dry-run
npx everything-maa uninstall --target codex
```

默认安装到项目级。`--scope user` 可安装用户级 skills；Claude 用户级 MCP 合并暂不支持，因为这需要修改 Claude 的共享全局配置。该场景请选择 `--profile skills-only`、项目级安装或原生插件。

安装器只管理自己写入的内容。卸载时仅删除哈希仍与安装记录一致的 skill，保留无关 MCP 配置，并保留用户修改过的内容与恢复状态。

## 核心 skills

| Skill | 用途 |
| --- | --- |
| `maa-workflow-build` | 将模糊自动化需求编译为可验证的端到端 Maa 工作流。 |
| `maa-cli-operate` | 通过 maafw-cli 执行可重复的设备、识别、动作和 Pipeline 操作。 |
| `maa-project-create` | 通过 create-maa-project 创建、扩展、诊断和更新 Maa 项目。 |
| `maa-project-init` | 扫描 Maa 项目并生成可复用的 `basic_info.md` 接力文档。 |
| `maa-wiki` | 将 MaaFramework 知识问题和其它 Maa skills 路由到权威官方文档、schema、API、binding、release 与语义变化。 |
| `maa-interface-guide` | 审查、诊断和修改已有的 Project Interface V2，并可通过 `@nekosu/maa-tools` 校验。 |
| `maa-pipeline-guide` | 设计、修改和审查 MaaFramework Pipeline JSON。 |
| `maa-pipeline-generate` | 生成识别/动作节点并扫描 OCR ROI。 |
| `maa-pipeline-option` | 贯通 UI、Pipeline 与 Python 的运行时选项。 |
| `maa-pipeline-testing` | 验证资源、识别、Custom 映射和端到端流程。 |
| `maa-diagnose` | 责任方未知时，加载权威 MaaEvidenceKit 指引，只读诊断失败并给出唯一失败责任方。 |
| `maa-pipeline-graph` | 梳理 Pipeline 状态关系与 Python 外部入口。 |
| `maa-pipeline-history-audit` | 从 Git 历史学习 Pipeline 与 Custom 约定。 |

项目专用工作流放在 `recipes/`，不作为核心 skills 默认安装。

## 仓库结构

- `skills/`：规范化 Maa skills，每个目录可独立安装。
- `recipes/`：可选的项目或任务配方。
- `evals/`：与安装载荷分离的 skill 评测用例。
- `adapters/`：MaaHub 及后续 agent 平台的分发元数据。
- `distribution/`：所有支持发行渠道的版本化状态与路径。
- `integrations/`：MCP 与可选 CLI 工具的运行时路由元数据。
- `mcp/`：版本化 MCP 服务器目录与 profiles。
- `.claude-plugin/` 与 `.codex-plugin/`：原生插件清单。
- `packages/cli/`：无运行时依赖的 Node.js 安装器。
- `tests/`：跨平台 fixture 和仓库结构约束。
- `.github/workflows/`：跨平台 CI 与标签门控的可信发布流程。

已完成的六阶段路线图和剩余公开发布门槛见 [docs/roadmap.md](docs/roadmap.md)。

## 开发与验证

```bash
uv sync
uv run python -m pytest
uv run python scripts/validate_skills.py
npm test
npm run release:check
npm pack --dry-run
```

修改 create-maa-project 集成时，还需运行连接上游发行包的冒烟测试：

```bash
npm run smoke:create-project
```

修改 maafw-cli 集成时，运行不连接设备的上游命令契约冒烟测试：

```bash
npm run smoke:maafw-cli
```

当前基线支持 Python 3.10 及以上、Node.js 18 及以上。skill 不得假设自己安装在 `.claude/skills`、固定盘符或 Everything Maa 源码目录中。

## 范围与依赖

Everything Maa 不复制 create-maa-project、MaaEvidenceKit、MaaMCP、maafw-cli、Playwright MCP、MaaFramework 二进制、OCR 模型、`@nekosu/maa-tools`、MaaLLMWiki 的 `maallmwiki` Skill、catalog 或 Project Interface V2 协议快照。MCP 与 CLI 命令契约只调用上游发行包；create-maa-project 与 MaaEvidenceKit 跟踪 latest，并衔接上游 README 或集成 Skill。`maa-wiki` skill 衔接 raw GitHub URL 上的上游 `maallmwiki` Skill，不下载、缓存或复制该 Skill 和 catalog 内容到安装目录；Interface 与 option 指南通过项目证据和 pinned 上游文档/schema 解析协议语义。MaaMCP、create-maa-project 和实验性的 maafw-cli skill 需要 `uvx`，Playwright MCP 和 `@nekosu/maa-tools` 需要 `npx`；maafw-cli 仅按需运行，不由 profile 持久安装。调用 MaaEvidenceKit 时，通过 `npx` 按需解析 `maa-evidence-kit@latest`；不要回退到 `PATH` 中的旧 `maa-evidence` 可执行文件。

许可证边界见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 许可证

Everything Maa 自有的 skills、脚本、测试和文档使用 [MIT License](LICENSE)。第三方运行时继续遵守各自的上游许可证。

Everything Maa 是社区项目；除非另有明确说明，它不是 MaaFramework 官方发行版。
