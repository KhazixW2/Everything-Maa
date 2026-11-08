from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_skills.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_skill_repository_validation_passes():
    validator = load_module("validate_skills", VALIDATOR_PATH)
    assert validator.validate_repository() == []


def test_eval_skill_names_resolve_to_canonical_skills():
    skill_names = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
    for eval_path in (ROOT / "evals").glob("*.json"):
        data = json.loads(eval_path.read_text(encoding="utf-8"))
        assert data["skill_name"] in skill_names


def test_maahub_adapter_paths_exist():
    for metadata_path in (ROOT / "adapters" / "maahub" / "skills").glob("*.json"):
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        for field in ("entry", "readme"):
            target = (metadata_path.parent / data[field]).resolve()
            assert target.is_file(), f"{metadata_path.name}: missing {field} target {target}"


def test_every_canonical_skill_has_a_maahub_adapter():
    skills = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
    adapters = {
        path.stem for path in (ROOT / "adapters" / "maahub" / "skills").glob("*.json")
    }

    assert adapters == skills
    for name in sorted(skills):
        data = json.loads(
            (ROOT / "adapters" / "maahub" / "skills" / f"{name}.json").read_text(
                encoding="utf-8"
            )
        )
        assert data["id"] == f"KhazixW2/{name}"
        assert data["type"] == "skill"
        assert re.fullmatch(r"\d+\.\d+\.\d+", data["version"])
        assert (ROOT / "docs" / "skills" / f"{name}.md").is_file()


def test_relative_markdown_links_inside_skills_exist():
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for markdown_path in (ROOT / "skills").rglob("*.md"):
        text = markdown_path.read_text(encoding="utf-8")
        for raw_target in link_pattern.findall(text):
            target = raw_target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith("<"):
                continue
            if not target.startswith(("../maa-", "../../maa-", "references/", "scripts/", "assets/")):
                continue
            resolved = (markdown_path.parent / target).resolve()
            assert resolved.exists(), f"{markdown_path.relative_to(ROOT)} -> {raw_target}"


def test_plugin_versions_and_mcp_presets_stay_in_sync():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    claude = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    codex = json.loads(
        (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    catalog = json.loads((ROOT / "mcp" / "catalog.json").read_text(encoding="utf-8"))
    native_mcp = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))

    assert package["version"] == claude["version"] == codex["version"]

    def expected_server(server):
        expected = {
            "command": server["command"],
            "args": server["args"],
        }
        if "env" in server:
            expected["env"] = server["env"]
        return expected

    expected_servers = {
        name: expected_server(catalog["servers"][name])
        for name in catalog["profiles"]["full"]
    }
    assert native_mcp["mcpServers"] == expected_servers


def test_integration_catalog_resolves_to_known_mcp_servers():
    mcp_catalog = json.loads((ROOT / "mcp" / "catalog.json").read_text(encoding="utf-8"))
    integrations = json.loads(
        (ROOT / "integrations" / "catalog.json").read_text(encoding="utf-8")
    )

    for name, tool in integrations["tools"].items():
        if "mcpServer" in tool:
            assert tool["mcpServer"] in mcp_catalog["servers"], name

    create_cli = integrations["tools"]["create-maa-project"]["cli"]
    create_server = mcp_catalog["servers"]["create-maa-project"]
    assert create_cli["command"] == create_server["command"]
    assert create_cli["args"] == create_server["args"][:-1]


def test_distribution_manifests_match_package_version():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    marketplace = json.loads(
        (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    distribution = json.loads(
        (ROOT / "distribution" / "catalog.json").read_text(encoding="utf-8")
    )

    plugin = next(item for item in marketplace["plugins"] if item["name"] == "everything-maa")
    assert plugin["source"] == "./"
    assert plugin["version"] == package["version"] == distribution["version"]
    assert distribution["channels"]["maahub"]["adapterCount"] == len(
        list((ROOT / "skills").iterdir())
    )
    for channel in distribution["channels"].values():
        for field in ("manifest", "installer", "adapterRoot", "workflow"):
            if field in channel:
                assert (ROOT / channel[field]).exists(), (field, channel[field])
