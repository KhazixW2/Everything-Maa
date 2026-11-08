from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "maa-cli-operate"


def test_cli_skill_routes_batch_and_persistent_workflows():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    assert "Use `maafw-cli` for one-shot" in text
    assert "Use MaaMCP instead" in text
    assert "pipeline validate" in text
    assert "`custom load`" in text
    assert "$maa-pipeline-testing" in text


def test_cli_reference_documents_pinned_version_and_contract_terms():
    # This checks documentation discoverability, not the external CLI contract.
    reference = (SKILL_DIR / "references" / "command-contract.md").read_text(
        encoding="utf-8"
    )
    integrations = json.loads(
        (ROOT / "integrations" / "catalog.json").read_text(encoding="utf-8")
    )
    tool = integrations["tools"]["maafw-cli"]

    assert tool["version"] == "0.1.6"
    assert "maafw-cli==0.1.6" in reference
    assert "--json" in reference
    assert "--size short:720" in reference
    assert "short-side baseline" in reference
    assert "NoScalingTouchPoints" in reference
    assert "ProjectInterface V2" in reference
    assert "Unity Canvas Scaler" in reference
    assert "must not rely" in reference


def test_cli_metadata_and_evals_are_discoverable():
    metadata = yaml.safe_load(
        (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )
    evals = json.loads((ROOT / "evals" / "maa-cli-operate.json").read_text(encoding="utf-8"))

    assert "$maa-cli-operate" in metadata["interface"]["default_prompt"]
    assert evals["skill_name"] == "maa-cli-operate"
    assert len(evals["evals"]) >= 4
