from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "maa-workflow-build"


def test_workflow_build_owns_the_end_to_end_control_loop():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    for phase in (
        "SPECIFY",
        "DISCOVER",
        "EXPLORE",
        "DESIGN",
        "IMPLEMENT",
        "VERIFY",
        "COMPLETE",
        "RECOVER",
    ):
        assert phase in text

    for routed_skill in (
        "$maa-pipeline-guide",
        "$maa-pipeline-generate",
        "$maa-pipeline-option",
        "$maa-pipeline-testing",
        "$maa-cli-operate",
    ):
        assert routed_skill in text

    assert "Do not declare completion" in text
    assert "references/task-contract.md" in text
    assert "references/run-state.md" in text
    assert "references/exploration-first.md" in text
    assert "references/acceptance-protocol.md" in text
    assert "references/recovery-policy.md" in text


def test_workflow_build_consumes_init_and_graph_artifacts_without_invoking_setup():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    assert "Never invoke `$maa-project-init` or `$maa-pipeline-graph` automatically" in text
    assert "only when the user explicitly requests" in text
    assert "basic_info.md" in text
    assert "pipeline_overview.html" in text
    assert "continue with targeted source discovery" in text


def test_specialist_roles_form_a_conditional_feedback_loop_not_a_fixed_pipeline():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    recovery = (SKILL_DIR / "references" / "recovery-policy.md").read_text(
        encoding="utf-8"
    )

    assert "owns state-machine assembly and integration" in text
    assert "$maa-pipeline-guide" in text and "reference and constraint source" in text
    assert "$maa-pipeline-generate" in text and "primary producer" in text
    assert "Invoke `$maa-pipeline-option` only when" in text
    assert "Run `$maa-pipeline-testing` after each coherent implementation increment" in text
    assert "Do not treat the specialists as a fixed" in text

    for failure_owner in (
        "Recognition or action-node failure",
        "Option-surface or override-wiring failure",
        "State-model failure",
        "Integration or control-flow failure",
    ):
        assert failure_owner in recovery


def test_workflow_contracts_define_state_feedback_and_exit_conditions():
    task_contract = (SKILL_DIR / "references" / "task-contract.md").read_text(
        encoding="utf-8"
    )
    run_state = (SKILL_DIR / "references" / "run-state.md").read_text(
        encoding="utf-8"
    )
    acceptance = (SKILL_DIR / "references" / "acceptance-protocol.md").read_text(
        encoding="utf-8"
    )
    recovery = (SKILL_DIR / "references" / "recovery-policy.md").read_text(
        encoding="utf-8"
    )

    for field in (
        "goal",
        "start_states",
        "success_states",
        "constraints",
        "acceptance_criteria",
    ):
        assert field in task_contract

    for field in (
        "status",
        "summary",
        "next_actions",
        "artifacts",
        "evidence",
        "stop_reason",
    ):
        assert field in run_state

    assert "observable evidence" in acceptance
    assert "root cause" in recovery
    assert "safe retry" in recovery
    assert "stop condition" in recovery


def test_guessed_states_open_an_exploration_gate_before_design():
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    contract = (SKILL_DIR / "references" / "task-contract.md").read_text(
        encoding="utf-8"
    )
    run_state = (SKILL_DIR / "references" / "run-state.md").read_text(encoding="utf-8")

    assert "### 3. EXPLORE" in text
    assert "### 4. DESIGN" in text
    assert "Enter DESIGN only when the exploration gate is closed" in text
    assert "evidence_status: observed" in text
    assert "evidence_status: guessed" in text
    assert "Do not write Pipeline nodes, CustomAction code, or a full implementation plan" in text
    assert "Never write a node first and match it to the UI afterwards." in text

    assert "evidence_status: observed | guessed" in contract
    assert "evidence_artifact" in contract
    assert "opens the exploration gate" in contract
    assert "entry precondition of every reused node" in contract

    # The gate only considers states the contract marks `required`, so the
    # contract has to define that marker for every start and success state.
    assert "required: true | false" in contract
    assert contract.count("required: true | false") >= 2
    assert "The exploration gate only considers required states" in contract

    assert "EXPLORE" in run_state
    assert "exploration:" in run_state
    assert "gate: open | closed" in run_state
    assert "round_trip_complete" in run_state
    assert "observed_transitions" in run_state
    assert "unreachable_states" in run_state


