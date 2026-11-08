from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "maa-project-create"
LOCATOR = SKILL_DIR / "scripts" / "find-create-maa-project-skill.mjs"
TEST_SKILL = (
    "---\nname: create-maa-project\nversion: 9.9.9\n"
    "description: Test upstream Skill.\n---\n\n# Create Maa Project\n"
)


def run_locator(
    *args: Path | str,
    ambient: bool = False,
    environment: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> dict[str, object]:
    locator_environment = {
        **(environment or os.environ),
        "MAA_PROJECT_CREATE_ROOT": str(SKILL_DIR),
    }
    result = subprocess.run(
        [
            "node",
            str(LOCATOR),
            *(("--no-ambient",) if not ambient else ()),
            *map(str, args),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=locator_environment,
    )

    result.check_returncode()
    return json.loads(result.stdout)


def write_upstream_skill(root: Path, *, bundled: bool) -> Path:
    if not bundled:
        root.mkdir(parents=True)
        skill = root / "SKILL.md"
        skill.write_text(TEST_SKILL, encoding="utf-8")
        return skill

    skill = root / "skills" / "create-maa-project" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(TEST_SKILL, encoding="utf-8")
    return skill


def test_locator_does_not_embed_a_historical_pin():
    source = LOCATOR.read_text(encoding="utf-8")

    assert "3.2.0" not in source
    assert "PINNED_SKILL_SHA256" not in source
    assert 'versionPolicy: "latest"' in source
    assert 'guidanceAuthority: "latest-release"' in source
    assert "latestReleaseUrl" in source
    assert "defaultBranchReadmeUrl" in source
    assert "defaultBranchSkillUrl" in source


def test_locator_prefers_an_explicit_upstream_skill(tmp_path: Path):
    expected = write_upstream_skill(tmp_path, bundled=True)

    result = run_locator("--root", tmp_path)

    assert result["status"] == "found"
    assert result["source"] == "explicit"
    assert result["skillVersion"] == "9.9.9"
    assert Path(str(result["skillPath"])).resolve() == expected.resolve()
    assert result["versionPolicy"] == "latest"
    assert result["guidanceAuthority"] == "latest-release"
    assert result["latestReleaseUrl"].endswith("/releases/latest")
    assert result["defaultBranchReadmeUrl"].endswith("/README.md")
    assert result["defaultBranchSkillUrl"].endswith("/SKILL.md")


def test_locator_skips_an_unrelated_explicit_root_skill(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text(
        "---\nname: unrelated-skill\ndescription: Unrelated.\n---\n",
        encoding="utf-8",
    )
    expected = write_upstream_skill(tmp_path, bundled=True)

    result = run_locator("--root", tmp_path)

    assert result["status"] == "found"
    assert result["source"] == "explicit"
    assert Path(str(result["skillPath"])).resolve() == expected.resolve()


def test_locator_reads_an_npm_package_skill_without_a_catalog_pin(tmp_path: Path):
    package = tmp_path / "create-maa-project"
    package.mkdir()
    (package / "package.json").write_text(
        json.dumps({"name": "create-maa-project", "version": "10.0.0"}),
        encoding="utf-8",
    )
    expected = write_upstream_skill(package, bundled=True)

    result = run_locator("--root", package)

    assert result["status"] == "found"
    assert result["source"] == "explicit-package"
    assert result["packageVersion"] == "10.0.0"
    assert result["skillVersion"] == "9.9.9"
    assert Path(str(result["skillPath"])).resolve() == expected.resolve()


def test_locator_reports_a_package_without_a_skill(tmp_path: Path):
    package = tmp_path / "create-maa-project"
    package.mkdir()
    (package / "package.json").write_text(
        json.dumps({"name": "create-maa-project", "version": "10.0.0"}),
        encoding="utf-8",
    )

    result = run_locator("--root", package)

    assert result["status"] == "package-without-skill"
    assert result["skillPath"] is None
    assert result["packageVersion"] == "10.0.0"
    assert result["versionPolicy"] == "latest"


def test_locator_rejects_the_wrapper_skill_and_reports_the_latest_fallback():
    result = run_locator("--root", SKILL_DIR)

    assert result["status"] == "not-found"
    assert result["skillPath"] is None
    assert result["versionPolicy"] == "latest"
    assert result["guidanceAuthority"] == "latest-release"
    assert result["latestReleaseUrl"] == (
        "https://github.com/Windsland52/create-maa-project/releases/latest"
    )
    assert result["defaultBranchReadmeUrl"] == (
        "https://raw.githubusercontent.com/Windsland52/create-maa-project/main/README.md"
    )
    assert result["defaultBranchSkillUrl"] == (
        "https://raw.githubusercontent.com/Windsland52/create-maa-project/"
        "main/skills/create-maa-project/SKILL.md"
    )


def test_locator_finds_an_installed_user_skill(tmp_path: Path):
    home = tmp_path / "home"
    expected = write_upstream_skill(
        home / ".codex" / "skills" / "create-maa-project",
        bundled=False,
    )
    environment = os.environ.copy()
    environment.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "CODEX_HOME": str(tmp_path / "codex-home"),
        }
    )

    payload = run_locator(ambient=True, environment=environment, cwd=tmp_path)
    assert payload["status"] == "found"
    assert payload["source"] == "installed-skill"
    assert payload["skillVersion"] == "9.9.9"
    assert Path(str(payload["skillPath"])).resolve() == expected.resolve()


def test_locator_accepts_an_unversioned_installed_user_skill(tmp_path: Path):
    home = tmp_path / "home"
    expected = home / ".codex" / "skills" / "create-maa-project" / "SKILL.md"
    skill_directory = home / ".codex" / "skills" / "create-maa-project"
    skill_directory.mkdir(parents=True)
    (skill_directory / "SKILL.md").write_text(
        "---\nname: create-maa-project\ndescription: Current Skill.\n---\n\n"
        "# Current command contract\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment.update(
        {
            "HOME": str(home),
            "USERPROFILE": str(home),
            "CODEX_HOME": str(tmp_path / "codex-home"),
        }
    )

    payload = run_locator(ambient=True, environment=environment, cwd=tmp_path)

    assert payload["status"] == "found"
    assert payload["skillPath"] == str(expected.resolve())
    assert payload["skillVersion"] is None
