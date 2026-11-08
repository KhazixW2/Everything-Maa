from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "maa-pipeline-generate" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("script_name", ["generate_node.py", "generate_sweep.py"])
def test_find_project_root_uses_target_project_not_skill_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, script_name: str
):
    module = load_module(f"test_{script_name.replace('.', '_')}", SCRIPT_DIR / script_name)
    project_root = tmp_path / "MaaExample"
    nested = project_root / "assets" / "resource" / "base"
    nested.mkdir(parents=True)
    (project_root / "assets" / "interface.json").write_text("{}", encoding="utf-8")

    monkeypatch.chdir(nested)
    monkeypatch.delenv("MAAHUB_ROOT", raising=False)
    monkeypatch.delenv("PROJECT_ROOT", raising=False)

    assert module.find_project_root() == project_root.resolve()


@pytest.mark.parametrize("script_name", ["generate_node.py", "generate_sweep.py"])
def test_find_project_root_respects_explicit_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, script_name: str
):
    module = load_module(f"test_env_{script_name.replace('.', '_')}", SCRIPT_DIR / script_name)
    explicit_root = tmp_path / "ExplicitProject"
    explicit_root.mkdir()
    monkeypatch.setenv("PROJECT_ROOT", str(explicit_root))

    assert module.find_project_root() == explicit_root.resolve()


def test_find_project_root_accepts_jsonc_and_assets_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = load_module("test_project_paths_assets", SCRIPT_DIR / "project_paths.py")
    project_root = tmp_path / "MaaJsonc"
    assets = project_root / "assets"
    (assets / "resource").mkdir(parents=True)
    (assets / "interface.jsonc").write_text(
        '{"resource": [{"path": ["./resource/base"]}],}',
        encoding="utf-8",
    )
    monkeypatch.chdir(assets)
    monkeypatch.delenv("MAAHUB_ROOT", raising=False)
    monkeypatch.delenv("PROJECT_ROOT", raising=False)

    context = module.find_project_context()

    assert context.root == project_root.resolve()
    assert context.interface_path == (assets / "interface.jsonc").resolve()


def test_resolve_pipeline_path_uses_declared_resource(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = load_module("test_project_paths_resolve", SCRIPT_DIR / "project_paths.py")
    project_root = tmp_path / "MaaRootInterface"
    base = project_root / "resource" / "base"
    pipeline = base / "pipeline" / "main.json"
    pipeline.parent.mkdir(parents=True)
    pipeline.write_text("{}", encoding="utf-8")
    (project_root / "interface.json").write_text(
        '{"resource": [{"path": ["./resource/base"]}]}',
        encoding="utf-8",
    )
    monkeypatch.chdir(project_root)
    monkeypatch.delenv("MAAHUB_ROOT", raising=False)
    monkeypatch.delenv("PROJECT_ROOT", raising=False)

    assert module.resolve_pipeline_path("main.json") == pipeline.resolve()
    assert module.resolve_pipeline_path(
        "resource/base/pipeline/new.json", project_root
    ) == project_root / "resource" / "base" / "pipeline" / "new.json"


def test_resolve_pipeline_path_rejects_ambiguous_bare_filename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = load_module("test_project_paths_ambiguous", SCRIPT_DIR / "project_paths.py")
    project_root = tmp_path / "MaaOverlay"
    interface = project_root / "interface.json"
    interface.parent.mkdir(parents=True)
    interface.write_text(
        '{"resource": [{"path": ["./resource/base", "./resource/channel"]}]}',
        encoding="utf-8",
    )
    for resource_name in ("base", "channel"):
        path = project_root / "resource" / resource_name / "pipeline" / "main.json"
        path.parent.mkdir(parents=True)
        path.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(project_root)
    monkeypatch.delenv("MAAHUB_ROOT", raising=False)
    monkeypatch.delenv("PROJECT_ROOT", raising=False)

    with pytest.raises(RuntimeError, match="多个声明资源"):
        module.resolve_pipeline_path("main.json")


def test_find_project_root_does_not_fallback_to_git_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = load_module("test_project_paths_git", SCRIPT_DIR / "project_paths.py")
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MAAHUB_ROOT", raising=False)
    monkeypatch.delenv("PROJECT_ROOT", raising=False)

    with pytest.raises(RuntimeError, match="无法定位项目根目录"):
        module.find_project_root()
