import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "maa-project-init"
    / "scripts"
    / "analyze_pipeline_project.py"
)


def load_analyzer():
    spec = importlib.util.spec_from_file_location("analyze_pipeline_project", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_load_json_accepts_jsonc_syntax(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "pipeline.json"
    path.write_text(
        """{
          // Pipeline files in M9A may contain comments.
          "Start": {
            "url": "https://example.invalid/not-a-comment",
            /* Keep newline positions useful in parser errors. */
            "next": ["Done",]
          },
        }
        """,
        encoding="utf-8",
    )

    assert analyzer.load_json(path) == {
        "Start": {
            "url": "https://example.invalid/not-a-comment",
            "next": ["Done"],
        }
    }


def test_custom_action_name_supports_v1_and_v2_syntax() -> None:
    analyzer = load_analyzer()
    assert analyzer.node_custom_action_name(
        {"action": "Custom", "custom_action": "LegacyHandler"}
    ) == "LegacyHandler"
    assert analyzer.node_custom_action_name(
        {
            "action": {
                "type": "Custom",
                "param": {"custom_action": "ObjectHandler"},
            }
        }
    ) == "ObjectHandler"


def make_consumer_project(tmp_path: Path) -> Path:
    root = tmp_path / "MaaExampleGame"
    assets = root / "assets"
    write_json(
        assets / "interface.json",
        {
            "name": "MaaExampleGame",
            "url": "https://example.invalid/MaaExampleGame",
            "controller": [{"name": "ADB 默认方式", "type": "Adb"}],
            "resource": [
                {"name": "官服", "path": ["./resource/base"]},
                {"name": "渠道服", "path": ["./resource/base", "./resource/channel"]},
            ],
            "agent": {
                "child_exec": "python",
                "child_args": ["-u", "./agent/main.py"],
            },
            "task": [
                {"name": "启动游戏", "entry": "Start"},
                {"name": "每日任务", "entry": "DailyTask"},
            ],
        },
    )
    write_json(
        assets / "resource" / "base" / "default_pipeline.json",
        {
            "Default": {"post_delay": 100},
            "TemplateMatch": {"recognition": "TemplateMatch", "threshold": 0.7},
        },
    )
    write_json(
        assets / "resource" / "base" / "pipeline" / "utils.json",
        {
            "BackText": {
                "recognition": "OCR",
                "expected": "返回",
                "roi": [500, 1100, 180, 80],
                "action": "Click",
            },
            "ConfirmButton": {
                "recognition": "OCR",
                "expected": ["确定", "确认"],
                "roi": [30, 400, 660, 420],
                "action": "Click",
            },
            "PopupClose": {
                "recognition": "TemplateMatch",
                "template": "utils/Close.png",
                "action": "Click",
            },
            "AndroidBackKey": {
                "recognition": "DirectHit",
                "action": "ClickKey",
                "key": 4,
            },
            "ReturnHall": {
                "recognition": "DirectHit",
                "next": [
                    "CheckHall",
                    "[JumpBack]BackText",
                    {"name": "ConfirmButton", "jump_back": True},
                ],
            },
            "CheckHall": {
                "recognition": "OCR",
                "expected": "大厅",
            },
        },
    )
    write_json(
        assets / "resource" / "base" / "pipeline" / "main.json",
        {
            "Start": {
                "next": ["TaskNode", "[JumpBack]ReturnHall"],
                "on_error": "ConfirmButton",
                "interrupt": ["PopupClose"],
            },
            "TaskNode": {
                "recognition": "TemplateMatch",
                "template": "task/Task.png",
                "action": "Click",
                "next": ["AndroidBackKey", "MissingNode", "CustomDispatch"],
            },
            "CustomDispatch": {
                "recognition": "DirectHit",
                "action": "Custom",
                "custom_action": "DemoDispatch",
                "next": "ReturnHall",
            },
            "DailyTask": {
                "recognition": "DirectHit",
                "next": ["TaskNode", "[JumpBack]BackText"],
            },
            "SelfLoop": {
                "recognition": "DirectHit",
                "next": "SelfLoop",
            },
            "IsolatedProbe": {
                "recognition": "OCR",
                "expected": "孤立",
            },
            "V2BackKey": {
                "recognition": {
                    "type": "TemplateMatch",
                    "param": {
                        "template": "utils/BackButton.png",
                        "roi": [500, 1100, 180, 80],
                    },
                },
                "action": {"type": "ClickKey", "param": {"key": 4}},
            },
            "V2OcrProbe": {
                "recognition": {
                    "type": "OCR",
                    "param": {
                        "expected": ["外部入口"],
                        "roi": [30, 40, 200, 80],
                    },
                },
            },
        },
    )
    write_json(
        assets / "resource" / "channel" / "pipeline" / "start_up.json",
        {
            "ChannelStart": {
                "recognition": "DirectHit",
                "next": ["Start"],
            }
        },
    )
    for image in [
        assets / "resource" / "base" / "image" / "utils" / "Close.png",
        assets / "resource" / "base" / "image" / "utils" / "BackButton.png",
        assets / "resource" / "base" / "image" / "task" / "Task.png",
    ]:
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(b"png")
    agent = root / "agent" / "action" / "example.py"
    agent.parent.mkdir(parents=True, exist_ok=True)
    agent.write_text(
        "@AgentServer.custom_action('DemoDispatch')\n"
        "class DemoDispatch:\n"
        "    def run(self, context):\n"
        "        return True\n"
        "\n"
        "def run(context, dynamic_name):\n"
        "    context.run_task('V2OcrProbe')\n"
        "    context.run_recognition('CheckHall', None)\n"
        "    context.run_task(dynamic_name)\n",
        encoding="utf-8",
    )
    return root


def make_standard_interface_project(tmp_path: Path) -> Path:
    root = tmp_path / "StandardMaaProject"
    write_json(
        root / "interface.json",
        {
            "interface_version": 2,
            "name": "standard-maa-project",
            "github": "https://example.invalid/standard-maa-project",
            "controller": [{"name": "ADB", "type": "Adb"}],
            "resource": [{"name": "default", "path": ["./resource/base"]}],
            "agent": [
                {
                    "child_exec": "uv",
                    "child_args": ["run", "python", "agent/bootstrap.py"],
                }
            ],
            "import": ["tasks/feature.json"],
        },
    )
    write_json(
        root / "tasks" / "feature.json",
        {
            "task": [{"name": "Feature", "entry": "Start", "option": ["Mode"]}],
            "option": {"Mode": {"type": "switch", "cases": []}},
            "preset": [
                {"name": "Default", "task": [{"name": "Feature", "enabled": True}]}
            ],
        },
    )
    write_json(
        root / "resource" / "base" / "pipeline" / "main.json",
        {
            "Start": {
                "recognition": "DirectHit",
                "action": "DoNothing",
                "next": ["Done"],
            },
            "Done": {"recognition": "DirectHit"},
        },
    )
    bootstrap = root / "agent" / "bootstrap.py"
    bootstrap.parent.mkdir(parents=True, exist_ok=True)
    bootstrap.write_text("# bootstrap\n", encoding="utf-8")
    return root


def test_analyze_project_loads_interface_imports_and_agent_array(tmp_path: Path):
    analyzer = load_analyzer()
    root = make_standard_interface_project(tmp_path)

    result = analyzer.analyze_project(root)

    assert result["project_url"] == "https://example.invalid/standard-maa-project"
    assert result["interface_path"] == "interface.json"
    assert result["interface_imports"]["declared"] == ["tasks/feature.json"]
    assert result["interface_imports"]["loaded"] == ["tasks/feature.json"]
    assert [task["entry"] for task in result["tasks"]] == ["Start"]
    assert result["resource_groups"][0]["raw_paths"] == ["./resource/base"]
    assert result["pipeline"]["task_flow_graphs"][0]["entry_found"] is True
    assert result["agent_scripts"]["agent_config_count"] == 1
    assert result["agent_scripts"]["declared_resolved_count"] == 1
    assert result["agent_scripts"]["declared_unresolved_count"] == 0
    assert result["agent_scripts"]["orphan_declarations"] == []
    interface, _ = analyzer.load_interface_bundle(root / "interface.json")
    assert interface["preset"][0]["name"] == "Default"


def test_analyze_project_expands_wildcard_interface_imports(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "M9AStyleProject"
    write_json(
        root / "interface.json",
        {
            "resource": [{"name": "default", "path": ["./resource/base"]}],
            "import": ["tasks/**/*.json"],
        },
    )
    write_json(
        root / "tasks" / "feature.json",
        {"task": [{"name": "Feature", "entry": "Start"}]},
    )
    write_json(
        root / "tasks" / "daily" / "login.json",
        {"task": [{"name": "Login", "entry": "Login"}]},
    )
    write_json(
        root / "resource" / "base" / "pipeline" / "main.json",
        {
            "Start": {"recognition": "DirectHit"},
            "Login": {"recognition": "DirectHit"},
        },
    )

    result = analyzer.analyze_project(root)

    assert result["interface_imports"]["declared"] == ["tasks/**/*.json"]
    assert result["interface_imports"]["loaded"] == [
        "tasks/daily/login.json",
        "tasks/feature.json",
    ]
    assert [task["name"] for task in result["tasks"]] == ["Login", "Feature"]
    assert all(flow["entry_found"] for flow in result["pipeline"]["task_flow_graphs"])


def test_empty_wildcard_interface_import_is_diagnosed(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "EmptyWildcard"
    write_json(root / "interface.json", {"import": ["tasks/**/*.json"]})

    result = analyzer.analyze_project(root)

    assert result["interface_imports"]["missing"] == ["tasks/**/*.json"]
    assert any("没有匹配到任何文件" in warning for warning in result["interface_imports"]["warnings"])


def test_analyze_project_prefers_root_interface_and_declared_resources(tmp_path: Path):
    analyzer = load_analyzer()
    root = make_standard_interface_project(tmp_path)
    write_json(
        root / "assets" / "interface.json",
        {
            "resource": [{"path": ["./resource/legacy"]}],
            "task": [{"name": "Legacy", "entry": "LegacyStart"}],
        },
    )

    result = analyzer.analyze_project(root)

    assert result["interface_path"] == "interface.json"
    assert [task["name"] for task in result["tasks"]] == ["Feature"]
    assert all(
        "resource/base" in path
        for group in result["resource_groups"]
        for path in group["paths"]
    )


def test_analyze_project_does_not_infer_undeclared_resource_roots(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "NoInterface"
    write_json(
        root / "assets" / "resource" / "base" / "pipeline" / "main.json",
        {"Start": {"recognition": "DirectHit"}},
    )

    result = analyzer.analyze_project(root)

    assert result["interface_path"] == ""
    assert result["resource_groups"] == []
    assert result["pipeline"]["node_names"] == []


def test_analyze_project_supports_root_interface_jsonc(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "JsoncInterface"
    root.mkdir()
    (root / "interface.jsonc").write_text(
        """{
          // Paths are relative to this main Interface.
          "controller": [{"type": "Adb"}],
          "resource": [{"name": "base", "path": ["./resource/base"]}],
          "import": ["tasks/feature.jsonc",],
        }
        """,
        encoding="utf-8",
    )
    tasks = root / "tasks"
    tasks.mkdir()
    (tasks / "feature.jsonc").write_text(
        """{
          "task": [{"name": "Feature", "entry": "Start",}],
        }
        """,
        encoding="utf-8",
    )
    write_json(
        root / "resource" / "base" / "pipeline" / "main.json",
        {"Start": {"recognition": "DirectHit"}},
    )

    result = analyzer.analyze_project(root)

    assert result["interface_path"] == "interface.jsonc"
    assert result["interface_imports"]["loaded"] == ["tasks/feature.jsonc"]
    assert [task["name"] for task in result["tasks"]] == ["Feature"]
    assert result["pipeline"]["task_flow_graphs"][0]["entry_found"] is True


def test_analyze_project_counts_imported_tasks_in_assets_interface_bundle(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "BoilerplateMaaProject"
    assets = root / "assets"
    assets.mkdir(parents=True)
    (assets / "interface.jsonc").write_text(
        """{
          // Boilerplate-family projects may keep all task declarations in imports.
          "controller": [{"type": "Adb"}],
          "resource": [{"name": "default", "path": ["./resource/base"]}],
          "agent": {
            "child_exec": "python",
            "child_args": ["-u", "../agent/main.py"],
          },
          "task": [],
          "import": ["tasks/feature.jsonc",],
        }
        """,
        encoding="utf-8",
    )
    tasks = assets / "tasks"
    tasks.mkdir()
    (tasks / "feature.jsonc").write_text(
        """{
          "task": [
            {"name": "Feature", "entry": "Start", "option": ["Mode"]},
            // Display-only separator entries still belong to the raw task count.
            {"name": "----------------", "entry": "DisplaySeparator"},
          ],
          "option": {"Mode": {"type": "switch", "cases": []}},
          "preset": [
            {"name": "Default", "task": [{"name": "Feature", "enabled": true}]}
          ],
        }
        """,
        encoding="utf-8",
    )
    write_json(
        assets / "resource" / "base" / "pipeline" / "main.json",
        {
            "Start": {"recognition": "DirectHit", "action": "DoNothing"},
            "DisplaySeparator": {"recognition": "DirectHit", "action": "DoNothing"},
        },
    )
    agent = root / "agent" / "main.py"
    agent.parent.mkdir(parents=True, exist_ok=True)
    agent.write_text("# agent entry\n", encoding="utf-8")

    result = analyzer.analyze_project(root)

    assert result["interface_path"] == "assets/interface.jsonc"
    assert result["interface_imports"]["loaded"] == ["tasks/feature.jsonc"]
    assert [task["name"] for task in result["tasks"]] == [
        "Feature",
        "----------------",
    ]
    assert all(flow["entry_found"] for flow in result["pipeline"]["task_flow_graphs"])
    assert result["resource_groups"][0]["paths"] == [
        (assets / "resource" / "base").resolve().as_posix()
    ]
    assert result["agent_scripts"]["declared_resolved_count"] == 1
    assert [Path(item).resolve() for item in result["agent_scripts"]["declared_resolved"]] == [
        agent.resolve()
    ]


def test_malformed_interface_jsonc_is_reported_without_stopping_analysis(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "MalformedMainInterface"
    root.mkdir()
    (root / "interface.jsonc").write_text(
        '{"resource": [{"path": ["./resource/base"]}] /*',
        encoding="utf-8",
    )
    write_json(
        root / "resource" / "base" / "pipeline" / "main.json",
        {"Start": {"recognition": "DirectHit"}},
    )

    result = analyzer.analyze_project(root)

    assert result["interface_path"] == "interface.jsonc"
    assert result["resource_groups"] == []
    assert result["pipeline"]["node_names"] == []
    assert any(
        "无法读取主 Interface" in warning
        for warning in result["interface_imports"]["warnings"]
    )


def test_malformed_interface_import_is_reported_without_stopping_analysis(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "MalformedInterfaceImport"
    write_json(
        root / "interface.json",
        {
            "resource": [{"name": "default", "path": ["./resource/base"]}],
            "import": ["tasks/broken.json"],
        },
    )
    (root / "tasks").mkdir()
    (root / "tasks" / "broken.json").write_text(
        '{"task": [] /*',
        encoding="utf-8",
    )
    write_json(
        root / "resource" / "base" / "pipeline" / "main.json",
        {"Start": {"recognition": "DirectHit"}},
    )

    result = analyzer.analyze_project(root)

    assert result["tasks"] == []
    assert result["interface_imports"]["missing"] == ["tasks/broken.json"]
    assert any(
        "tasks/broken.json" in warning
        for warning in result["interface_imports"]["warnings"]
    )
    assert "Start" in result["pipeline"]["node_names"]


def test_malformed_main_interface_shapes_are_diagnosed_without_crashing(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "MalformedInterfaceShapes"
    write_json(
        root / "interface.json",
        {
            "task": "not-an-array",
            "preset": "not-an-array",
            "option": ["not-an-object"],
            "resource": [
                "not-an-object",
                {"name": 42, "path": [123, "./resource/base"]},
            ],
            "import": ["tasks/feature.json"],
        },
    )
    write_json(
        root / "tasks" / "feature.json",
        {"task": [{"name": "Feature", "entry": "Start"}]},
    )
    write_json(
        root / "resource" / "base" / "pipeline" / "main.json",
        {"Start": {"recognition": "DirectHit"}},
    )

    result = analyzer.analyze_project(root)
    warnings = result["interface_imports"]["warnings"]

    assert [task["name"] for task in result["tasks"]] == ["Feature"]
    assert result["resource_groups"][0]["raw_paths"] == ["./resource/base"]
    assert any("task 字段不是数组" in warning for warning in warnings)
    assert any("preset 字段不是数组" in warning for warning in warnings)
    assert any("option 字段不是 object" in warning for warning in warnings)
    assert any("resource[0] 不是 JSON object" in warning for warning in warnings)
    assert any("resource[1].path 不是字符串或字符串数组" in warning for warning in warnings)
    assert "Start" in result["pipeline"]["node_names"]


def test_missing_interface_import_is_reported_without_stopping_analysis(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "BrokenImport"
    write_json(
        root / "interface.json",
        {
            "interface_version": 2,
            "name": "broken-import",
            "controller": [{"type": "Adb"}],
            "resource": [{"name": "default", "path": ["./resource/base"]}],
            "import": ["tasks/missing.json"],
        },
    )
    write_json(
        root / "resource" / "base" / "pipeline" / "main.json",
        {"Start": {"recognition": "DirectHit"}},
    )

    result = analyzer.analyze_project(root)

    assert result["tasks"] == []
    assert result["interface_imports"]["declared"] == ["tasks/missing.json"]
    assert result["interface_imports"]["loaded"] == []
    assert result["interface_imports"]["missing"] == ["tasks/missing.json"]
    assert any("tasks/missing.json" in warning for warning in result["interface_imports"]["warnings"])
    assert "Start" in result["pipeline"]["node_names"]


def test_unique_existing_resource_dirs_preserves_case_sensitive_paths():
    analyzer = load_analyzer()
    groups = [
        {"existing_paths": ["/tmp/MaaProject/Resource/Base"]},
        {"existing_paths": ["/tmp/MaaProject/resource/base"]},
    ]

    result = analyzer.unique_existing_resource_dirs(groups)

    if os.name == "posix":
        assert [path.as_posix() for path in result] == [
            "/tmp/MaaProject/Resource/Base",
            "/tmp/MaaProject/resource/base",
        ]
    else:
        assert [path.as_posix() for path in result] == [
            "/tmp/MaaProject/Resource/Base",
        ]


def test_analyze_project_finds_entries_edges_common_nodes_and_images(tmp_path: Path):
    analyzer = load_analyzer()
    root = make_consumer_project(tmp_path)

    result = analyzer.analyze_project(root)
    pipeline = result["pipeline"]

    assert result["project_name"] == "MaaExampleGame"
    assert result["controllers"] == ["Adb"]
    assert {task["entry"] for task in result["tasks"]} == {"Start", "DailyTask"}
    assert result["pipeline_file_count"] == 3
    assert pipeline["edge_type_counts"]["next"] >= 8
    assert pipeline["edge_type_counts"]["on_error"] == 1
    assert pipeline["edge_type_counts"]["interrupt"] == 1
    assert "MissingNode" in pipeline["unresolved_refs"]
    assert ["SelfLoop"] in pipeline["cycle_candidates"]
    assert "Start" in pipeline["node_names"]

    common_names = {item["name"] for item in pipeline["common_nodes"]}
    return_names = {item["name"] for item in pipeline["return_exit_nodes"]}
    confirm_names = {item["name"] for item in pipeline["confirm_nodes"]}

    assert {"BackText", "ConfirmButton", "ReturnHall"} <= common_names
    assert {"BackText", "ReturnHall", "AndroidBackKey"} <= return_names
    assert "ConfirmButton" in confirm_names
    assert result["image_summary"]["image_count"] == 3
    assert any(item["dir"].endswith("utils") for item in result["image_summary"]["top_dirs"])

    flows = {flow["entry"]: flow for flow in pipeline["task_flow_graphs"]}
    start_flow = flows["Start"]
    assert start_flow["entry_found"] is True
    assert "TaskNode" in start_flow["nodes"]
    assert "MissingNode" in start_flow["unresolved_refs"]
    assert start_flow["primary_path"][:2] == ["Start", "TaskNode"]
    assert any(edge["field"] == "on_error" for edge in start_flow["edges"])
    assert any(edge["field"] == "interrupt" for edge in start_flow["edges"])
    assert any("JumpBack" in edge["attrs"] for edge in start_flow["edges"])
    assert len(start_flow["custom_actions"]) == 1
    custom_action = start_flow["custom_actions"][0]
    assert custom_action["node"] == "CustomDispatch"
    assert custom_action["custom_action"] == "DemoDispatch"
    assert custom_action["file"].replace("\\", "/").endswith("pipeline/main.json")
    registration = custom_action["registrations"][0]
    assert registration["name"] == "DemoDispatch"
    assert registration["file"].replace("\\", "/") == "agent/action/example.py"
    assert registration["line"] == 1
    assert registration["handler"] == "DemoDispatch"
    assert any(item["node"] == "V2OcrProbe" for item in pipeline["ocr_expected"])
    assert any(item["node"] == "V2BackKey" for item in pipeline["templates"])
    assert "V2BackKey" in return_names
    assert pipeline["python_pipeline"]["targets"] == ["CheckHall", "V2OcrProbe"]
    assert {
        (item["kind"], item["target"]): item["count"]
        for item in pipeline["python_pipeline"]["call_summaries"]
    } == {("run_recognition", "CheckHall"): 1, ("run_task", "V2OcrProbe"): 1}
    assert len(pipeline["python_pipeline"]["dynamic_calls"]) == 1
    assert len(pipeline["python_pipeline"]["custom_action_registrations"]) == 1
    assert "V2OcrProbe" in pipeline["external_entry_nodes"]
    assert "V2OcrProbe" not in pipeline["orphan_candidates"]
    assert "IsolatedProbe" in pipeline["orphan_candidates"]


def test_render_and_write_basic_info_refuses_existing_file(tmp_path: Path):
    analyzer = load_analyzer()
    root = make_consumer_project(tmp_path)
    result = analyzer.analyze_project(root)

    content = analyzer.render_basic_info(result)
    assert "MaaExampleGame" in content
    assert "Start" in content
    assert "BackText" in content
    assert "ConfirmButton" in content
    assert "MissingNode" in content
    assert "TemplateMatch" in content
    assert "入口主链路流程图" in content
    assert "flowchart TD" in content
    assert "Python Agent" in content
    assert "CustomAction call" in content
    assert "DemoDispatch" in content
    assert "Maa Skills 接力协议" in content
    assert "Python / interface 外部入口" in content
    assert "V2OcrProbe" in content
    assert "static-scan-only" in content

    written = analyzer.write_basic_info(result)
    assert written == root / "basic_info.md"
    assert written.read_text(encoding="utf-8") == content

    with pytest.raises(FileExistsError):
        analyzer.write_basic_info(result)

    overwritten = analyzer.write_basic_info(result, overwrite=True)
    assert overwritten == written


# ---------------------------------------------------------------------------
# Agent script scanning tests
# ---------------------------------------------------------------------------


def make_consumer_project_with_agent_main(tmp_path: Path) -> Path:
    """与 make_consumer_project 相同，但额外创建 agent/main.py（命中 child_args）。"""
    root = make_consumer_project(tmp_path)
    main_script = root / "agent" / "main.py"
    main_script.parent.mkdir(parents=True, exist_ok=True)
    main_script.write_text("# agent entry\n", encoding="utf-8")
    return root


def _build_minimal_project(tmp_path: Path, agent_block: dict[str, Any]) -> Path:
    root = tmp_path / "Project"
    assets = root / "assets"
    write_json(
        assets / "interface.json",
        {
            "name": "Project",
            "controller": [{"name": "ADB", "type": "Adb"}],
            "resource": [{"name": "default", "path": ["./resource/base"]}],
            "agent": agent_block,
            "task": [],
        },
    )
    (assets / "resource" / "base").mkdir(parents=True, exist_ok=True)
    return root


class TestResolveAgentArg:
    def test_resolved_at_level_zero(self, tmp_path: Path):
        analyzer = load_analyzer()
        script = tmp_path / "agent" / "main.py"
        script.parent.mkdir(parents=True)
        script.touch()
        result = analyzer.resolve_agent_arg(tmp_path, "./agent/main.py")
        assert result["status"] == "resolved"
        assert result["resolved_at_level"] == 0
        assert Path(result["resolved"]).resolve() == script.resolve()
        assert result["is_py"] is True
        assert result["is_absolute"] is False

    def test_resolved_at_parent_level(self, tmp_path: Path):
        analyzer = load_analyzer()
        repo = tmp_path / "repo"
        assets = repo / "assets"
        assets.mkdir(parents=True)
        script = repo / "agent" / "main.py"
        script.parent.mkdir(parents=True)
        script.touch()
        result = analyzer.resolve_agent_arg(assets, "./agent/main.py")
        assert result["status"] == "resolved"
        # candidates[0] = assets/agent/main.py (level 0, missing)
        # candidates[1] = repo/agent/main.py (level 1, hits here)
        assert result["resolved_at_level"] == 1
        assert Path(result["resolved"]).resolve() == script.resolve()

    def test_unresolved_returns_none(self, tmp_path: Path):
        analyzer = load_analyzer()
        result = analyzer.resolve_agent_arg(tmp_path, "agent/missing.py")
        assert result["status"] == "unresolved"
        assert result["resolved"] is None
        assert result["resolved_at_level"] == -1
        assert len(result["candidates"]) >= 1

    def test_absolute_path_kept_as_is(self, tmp_path: Path):
        analyzer = load_analyzer()
        script = tmp_path / "main.py"
        script.touch()
        result = analyzer.resolve_agent_arg(tmp_path, str(script))
        assert result["is_absolute"] is True
        assert result["status"] == "absolute"
        assert result["resolved"] == str(script)

    def test_non_py_arg_short_circuits(self, tmp_path: Path):
        analyzer = load_analyzer()
        result = analyzer.resolve_agent_arg(tmp_path, "-u")
        assert result["is_py"] is False
        assert result["status"] == "non-py"
        assert result["resolved"] is None
        assert result["candidates"] == []

    def test_empty_arg_short_circuits(self, tmp_path: Path):
        analyzer = load_analyzer()
        result = analyzer.resolve_agent_arg(tmp_path, "")
        assert result["status"] == "non-py"
        assert result["resolved"] is None


class TestDiscoverAgentCandidates:
    def test_root_level_main_py_found(self, tmp_path: Path):
        analyzer = load_analyzer()
        script = tmp_path / "agent" / "main.py"
        script.parent.mkdir(parents=True)
        script.touch()
        result = analyzer.discover_agent_candidates(tmp_path)
        candidates = {item["candidate"] for item in result}
        assert str(script) in candidates
        match = next(item for item in result if item["candidate"] == str(script))
        assert match["exists"] is True
        assert match["level"] == 0

    def test_existing_and_missing_both_listed(self, tmp_path: Path):
        analyzer = load_analyzer()
        (tmp_path / "agent").mkdir()
        (tmp_path / "agent" / "main.py").touch()
        result = analyzer.discover_agent_candidates(tmp_path)
        main_exists = next(
            item for item in result if item["candidate"].endswith("agent\\main.py")
            or item["candidate"].endswith("agent/main.py")
        )
        server_missing = next(
            item for item in result if item["candidate"].endswith("agent\\server.py")
            or item["candidate"].endswith("agent/server.py")
        )
        assert main_exists["exists"] is True
        assert server_missing["exists"] is False

    def test_does_not_recurse_into_subdirectories(self, tmp_path: Path):
        analyzer = load_analyzer()
        nested = tmp_path / "agent" / "action" / "weird_main.py"
        nested.parent.mkdir(parents=True)
        nested.touch()
        result = analyzer.discover_agent_candidates(tmp_path)
        # nested file should NOT appear (we only look at convention basenames at agent/<basename>)
        assert not any(item["candidate"].endswith("weird_main.py") for item in result)

    def test_walks_ancestors_up_to_limit(self, tmp_path: Path):
        analyzer = load_analyzer()
        # tmp_path/grandparent/parent/child  → root=child, walk up to grandparent (level 2)
        grandparent = tmp_path / "grandparent"
        parent = grandparent / "parent"
        child = parent / "child"
        child.mkdir(parents=True)
        # Place main.py at grandparent level
        (grandparent / "agent").mkdir()
        (grandparent / "agent" / "main.py").touch()
        result = analyzer.discover_agent_candidates(child)
        levels = [item["level"] for item in result if item.get("exists")]
        # Should discover grandparent's agent/main.py (level 2)
        assert 2 in levels

    def test_skips_disallowed_ancestor(self, tmp_path: Path):
        analyzer = load_analyzer()
        venv = tmp_path / ".venv" / "project"
        venv.mkdir(parents=True)
        (venv / "agent").mkdir()
        (venv / "agent" / "main.py").touch()
        result = analyzer.discover_agent_candidates(venv)
        # .venv is in SKIP_DIR_NAMES → should be filtered out
        # All candidates should be from venv or its descendants (which is just venv itself)
        # Since venv should_skip(), its candidates get filtered
        assert all(item["level"] >= 0 for item in result)


class TestAnalyzeAgentScripts:
    def test_returns_empty_skeleton_without_interface(self, tmp_path: Path):
        analyzer = load_analyzer()
        result = analyzer.analyze_agent_scripts(tmp_path, None, {})
        assert result["agent_block_present"] is False
        assert result["declared"] == []
        assert result["discovered"] == []
        assert result["declared_resolved"] == []
        assert result["warnings"] == []

    def test_malformed_agent_array_entries_are_reported(self, tmp_path: Path):
        analyzer = load_analyzer()
        root = _build_minimal_project(
            tmp_path,
            [{"child_args": ["agent/main.py"]}, "not-an-object"],
        )
        interface_path = root / "assets" / "interface.json"
        interface = json.loads(interface_path.read_text(encoding="utf-8"))

        result = analyzer.analyze_agent_scripts(root, interface_path, interface["agent"])

        assert result["agent_block_present"] is True
        assert result["agent_config_count"] == 1
        assert any("agent[1] 不是 JSON object" in warning for warning in result["warnings"])

    def test_empty_agent_array_remains_a_present_block(self, tmp_path: Path):
        analyzer = load_analyzer()
        root = _build_minimal_project(tmp_path, [])
        interface_path = root / "assets" / "interface.json"

        result = analyzer.analyze_agent_scripts(root, interface_path, [])

        assert result["agent_block_present"] is True
        assert result["agent_config_count"] == 0
        assert any("agent 数组为空" in warning for warning in result["warnings"])

    def test_unresolved_when_file_missing(self, tmp_path: Path):
        analyzer = load_analyzer()
        # Use the existing make_consumer_project fixture which has child_args pointing to ./agent/main.py
        # but does NOT create that file.
        root = make_consumer_project(tmp_path)
        interface_path = root / "assets" / "interface.json"
        with interface_path.open("r", encoding="utf-8") as fh:
            interface = json.load(fh)
        result = analyzer.analyze_agent_scripts(root, interface_path, interface.get("agent") or {})
        assert result["agent_block_present"] is True
        assert result["declared_unresolved_count"] == 1  # ./agent/main.py
        assert "./agent/main.py" in [item["arg"] for item in result["declared"] if item["status"] == "unresolved"]
        assert any("./agent/main.py" in w for w in result["warnings"])

    def test_resolved_when_file_exists(self, tmp_path: Path):
        analyzer = load_analyzer()
        root = make_consumer_project_with_agent_main(tmp_path)
        interface_path = root / "assets" / "interface.json"
        with interface_path.open("r", encoding="utf-8") as fh:
            interface = json.load(fh)
        result = analyzer.analyze_agent_scripts(root, interface_path, interface.get("agent") or {})
        assert result["declared_resolved_count"] == 1
        assert result["declared_unresolved_count"] == 0
        assert any(item.endswith("agent\\main.py") or item.endswith("agent/main.py") for item in result["declared_resolved"])

    def test_interface_declaration_is_authoritative_outside_convention(self, tmp_path: Path):
        analyzer = load_analyzer()
        # child_args 指向 agent/custom_entry.py，不在 AGENT_ENTRY_BASENAMES 清单
        root = _build_minimal_project(
            tmp_path,
            {"child_exec": "python", "child_args": ["agent/custom_entry.py"]},
        )
        # 真实创建该文件
        script = root / "assets" / "agent" / "custom_entry.py"
        script.parent.mkdir(parents=True)
        script.touch()
        interface_path = root / "assets" / "interface.json"
        with interface_path.open("r", encoding="utf-8") as fh:
            interface = json.load(fh)
        result = analyzer.analyze_agent_scripts(root, interface_path, interface.get("agent") or {})
        assert result["declared_resolved_count"] == 1
        assert result["orphan_declarations"] == []

    def test_unused_candidates_when_discovered_not_referenced(self, tmp_path: Path):
        analyzer = load_analyzer()
        # child_args 指向 ./agent/main.py；同时仓库里额外存在 ./agent/server.py 没用上
        root = _build_minimal_project(
            tmp_path,
            {"child_exec": "python", "child_args": ["./agent/main.py"]},
        )
        (root / "assets" / "agent").mkdir(parents=True)
        (root / "assets" / "agent" / "main.py").touch()
        (root / "assets" / "agent" / "server.py").touch()
        interface_path = root / "assets" / "interface.json"
        with interface_path.open("r", encoding="utf-8") as fh:
            interface = json.load(fh)
        result = analyzer.analyze_agent_scripts(root, interface_path, interface.get("agent") or {})
        # main.py referenced; server.py exists but not referenced
        unused_paths = [p for p in result["unused_candidates"] if p.endswith("server.py")]
        assert len(unused_paths) == 1

    def test_absolute_and_non_py_skipped_from_unresolved(self, tmp_path: Path):
        analyzer = load_analyzer()
        # Use a real absolute .py path that exists, plus a non-.py flag.
        real_script = tmp_path / "real_agent.py"
        real_script.touch()
        root = _build_minimal_project(
            tmp_path,
            {"child_exec": "python", "child_args": ["-u", str(real_script)]},
        )
        interface_path = root / "assets" / "interface.json"
        with interface_path.open("r", encoding="utf-8") as fh:
            interface = json.load(fh)
        result = analyzer.analyze_agent_scripts(root, interface_path, interface.get("agent") or {})
        # Neither -u nor existing absolute .py path should count toward unresolved
        assert result["declared_unresolved_count"] == 0
        assert result["declared_resolved_count"] == 1

    def test_warning_when_no_py_entries(self, tmp_path: Path):
        analyzer = load_analyzer()
        root = _build_minimal_project(
            tmp_path,
            {"child_exec": "python", "child_args": ["-u", "-X", "utf8"]},
        )
        interface_path = root / "assets" / "interface.json"
        with interface_path.open("r", encoding="utf-8") as fh:
            interface = json.load(fh)
        result = analyzer.analyze_agent_scripts(root, interface_path, interface.get("agent") or {})
        assert any("没有任何 .py" in w for w in result["warnings"])


class TestRenderAgentScriptPaths:
    def test_basic_info_includes_both_tables(self, tmp_path: Path):
        analyzer = load_analyzer()
        root = make_consumer_project(tmp_path)
        result = analyzer.analyze_project(root)
        content = analyzer.render_basic_info(result)
        assert "Agent script paths" in content
        assert "Declared (interface.json child_args)" in content
        assert "Discovered (root 与 4 层 ancestor" in content
        assert "Cross-check" in content
        assert "./agent/main.py" in content

    def test_basic_info_risk_bullet_counts_unresolved(self, tmp_path: Path):
        analyzer = load_analyzer()
        root = make_consumer_project(tmp_path)
        result = analyzer.analyze_project(root)
        content = analyzer.render_basic_info(result)
        assert "Agent script paths unresolved:" in content

    def test_basic_info_no_agent_block_shows_placeholder(self, tmp_path: Path):
        analyzer = load_analyzer()
        # Build a project WITHOUT agent block
        root = tmp_path / "NoAgent"
        (root / "assets" / "resource" / "base").mkdir(parents=True)
        write_json(
            root / "assets" / "interface.json",
            {
                "name": "NoAgent",
                "controller": [{"type": "Adb"}],
                "resource": [{"name": "default", "path": ["./resource/base"]}],
                "task": [],
            },
        )
        result = analyzer.analyze_project(root)
        content = analyzer.render_basic_info(result)
        assert "No agent block / child_args detected" in content

    def test_summary_includes_agent_script_paths_section(self, tmp_path: Path):
        analyzer = load_analyzer()
        root = make_consumer_project(tmp_path)
        result = analyzer.analyze_project(root)
        summary = analyzer.render_summary(result)
        assert "## Agent Script Paths" in summary
        assert "Declared (interface.json child_args)" in summary

    def test_summary_risks_includes_agent_counters(self, tmp_path: Path):
        analyzer = load_analyzer()
        root = make_consumer_project(tmp_path)
        result = analyzer.analyze_project(root)
        summary = analyzer.render_summary(result)
        assert "Unresolved agent script paths:" in summary
        assert "Orphan agent script path declarations:" in summary
        assert "Unreferenced agent entry candidates:" in summary


def test_analyze_project_includes_agent_scripts_field(tmp_path: Path):
    analyzer = load_analyzer()
    root = make_consumer_project(tmp_path)
    result = analyzer.analyze_project(root)
    assert "agent_scripts" in result
    assert result["agent_scripts"]["agent_block_present"] is True
    assert result["agent_scripts"]["declared_unresolved_count"] == 1


# ---------------------------------------------------------------------------
# Node-level `anchor` field resolution (regression test for issue #8)
# ---------------------------------------------------------------------------


def test_collect_anchor_defs_parses_string_list_object_and_clear_forms():
    analyzer = load_analyzer()

    assert analyzer.collect_anchor_defs("Cook", {"anchor": "Cooking"}) == [
        {"anchor": "Cooking", "target": "Cook", "cleared": False}
    ]
    assert analyzer.collect_anchor_defs("Cook", {"anchor": ["A", "B"]}) == [
        {"anchor": "A", "target": "Cook", "cleared": False},
        {"anchor": "B", "target": "Cook", "cleared": False},
    ]
    assert analyzer.collect_anchor_defs("Cook", {"anchor": {"Cooking": "TargetNode"}}) == [
        {"anchor": "Cooking", "target": "TargetNode", "cleared": False}
    ]
    assert analyzer.collect_anchor_defs("Cook", {"anchor": {"Cooking": ""}}) == [
        {"anchor": "Cooking", "target": None, "cleared": True}
    ]
    assert analyzer.collect_anchor_defs("Cook", {"anchor": {"Cooking": None}}) == [
        {"anchor": "Cooking", "target": None, "cleared": True}
    ]
    assert analyzer.collect_anchor_defs("Cook", {}) == []
    assert analyzer.collect_anchor_defs("Cook", {"anchor": ""}) == []


def test_anchor_string_and_list_forms_resolve_multi_target_without_conflict(tmp_path: Path):
    analyzer = load_analyzer()
    write_json(
        tmp_path / "pipeline" / "main.json",
        {
            "CookNodeA": {"recognition": "DirectHit", "anchor": "Cooking"},
            "CookNodeB": {"recognition": "DirectHit", "anchor": ["Cooking", "Prep"]},
            "Chef": {
                "recognition": "DirectHit",
                "next": ["[Anchor]Cooking", "[Anchor]Prep"],
            },
        },
    )

    result = analyzer.analyze_pipeline_files(tmp_path, [tmp_path / "pipeline" / "main.json"])

    assert result["unresolved_refs"] == []
    assert result["unresolved_anchor_refs"] == []
    assert result["dangling_anchor_targets"] == []
    edge_targets = {(edge["source"], edge["target"]) for edge in result["edges"]}
    # "Cooking" has two targets (CookNodeA and CookNodeB); both edges are kept,
    # not flagged as a conflict. "Prep" independently also targets CookNodeB.
    assert ("Chef", "CookNodeA") in edge_targets
    assert ("Chef", "CookNodeB") in edge_targets
    assert "CookNodeA" not in result["isolated_nodes"]
    assert "CookNodeB" not in result["isolated_nodes"]
    assert "CookNodeA" not in result["zero_in_degree_nodes"]
    assert "CookNodeB" not in result["zero_in_degree_nodes"]


def test_anchor_object_form_next_attr_is_also_redirected(tmp_path: Path):
    analyzer = load_analyzer()
    write_json(
        tmp_path / "pipeline" / "main.json",
        {
            "CookNodeA": {"recognition": "DirectHit", "anchor": "Cooking"},
            "Chef": {
                "recognition": "DirectHit",
                "next": [{"name": "Cooking", "anchor": True}],
            },
        },
    )

    result = analyzer.analyze_pipeline_files(tmp_path, [tmp_path / "pipeline" / "main.json"])

    edge_targets = {(edge["source"], edge["target"]) for edge in result["edges"]}
    assert ("Chef", "CookNodeA") in edge_targets
    assert result["unresolved_refs"] == []


def test_anchor_object_form_explicit_target_and_dangling_target(tmp_path: Path):
    analyzer = load_analyzer()
    write_json(
        tmp_path / "pipeline" / "main.json",
        {
            "Kitchen": {
                "recognition": "DirectHit",
                "anchor": {"Cooking": "CookNodeA", "Ghost": "MissingTarget"},
            },
            "CookNodeA": {"recognition": "DirectHit"},
            "Chef": {
                "recognition": "DirectHit",
                "next": ["[Anchor]Cooking", "[Anchor]Ghost"],
            },
        },
    )

    result = analyzer.analyze_pipeline_files(tmp_path, [tmp_path / "pipeline" / "main.json"])

    edge_targets = {(edge["source"], edge["target"]) for edge in result["edges"]}
    assert ("Chef", "CookNodeA") in edge_targets
    assert not any(target == "MissingTarget" for _, target in edge_targets)
    # "Ghost" IS declared (it just points at a missing node), so it must not
    # show up as an undeclared anchor reference.
    assert result["unresolved_anchor_refs"] == []
    assert "MissingTarget" not in result["unresolved_refs"]
    assert result["dangling_anchor_targets"] == [
        {"anchor": "Ghost", "target": "MissingTarget", "file": "pipeline/main.json"}
    ]


def test_anchor_object_form_clear_declares_name_without_target(tmp_path: Path):
    analyzer = load_analyzer()
    write_json(
        tmp_path / "pipeline" / "main.json",
        {
            "Kitchen": {"recognition": "DirectHit", "anchor": {"Cooking": ""}},
            "Chef": {"recognition": "DirectHit", "next": ["[Anchor]Cooking"]},
        },
    )

    result = analyzer.analyze_pipeline_files(tmp_path, [tmp_path / "pipeline" / "main.json"])

    assert "Cooking" in result["anchor_names"]
    # The name is declared (just currently cleared), so referencing it is
    # neither an undeclared anchor reference nor a dangling target -- it
    # simply resolves to no edge at all.
    assert result["unresolved_anchor_refs"] == []
    assert result["dangling_anchor_targets"] == []
    assert result["edges"] == []


def test_anchor_undeclared_name_is_reported_as_dangling_reference(tmp_path: Path):
    analyzer = load_analyzer()
    write_json(
        tmp_path / "pipeline" / "main.json",
        {"Chef": {"recognition": "DirectHit", "next": ["[Anchor]NeverDeclared"]}},
    )

    result = analyzer.analyze_pipeline_files(tmp_path, [tmp_path / "pipeline" / "main.json"])

    assert result["unresolved_anchor_refs"] == ["NeverDeclared"]
    assert "NeverDeclared" not in result["unresolved_refs"]
    assert result["edges"] == []


def test_anchor_resolution_removes_node_from_orphan_candidates(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "AnchorProject"
    write_json(
        root / "interface.json",
        {
            "resource": [{"name": "default", "path": ["./resource/base"]}],
            "task": [{"name": "Entry", "entry": "Chef"}],
        },
    )
    write_json(
        root / "resource" / "base" / "pipeline" / "main.json",
        {
            "Chef": {"recognition": "DirectHit", "next": ["[Anchor]Cooking"]},
            "CookNodeA": {"recognition": "DirectHit", "anchor": "Cooking"},
        },
    )

    result = analyzer.analyze_project(root)
    pipeline = result["pipeline"]

    assert "CookNodeA" not in pipeline["orphan_candidates"]
    assert "CookNodeA" not in pipeline["zero_in_degree_nodes"]
    assert "CookNodeA" not in pipeline["isolated_nodes"]


def test_analyze_project_labels_cross_bundle_override_separately(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "OverrideProject"
    write_json(
        root / "interface.json",
        {
            "resource": [
                {"name": "base", "path": ["./resource/base"]},
                {"name": "channel", "path": ["./resource/channel"]},
            ],
            "task": [{"name": "Entry", "entry": "BaseOnly"}],
        },
    )
    write_json(
        root / "resource" / "base" / "pipeline" / "main.json",
        {
            "BaseOnly": {"recognition": "DirectHit"},
            "SharedNode": {"recognition": "DirectHit", "next": ["BaseOnly"]},
        },
    )
    write_json(
        root / "resource" / "channel" / "pipeline" / "main.json",
        {
            "SharedNode": {"recognition": "OCR", "expected": ["Channel"]},
        },
    )

    pipeline = analyzer.analyze_project(root)["pipeline"]

    assert pipeline["duplicate_nodes"] == []
    assert pipeline["cross_bundle_override_nodes"] == ["SharedNode"]


def test_analyze_pipeline_files_flags_same_bundle_duplicate_only(tmp_path: Path):
    analyzer = load_analyzer()
    base = tmp_path / "resource" / "base"
    first = base / "pipeline" / "main.json"
    second = base / "pipeline" / "override.json"
    write_json(first, {"SharedNode": {"recognition": "DirectHit"}})
    write_json(second, {"SharedNode": {"recognition": "OCR", "expected": ["Base"]}})

    pipeline = analyzer.analyze_pipeline_files(
        tmp_path,
        [first, second],
        [base],
        {str(base): "base"},
    )

    assert pipeline["duplicate_nodes"] == ["SharedNode"]
    assert pipeline["cross_bundle_override_nodes"] == []


# ---------------------------------------------------------------------------
# Windows console encoding + async visitor typing (issue #8 minor extras)
# ---------------------------------------------------------------------------


def test_main_handles_non_ascii_node_names_without_unicode_error(tmp_path: Path, capsys):
    analyzer = load_analyzer()
    root = tmp_path / "NonAsciiProject"
    write_json(
        root / "interface.json",
        {"resource": [{"name": "default", "path": ["./resource/base"]}]},
    )
    write_json(
        root / "resource" / "base" / "pipeline" / "main.json",
        {"烹饪": {"recognition": "DirectHit"}},
    )

    exit_code = analyzer.main([str(root), "--json"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "烹饪" in captured.out


def test_python_pipeline_calls_are_collected_from_async_functions(tmp_path: Path):
    analyzer = load_analyzer()
    root = tmp_path / "AsyncAgentProject"
    agent = root / "agent" / "async_action.py"
    agent.parent.mkdir(parents=True, exist_ok=True)
    agent.write_text(
        "async def run(context):\n"
        "    await context.run_task('AsyncTarget')\n",
        encoding="utf-8",
    )

    result = analyzer.analyze_python_pipeline_calls(root)

    assert result["targets"] == ["AsyncTarget"]
