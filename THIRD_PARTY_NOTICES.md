# Third-party notices

Everything Maa keeps third-party runtimes separate from its MIT-licensed source tree.

| Component | Upstream license | Distribution policy |
| --- | --- | --- |
| [create-maa-project](https://github.com/Windsland52/create-maa-project) | AGPL-3.0-or-later | `create-maa-project@latest`; referenced as an external project lifecycle CLI/MCP runtime and its upstream Skill or README is read at use time, never vendored. |
| [MaaMCP](https://github.com/MAA-AI/MaaMCP) | AGPL-3.0-or-later | `maa-mcp==1.2.3`; referenced as an external Python/uv runtime and not vendored. |
| [maafw-cli](https://github.com/otowa-kotori/maafw-cli) | MIT | `maafw-cli==0.1.6`; cataloged as an optional experimental CLI and not vendored or installed by default. |
| [MaaEvidenceKit](https://github.com/Windsland52/MaaEvidenceKit) (formerly MaaDiagnosticExpert) | MIT | `maa-evidence-kit@latest`; its user-managed npm runtime and external `maa-evidence` Skill or README are discovered at use time by `maa-diagnose`, never vendored or persistently installed by Everything Maa. On-demand `npx @latest` execution may refresh the user-level npm cache. |
| [MaaLogAnalyzer](https://github.com/MaaXYZ/MaaLogAnalyzer) | MIT | Consumed only through MaaEvidenceKit's log adapter; its packages are not vendored or invoked directly by Everything Maa. |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | Apache-2.0 | `@playwright/mcp@0.0.78`; referenced as an external npm runtime and not vendored. |
| [MaaFramework](https://github.com/MaaXYZ/MaaFramework) | LGPL-3.0 | Used through its public protocol/runtime; binaries are not bundled here. |
| [MaaLLMWiki](https://github.com/Windsland52/MaaLLMWiki) | No upstream license declared | The `maa-wiki` skill references the upstream `maallmwiki` Skill and catalog through raw GitHub and disclosed jsDelivr URLs; neither is vendored or downloaded by Everything Maa. |

MaaHub adapter metadata records distribution information only. Do not copy third-party MaaHub content into this repository without confirming its license and provenance.
