# Changelog

All notable changes to Everything Maa will be documented in this file. The project follows Semantic Versioning after the first public release.

## [Unreleased]

### Changed

- `maa-wiki` now loads MaaLLMWiki's authoritative `maallmwiki` Skill before catalog navigation and uses disclosed raw, jsDelivr, and README fallbacks while preserving pinned-source citation requirements.
- `maa-wiki` now gives explicit version requests precedence, resolves target-project runtime and lock conflicts before choosing upstream defaults, and routes Interface protocol discovery through the upstream `maallmwiki` Skill with the root README only as a disclosed fallback.

## [0.2.0] - 2026-10-06

### Added

- Strengthened `maa-diagnose` to locate and fully load the authoritative MaaEvidenceKit Skill before runtime discovery and diagnosis.
- `maa-wiki` skill that routes MaaFramework knowledge questions and other Maa skills to authoritative official documentation, schemas, APIs, bindings, releases, and semantic changes through the MaaLLMWiki catalog.
- Added `maa-interface-guide` for reviewing, diagnosing, and modifying existing MaaFramework Project Interface V2 files with project-first schema resolution and guarded `maa-tools` validation.
- Added `maa-diagnose`, a read-only diagnostic skill that discovers and drives the external MaaEvidenceKit runtime (formerly MaaDiagnosticExpert) over local logs, project sources, and run-state context instead of implementing another log parser or diagnostic engine. It resolves the runtime surface dynamically, applies one MCP-then-CLI-then-local-checkout precedence policy, consumes only the structured JSON contract, and normalizes results into findings, evidence, artifacts, next actions, and one bounded `failure_owner`.
- Added orchestration routing so `maa-workflow-build` `RECOVER` requests diagnostic evidence only when the failure owner is unknown, keeps focused recognition failures with `maa-pipeline-generate` and `maa-pipeline-testing`, and decides retry, replan, delegation, user action, or stop from the returned owner.
- Cataloged `maa-evidence-kit@0.3.2` as an optional user-managed external diagnostic runtime with its supported version range, structured schema ids, and third-party notices; `everything-maa doctor` now reports external runtimes alongside MCP and optional CLI integrations.
- Added an `EXPLORE` phase to `maa-workflow-build` that gates DESIGN behind observed UI evidence: start and success states now carry an `evidence_status`, a guessed state opens an exploration-first gate, and the run state records the round-trip observations that close it.
- Added coordinate-hygiene guidance to `maa-pipeline-guide` covering the `DirectHit` plus hardcoded `target` and recognized-then-offset anti-patterns, OCR- and TemplateMatch-based click replacements, and the conditions under which an anchored offset is still acceptable.

### Changed

- Replaced local Project Interface V2 protocol snapshots and version matrices with `$maa-wiki` routing, project-first schema resolution, and pinned upstream source discovery. Interface and option guidance now keep only workflow, reference, and wiring boundaries locally, while `pretask`, Agent `PI_*`, telemetry, resource hash, preset, option type, and field semantics remain under upstream authority.
- Updated README release status and installation guidance for the published npm package and public GitHub repository, aligned Chinese development commands with the `uv`-based CI workflow, and documented the Project Interface V2 no-local-snapshot dependency boundary.
- Changed create-maa-project and MaaEvidenceKit integration policy from tested version pins to latest: create-maa-project resolves through `uvx --upgrade --from create-maa-project`, while MaaEvidenceKit remains externally user-managed and invokes its CLI on demand through `maa-evidence-kit@latest`, rejecting stale `PATH` executables; both locators expose latest Release, README, and integrated-Skill handoffs instead of a fixed CMP digest or MEK version range.
- `maa-diagnose` and `maa-project-create` now load authoritative guidance from the upstream latest Release Skill or README instead of selecting local guidance by version metadata.
- Pipeline node authoring now derives click targets from recognition results across `maa-pipeline-guide`, `maa-pipeline-generate`, and `maa-workflow-build`, instead of presenting a hardcoded `target_offset` as a default pattern.
- `maa-pipeline-testing` documents that recognition success does not prove the click landed, and records the current lack of an ROI-limited `run_pipeline` in MaaMCP together with the ways to keep single-node verification cheap.

### Fixed

- `maa-project-init`'s `analyze_pipeline_project.py` now parses node-level `anchor` declarations (`string | list | object` forms) into an anchor-name -> target-node table and redirects `[Anchor]X` references through it, instead of reporting every anchor reference as an unresolved node reference. This also corrects the derived `zero_in_degree_nodes`, `isolated_nodes`, and `orphan_candidates` stats, which previously misclassified anchor-only-reachable nodes as unreachable. An anchor name that is never declared and a declared anchor whose explicit target node does not exist are now reported separately (`unresolved_anchor_refs` vs. `dangling_anchor_targets`), and a single anchor name mapping to multiple target nodes is treated as normal rather than a conflict.
- `analyze_pipeline_project.py` no longer crashes with `UnicodeEncodeError` on Windows consoles (cp1252/cp936) when pipeline node names contain non-ASCII characters.

## [0.1.1] - 2026-07-19

### Added

- End-to-end Maa workflow orchestration that connects project initialization, Pipeline authoring, options, graph analysis, testing, and specialist feedback loops.
- Project initialization guidance that visualizes Python custom action and AgentServer relationships.

### Changed

- Upgraded GitHub Actions runtimes used by CI and release workflows.
- Made project context initialization and Pipeline graph invocation explicit in the orchestration contract.

### Fixed

- Defined ownership of specialist feedback loops so generated Maa workflows return to the correct orchestration stage.

## [0.1.0] - 2026-07-15

### Added

- Ten MaaFramework lifecycle skills covering intent-to-workflow orchestration, project creation and discovery, Pipeline authoring, generation, options, graphing, testing, history auditing, and CLI operation.
- Versioned `skills-only`, `core`, `authoring`, and `full` installation profiles for Codex and Claude Code.
- External integrations for MaaMCP, create-maa-project, maafw-cli, and isolated Playwright MCP.
- Dependency-free `everything-maa` installer with dry-run, doctor, managed uninstall, and conflict recovery.
- Cross-platform tests, upstream contract smoke tests, native plugin manifests, and release validation.
- Self-hosted Claude marketplace metadata, a complete ten-skill MaaHub adapter set, and a machine-readable distribution catalog.

[Unreleased]: https://github.com/KhazixW2/Everything-Maa/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/KhazixW2/Everything-Maa/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/KhazixW2/Everything-Maa/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/KhazixW2/Everything-Maa/releases/tag/v0.1.0