def test_exploration_first_reference_defines_a_checkable_round_trip():
    exploration = (SKILL_DIR / "references" / "exploration-first.md").read_text(
        encoding="utf-8"
    )
    acceptance = (SKILL_DIR / "references" / "acceptance-protocol.md").read_text(
        encoding="utf-8"
    )
    recovery = (SKILL_DIR / "references" / "recovery-policy.md").read_text(
        encoding="utf-8"
    )

    assert "at least one complete round-trip" in exploration
    for required in (
        "screencap",
        "ocr",
        "click",
        "exit criteria",
        "Reused components have preconditions",
        "When exploration cannot run",
    ):
        assert required.lower() in exploration.lower(), required

    assert "write or edit Pipeline nodes" in exploration
    assert "write CustomAction or CustomRecognition code" in exploration
    assert "stay `guessed`" in exploration

    assert "exploration-trace" in acceptance
    assert "no criterion depends on a state that is still `evidence_status: guessed`" in acceptance

    assert "Unexplored-scene or assumed-precondition failure" in recovery
    assert "`EXPLORE` in `$maa-workflow-build`" in recovery


def test_workflow_build_metadata_adapter_docs_and_evals_are_discoverable():
    metadata = yaml.safe_load(
        (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )
    adapter = json.loads(
        (
            ROOT
            / "adapters"
            / "maahub"
            / "skills"
            / "maa-workflow-build.json"
        ).read_text(encoding="utf-8")
    )
    evals = json.loads(
        (ROOT / "evals" / "maa-workflow-build.json").read_text(encoding="utf-8")
    )

    assert "$maa-workflow-build" in metadata["interface"]["default_prompt"]
    assert adapter["id"] == "KhazixW2/maa-workflow-build"
    assert evals["skill_name"] == "maa-workflow-build"
    assert len(evals["evals"]) >= 4
    assert any("体力药剂" in case["prompt"] for case in evals["evals"])
    stamina_eval = next(case for case in evals["evals"] if "体力药剂" in case["prompt"])
    assert "不自动调用 init 或 graph" in stamina_eval["expected_output"]
    feedback_eval = next(
        case
        for case in evals["evals"]
        if case["eval_name"] == "route-specialist-failures-to-owner"
    )
    assert "guide 只作为规则来源" in feedback_eval["expected_output"]
    assert "testing 的证据分类失败" in feedback_eval["expected_output"]
    exploration_eval = next(
        case
        for case in evals["evals"]
        if case["eval_name"] == "explore-unknown-scene-before-planning"
    )
    assert "exploration-first" in exploration_eval["expected_output"]
    assert "round-trip" in exploration_eval["expected_output"]

    observed_eval = next(
        case
        for case in evals["evals"]
        if case["eval_name"] == "enter-design-with-observed-ui-trace"
    )
    assert "关闭 exploration 闸门" in observed_eval["expected_output"]
    assert "不重复强制探索" in observed_eval["expected_output"]

    authority_eval = next(
        case
        for case in evals["evals"]
        if case["eval_name"] == "do-not-infer-dangerous-exploration-authority"
    )
    assert "不等于授权在探索时实际触发这些副作用" in authority_eval["expected_output"]
    assert "non-mutating probe" in authority_eval["expected_output"]

    assert (ROOT / "docs" / "skills" / "maa-workflow-build.md").is_file()


def test_workflow_build_docs_show_the_non_linear_specialist_loop():
    docs = (ROOT / "docs" / "skills" / "maa-workflow-build.md").read_text(
        encoding="utf-8"
    )

    assert "flowchart TD" in docs
    assert "guide 不是执行阶段" in docs
    assert "负责整体组装" in docs
    assert "EXPLORE" in docs
    assert "round-trip" in docs
    assert "evidence_status" in docs


def test_specialist_skills_route_uncompiled_end_to_end_requests_to_workflow_build():
    for skill_name in (
        "maa-pipeline-guide",
        "maa-pipeline-generate",
        "maa-pipeline-option",
        "maa-pipeline-testing",
    ):
        text = (ROOT / "skills" / skill_name / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert "$maa-workflow-build" in text, skill_name


def test_specialist_skills_do_not_auto_invoke_project_init():
    for skill_name in (
        "maa-pipeline-guide",
        "maa-pipeline-generate",
        "maa-pipeline-graph",
        "maa-pipeline-option",
        "maa-pipeline-testing",
    ):
        text = (ROOT / "skills" / skill_name / "SKILL.md").read_text(
            encoding="utf-8"
        )
        assert "不得自动调用 `$maa-project-init`" in text, skill_name
