from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "maa-interface-guide"


def test_interface_guide_enforces_scope_and_handoffs():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    assert "只接受 V2" in text
    assert "不得生成孤立的 Interface" in text
    assert "$maa-project-create" in text
    assert "$maa-pipeline-option" in text
    assert "Pipeline、Python Agent、图片和构建配置只读" in text


def test_interface_guide_prioritizes_project_evidence_and_uses_project_tooling():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    validation = (SKILL_DIR / "references" / "validation.md").read_text(
        encoding="utf-8"
    )

    assert "项目内证据优先" in text
    assert "$maa-wiki" in text
    assert "pinned revision" in text
    assert "必须先询问用户" in text
    assert "`package.json`" in text
    assert "禁止直接执行 `node_modules`" in text
    assert "会写日志、缓存或其他文件" in text
    assert "packageManager" in validation
    assert "lockfile 一致的包管理器" in validation
    assert "node_modules/.bin" in validation
    assert "npx --no-install @nekosu/maa-tools check" in validation
    assert "只读审查不授权这些写入" in validation
    assert "不以 `npx ... init` 创建配置" in validation


def test_interface_review_guide_documents_controller_resolution_modes():
    review = (SKILL_DIR / "references" / "review-guide.md").read_text(
        encoding="utf-8"
    )

    assert "display_short_side" in review
    assert "display_long_side" in review
    assert "display_expand" in review
    assert "display_raw" in review
    assert "互斥" in review
    assert "短边 720" in review


def test_interface_guide_metadata_adapter_and_evals_are_discoverable():
    metadata = yaml.safe_load(
        (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )
    adapter = json.loads(
        (ROOT / "adapters" / "maahub" / "skills" / "maa-interface-guide.json").read_text(
            encoding="utf-8"
        )
    )
    evals = json.loads(
        (ROOT / "evals" / "maa-interface-guide.json").read_text(encoding="utf-8")
    )

    assert "$maa-interface-guide" in metadata["interface"]["default_prompt"]
    assert adapter["entry"] == "../../../skills/maa-interface-guide/SKILL.md"
    assert evals["skill_name"] == "maa-interface-guide"
    assert len(evals["evals"]) >= 4


def test_interface_guide_documents_maa_tools_in_readmes():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    assert "@nekosu/maa-tools" in english
    assert "@nekosu/maa-tools" in chinese


def test_interface_guide_routes_protocol_semantics_to_external_sources():
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    interface_protocol = SKILL_DIR / "references" / "interface-v2-protocol.md"
    review = (SKILL_DIR / "references" / "review-guide.md").read_text(
        encoding="utf-8"
    )

    assert "`interface_version: 2` 不是 PI 扩展能力的语义版本" in skill
    assert "不维护 PI 字段矩阵、能力快照或版本语义缓存" in skill
    assert "$maa-wiki" in skill
    assert "MaaLLMWiki" in skill
    assert "pinned revision" in skill
    assert "interface*.schema.json" in skill
    assert "pretask" in skill
    assert "telemetry" in skill
    assert "resource hash" in skill
    assert "attach_resource_path" in skill

    assert not interface_protocol.exists()

    assert "`interface_version: 2` 与 PI 扩展能力语义版本是两层版本" in review
    assert "## 协议来源发现" in review
    assert "不维护 Project Interface V2 的字段矩阵、版本能力表或语义快照" in review
    assert "$maa-wiki" in review
    assert "MaaLLMWiki 上游 `maallmwiki` skill" in review
    assert "按 `$maa-wiki` 的披露顺序用根 README 降级" in review
    assert "pinned tag、commit 或 revision" in review
    assert "不要把历史路径或本地引用写成永久协议来源" in review
    assert "pretask" in review
    assert "`attach_resource_path`" in review
    assert "Agent 子进程假设 `PI_*` 全部存在" in review


def test_pipeline_option_routes_protocol_and_keeps_wiring_boundary():
    option_skill = (ROOT / "skills" / "maa-pipeline-option" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    option_protocol = ROOT / "skills" / "maa-pipeline-option" / "references" / "protocol.md"
    docs = (ROOT / "docs" / "skills" / "maa-pipeline-option.md").read_text(
        encoding="utf-8"
    )

    for term in ("hotkey", "password", "min_count", "max_count"):
        assert term in option_skill

    assert "不是协议全量清单" in option_skill
    assert "$maa-wiki" in option_skill
    assert "interface*.schema.json" in option_skill
    assert "pinned" in option_skill
    assert "不要把本仓库文件当成协议缓存" in option_skill
    assert "pipeline_override 只做属性合并" in option_skill
    assert "context.get_node_data()" in option_skill
    assert not option_protocol.exists()
    assert "references/protocol.md" not in docs
