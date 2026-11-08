from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
HYGIENE = SKILLS / "maa-pipeline-guide" / "references" / "coordinate-hygiene.md"


def test_coordinate_hygiene_reference_names_both_anti_patterns_and_replacements():
    text = HYGIENE.read_text(encoding="utf-8")

    assert "DirectHit" in text and "target" in text
    assert "target_offset" in text
    assert "OCR-based click" in text
    assert "TemplateMatch-based click" in text
    assert "expected" in text
    assert "screencap" in text
    assert "green_mask" in text

    # The two field-level rules an agent can actually check.
    assert "不写 target" in text
    assert "`target` 默认是 `true`" in text

    # Hardcoded coordinates are allowed only when anchored to a recognition result.
    assert "例外" in text
    assert "锚点是**识别结果**" in text


def test_pipeline_guide_promotes_recognition_derived_click_targets():
    skill = (SKILLS / "maa-pipeline-guide" / "SKILL.md").read_text(encoding="utf-8")

    assert "references/coordinate-hygiene.md" in skill
    assert "点击目标由识别结果推导" in skill
    assert "点击目标来自识别结果" in skill  # review checklist item
    # The guide must not recommend a bare hardcoded offset as the default pattern.
    assert "**`target_offset` 偏移点击**" not in skill


def test_pipeline_generate_binds_node_authoring_to_observed_ui():
    skill = (SKILLS / "maa-pipeline-generate" / "SKILL.md").read_text(encoding="utf-8")

    assert "../maa-pipeline-guide/references/coordinate-hygiene.md" in skill
    assert "点击目标必须由识别结果推导" in skill
    assert "UI 流程未探明时不要先生成节点" in skill
    assert "EXPLORE" in skill
    assert "**`target_offset` 偏移点击**" not in skill


def test_pipeline_testing_records_the_run_pipeline_roi_limitation():
    skill = (SKILLS / "maa-pipeline-testing" / "SKILL.md").read_text(encoding="utf-8")

    assert "单节点验证的工具限制" in skill
    assert "run_pipeline" in skill
    assert "识别成功不等于点对位置" in skill
    assert "不在本仓库范围内" in skill


def test_coordinate_hygiene_guidance_reaches_the_orchestrator_and_docs():
    workflow = (SKILLS / "maa-workflow-build" / "SKILL.md").read_text(encoding="utf-8")
    guide_doc = (ROOT / "docs" / "skills" / "maa-pipeline-guide.md").read_text(
        encoding="utf-8"
    )
    evals = json.loads(
        (ROOT / "evals" / "maa-pipeline-generate.json").read_text(encoding="utf-8")
    )

    assert "../maa-pipeline-guide/references/coordinate-hygiene.md" in workflow
    assert "coordinate-hygiene.md" in guide_doc

    assert evals["skill_name"] == "maa-pipeline-generate"
    names = {case["eval_name"] for case in evals["evals"]}
    assert {
        "replace-directhit-hardcoded-target",
        "replace-hardcoded-target-offset",
        "explore-before-generating-nodes",
    } <= names
