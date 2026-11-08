from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "maa-project-create"


def test_project_create_skill_routes_to_external_lifecycle_engine():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    assert "`create_project`" in text
    assert "`doctor`" in text
    assert "`list_backups`" in text
    assert "$maa-project-init" in text
    assert "Do not reproduce its templates" in text
    assert "resourcePackSlug" in text
    assert "`diff`" not in text


def test_project_create_requires_upstream_skill_handoff():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    discovery = (
        SKILL_DIR / "references" / "upstream-skill-discovery.md"
    ).read_text(encoding="utf-8")

    assert "## Load the bundled upstream Skill" in text
    assert "node scripts/find-create-maa-project-skill.mjs" in text
    assert "For every locator result, read the latest formal upstream Release" in text
    assert "they do not override the latest upstream handoff" in text
    assert "latest formal release" in discovery
    assert "README" in discovery
    assert "integrated Skill" in discovery
    assert "Do not improvise create-maa-project commands" in text
    assert (SKILL_DIR / "scripts" / "find-create-maa-project-skill.mjs").is_file()


def test_project_create_cli_reference_matches_catalog_pin():
    reference = (SKILL_DIR / "references" / "cli-and-reports.md").read_text(
        encoding="utf-8"
    )
    mcp_catalog = json.loads((ROOT / "mcp" / "catalog.json").read_text(encoding="utf-8"))
    integration_catalog = json.loads(
        (ROOT / "integrations" / "catalog.json").read_text(encoding="utf-8")
    )
    server = mcp_catalog["servers"]["create-maa-project"]

    assert server["version"] == "latest"
    assert "uvx --upgrade --from create-maa-project" in reference
    assert "create-maa-project==" not in reference
    assert "v3.2.0" not in reference
    assert integration_catalog["tools"]["create-maa-project"]["mcpServer"] == (
        "create-maa-project"
    )
    assert integration_catalog["tools"]["create-maa-project"]["cli"]["args"] == [
        "--upgrade",
        "--from",
        "create-maa-project",
        "create-maa-project",
    ]


def test_project_create_openai_metadata_and_evals_are_discoverable():
    metadata = yaml.safe_load(
        (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )
    evals = json.loads(
        (ROOT / "evals" / "maa-project-create.json").read_text(encoding="utf-8")
    )

    assert "$maa-project-create" in metadata["interface"]["default_prompt"]
    assert evals["skill_name"] == "maa-project-create"
    assert len(evals["evals"]) >= 4
