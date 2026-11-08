# Everything Maa

Everything Maa is a focused toolkit of reusable AI skills for MaaFramework projects. Its canonical content covers intent-to-workflow orchestration, project creation and discovery, Project Interface maintenance, Pipeline authoring and generation, option wiring, graph analysis, testing, history auditing, guarded CLI operation, and official Maa knowledge routing.

> Status: published toolkit baseline. The canonical skills, native plugin manifests, MCP profiles, and installer are covered by local and CI checks; the npm package and GitHub repository are public.

## Install

Install into a project with one of these commands:

```bash
npx everything-maa@latest install --target claude
npx everything-maa@latest install --target codex
```

For a local checkout, replace `npx everything-maa@latest` with `node packages/cli/bin/everything-maa.js`.

Claude Code can also install the native plugin through its self-hosted marketplace:

```text
/plugin marketplace add https://github.com/KhazixW2/Everything-Maa
/plugin install everything-maa@everything-maa
```

The default `core` profile installs all thirteen skills and configures MaaMCP. Profiles are explicit and versioned:

| Profile | Installed components |
| --- | --- |
| `skills-only` | Maa skills only |
| `core` | Maa skills + MaaMCP |
| `authoring` | Core + create-maa-project project lifecycle MCP |
| `full` | Authoring + isolated Playwright MCP |

Useful operations:

```bash
npx everything-maa list
npx everything-maa doctor
npx everything-maa install --target codex --profile authoring
npx everything-maa install --target codex --profile full --dry-run
npx everything-maa uninstall --target codex
```

Project scope is the default. User-scope skill installation is available through `--scope user`; Claude user-scope MCP merging is intentionally excluded because it would require editing Claude's shared global configuration. Use `--profile skills-only`, project scope, or the native plugin in that case.

The installer records exactly what it owns. Uninstall removes an installed skill only when its content still matches the recorded hash, preserves unrelated MCP entries, and leaves locally modified content in place with recovery state.

## Core skills

| Skill | Purpose |
| --- | --- |
| `maa-workflow-build` | Compile ambiguous automation requests into verified end-to-end Maa workflows. |
| `maa-cli-operate` | Run repeatable device, recognition, action, and Pipeline operations through maafw-cli. |
| `maa-project-create` | Create, extend, diagnose, and update Maa projects through create-maa-project. |
| `maa-project-init` | Scan a Maa project and produce a reusable `basic_info.md` handoff. |
| `maa-wiki` | Route MaaFramework knowledge questions and other Maa skills to authoritative official documentation, schemas, APIs, bindings, releases, and semantic changes. |
| `maa-interface-guide` | Review, diagnose, and modify an existing Project Interface V2 with optional `@nekosu/maa-tools` validation. |
| `maa-pipeline-guide` | Design and review MaaFramework Pipeline JSON. |
| `maa-pipeline-generate` | Generate recognition/action nodes and sweep OCR ROIs. |
| `maa-pipeline-option` | Wire runtime options across UI, Pipeline, and Python. |
| `maa-pipeline-testing` | Validate resources, recognition, Custom wiring, and runtime flows. |
| `maa-diagnose` | Load the authoritative MaaEvidenceKit guidance, then diagnose an unexplained failure read-only and return one bounded failure owner. |
| `maa-pipeline-graph` | Map Pipeline state relationships and external Python entries. |
| `maa-pipeline-history-audit` | Learn Pipeline and Custom conventions from Git history. |

Project-specific workflows belong under `recipes/` and are not installed as core skills.

## Repository layout

- `skills/`: canonical Maa skills; each directory is independently installable.
- `recipes/`: optional project or task recipes.
- `evals/`: skill evaluation cases kept outside installed skill payloads.
- `adapters/`: distribution metadata for MaaHub and future agent harnesses.
- `distribution/`: versioned status and paths for every supported release channel.
- `integrations/`: runtime routing metadata for MCP and optional CLI tools.
- `mcp/`: versioned MCP server catalog and profiles.
- `.claude-plugin/` and `.codex-plugin/`: native plugin manifests.
- `packages/cli/`: dependency-free Node.js installer.
- `tests/`: portable fixtures and repository invariants.
- `.github/workflows/`: cross-platform CI and tag-gated trusted publishing.

The completed six-phase roadmap and remaining public-release gate are documented in [docs/roadmap.md](docs/roadmap.md).

## Development

```bash
uv sync
uv run python -m pytest
uv run python scripts/validate_skills.py
npm test
npm run release:check
npm pack --dry-run
```

When changing the create-maa-project integration, also run the networked upstream smoke test:

```bash
npm run smoke:create-project
```

When changing the maafw-cli integration, run its non-device upstream contract smoke test:

```bash
npm run smoke:maafw-cli
```

The current baseline supports Python 3.10 and later and Node.js 18 and later. Do not assume a skill is installed under `.claude/skills`, a particular drive letter, or the Everything Maa checkout itself.

## Scope and dependencies

Everything Maa does not vendor create-maa-project, MaaEvidenceKit, MaaMCP, maafw-cli, Playwright MCP, MaaFramework binaries, OCR models, `@nekosu/maa-tools`, the MaaLLMWiki `maallmwiki` Skill, its catalog, or Project Interface V2 protocol snapshots. MCP and CLI launch contracts reference upstream packages; create-maa-project and MaaEvidenceKit track latest and hand off to the upstream README or integrated Skill. The `maa-wiki` skill hands off to the raw upstream `maallmwiki` Skill and does not download, cache, or copy that Skill or catalog content into installations; Interface and option guidance resolves protocol semantics through project evidence and pinned upstream documentation and schemas. MaaMCP, create-maa-project, and the experimental maafw-cli skill require `uvx`; Playwright MCP and `@nekosu/maa-tools` require `npx`. Maafw-cli runs on demand without persistent installation by a profile. When invoking MaaEvidenceKit, resolve `maa-evidence-kit@latest` on demand with `npx`; reject a stale `maa-evidence` executable from `PATH`.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for license boundaries and [README.zh-CN.md](README.zh-CN.md) for Chinese documentation.

## License

Everything Maa's own skills, scripts, tests, and documentation are released under the [MIT License](LICENSE). Third-party runtimes keep their upstream licenses.

Everything Maa is a community project and is not an official MaaFramework distribution unless explicitly stated otherwise.
