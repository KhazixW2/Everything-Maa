from __future__ import annotations

import importlib.util
import sys
import types
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


def test_screen_size_prefers_explicit_dimensions_and_reads_controller_metadata():
    module = load_module("test_generate_node_screen", SCRIPT_DIR / "generate_node.py")

    assert module.get_screen_size(1280, 720) == (1280, 720)
    assert module.screen_size_from_metadata(
        {"coordinate_size": (1280, 720), "image_size": (720, 1280)}
    ) == (1280, 720)
    assert module.screen_size_from_metadata({"coordinate_size": [720, 0]}) is None
    assert module.screen_size_from_metadata({"image_size": [720, 1280]}) is None


def test_controller_screen_size_reads_coordinate_metadata(
    monkeypatch: pytest.MonkeyPatch,
):
    module = load_module("test_generate_node_controller", SCRIPT_DIR / "generate_node.py")
    calls = []

    maa_mcp = types.ModuleType("maa_mcp")
    vision = types.ModuleType("maa_mcp.vision")

    def fake_screencap(controller_id, include_metadata=False):
        calls.append((controller_id, include_metadata))
        assert include_metadata is True
        return {"coordinate_size": [1280, 720], "image_size": [1920, 1080]}

    vision.screencap = fake_screencap
    maa_mcp.vision = vision
    monkeypatch.setitem(sys.modules, "maa_mcp", maa_mcp)
    monkeypatch.setitem(sys.modules, "maa_mcp.vision", vision)

    assert module.controller_screen_size("controller-1") == (1280, 720)
    assert calls == [("controller-1", True)]


def test_controller_screen_size_rejects_missing_coordinate_size(
    monkeypatch: pytest.MonkeyPatch,
):
    module = load_module(
        "test_generate_node_metadata_error", SCRIPT_DIR / "generate_node.py"
    )

    maa_mcp = types.ModuleType("maa_mcp")
    vision = types.ModuleType("maa_mcp.vision")
    vision.screencap = lambda controller_id, include_metadata=False: {
        "image_size": [720, 1280]
    }
    maa_mcp.vision = vision
    monkeypatch.setitem(sys.modules, "maa_mcp", maa_mcp)
    monkeypatch.setitem(sys.modules, "maa_mcp.vision", vision)

    with pytest.raises(RuntimeError, match="无法从 controller metadata"):
        module.controller_screen_size("controller-1")


def test_sweep_screen_size_requires_explicit_or_environment_dimensions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = load_module("test_generate_sweep_screen", SCRIPT_DIR / "generate_sweep.py")
    monkeypatch.delenv("SCREEN_SIZE", raising=False)
    monkeypatch.delenv("SCREEN_WIDTH", raising=False)
    monkeypatch.delenv("SCREEN_HEIGHT", raising=False)

    assert module.get_screen_size(720, 1280) == (720, 1280)
    assert module.get_screen_size(None, None) is None


def test_sweep_cli_rejects_missing_dimensions_before_writing_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    module = load_module(
        "test_generate_sweep_cli_error", SCRIPT_DIR / "generate_sweep.py"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["generate_sweep.py", "角色", "10,20,30,40"])
    monkeypatch.delenv("SCREEN_SIZE", raising=False)
    monkeypatch.delenv("SCREEN_WIDTH", raising=False)
    monkeypatch.delenv("SCREEN_HEIGHT", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        module.main()

    assert exc_info.value.code == 2
    assert not (tmp_path / "generate_sweep").exists()


def test_build_node_config_omits_wait_defaults():
    module = load_module("test_generate_node_defaults", SCRIPT_DIR / "generate_node.py")

    assert module.build_node_config("角色", [1, 2, 3, 4], "Click", None, None) == {
        "recognition": "OCR",
        "expected": ["角色"],
        "roi": [1, 2, 3, 4],
        "action": "Click",
    }

    assert module.build_node_config("角色", [1, 2, 3, 4], "DoNothing", 500, 2000) == {
        "recognition": "OCR",
        "expected": ["角色"],
        "roi": [1, 2, 3, 4],
        "action": "DoNothing",
        "post_delay": 500,
        "timeout": 2000,
    }


def test_sweep_probe_keeps_fast_failure_timeout(tmp_path: Path):
    module = load_module("test_generate_sweep_timeout", SCRIPT_DIR / "generate_sweep.py")

    nodes = module.make_sweep_pipeline(
        "角色", (10, 20, 30, 40), [0], str(tmp_path / "unused.json"), 720, 1280
    )

    assert "post_delay" not in nodes["Sweep_角色_e0"]
    assert nodes["Sweep_角色_e0"]["timeout"] == 2000


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
