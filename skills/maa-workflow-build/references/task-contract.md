# Task Contract

Create this contract before editing. Keep facts, decisions, assumptions, and open questions separate. Update the contract only when new evidence or a user decision changes the intended outcome.

```yaml
task_id: stable-local-identifier
goal: observable outcome in one sentence
non_goals: []

start_states:
  - id: stable-state-name
    required: true | false
    evidence: how the state is recognized
    evidence_status: observed | source-backed | assumed | unknown
    evidence_artifact: current screenshot/recognition trace for observed, or current source path for source-backed
  - id: unknown-state
    required: true | false
    evidence: unexpected or insufficient observation
    evidence_status: unknown

success_states:
  - id: completed-state
    required: true | false
    evidence: observable postcondition
    evidence_status: observed | source-backed | assumed | unknown
    evidence_artifact: current screenshot/recognition trace for observed, or current source path for source-backed

transitions:
  - from: stable-state-name
    required: true | false
    action: minimal observable action
    action_target: recognized text, template, or justified coordinate
    action_target_evidence_status: observed | source-backed | assumed | unknown
    action_target_evidence_artifact: current screenshot plus box/template/coordinate basis for observed, or current source path for source-backed
    to: completed-state
    evidence_status: observed | source-backed | assumed | unknown
    evidence_artifact: current screenshot/runtime trace for observed, or current source path for source-backed

failure_states:
  - id: bounded-failure
    response: recover | stop | request-user

constraints: []
allowed_side_effects: []
forbidden_side_effects: []

facts: []
user_decisions: []
assumptions:
  - statement: reversible working assumption
    validation: how and when to verify it
open_questions: []

exploration_required: true | false

acceptance_criteria:
  - id: AC-1
    behavior: externally observable behavior
    evidence_required: test, screenshot, log, graph, or file inspection
    required: true
```

## Contract rules

- Express the goal as a result, not an implementation choice.
- Describe every start and success state using observable evidence.
- Classify required UI states, transitions, and action targets without promoting source inference or assumptions to observed evidence.
- Use `observed` only with a current screenshot, recognition result, or runtime trace. A source path can support only `source-backed` until runtime evidence confirms it.
- Mark optional or deferred states and transitions as `required: false`; never defer a `required: true` UI fact to pass the design gate.
- Set `exploration_required: true` when a required runtime UI fact is not `observed`; resolve it through the exploration protocol before `DESIGN`.
- Include a no-op path when the requested action is unnecessary or disabled.
- Make unsafe fallback behavior forbidden by default.
- Require a post-action observation; an attempted click or executed node is not success.
- Ask the user only when an unresolved choice changes safety, irreversible behavior, or the meaning of success.
- Keep optional enhancements outside the required acceptance criteria.

## Example: stamina recovery

```yaml
goal: Resume the original task after using at most one owned normal stamina item when stamina is insufficient.
non_goals:
  - Buy stamina items.
  - Spend premium currency.
start_states:
  - id: original-task
    required: true
    evidence: the task entry or its stable pre-action screen is recognized
    evidence_status: observed
    evidence_artifact: screenshot-or-recognition-trace-id
  - id: stamina-insufficient-dialog
    required: true
    evidence: the insufficient-stamina message is recognized
    evidence_status: observed
    evidence_artifact: screenshot-or-recognition-trace-id
  - id: recovery-dialog
    required: true
    evidence: the owned normal item and its use control are recognized
    evidence_status: observed
    evidence_artifact: screenshot-or-recognition-trace-id
  - id: unknown-state
    required: true
    evidence: none of the supported stable states is recognized
    evidence_status: observed
    evidence_artifact: failure-path-recognition-trace-id
success_states:
  - id: resumed
    required: true
    evidence: stamina increased or the insufficient dialog disappeared, and the original task resumed
    evidence_status: observed
    evidence_artifact: authorized-runtime-trace-id
transitions:
  - from: stamina-insufficient-dialog
    required: true
    action: open the recovery dialog
    action_target: recognized recovery control
    action_target_evidence_status: observed
    action_target_evidence_artifact: screenshot-or-recognition-trace-id
    to: recovery-dialog
    evidence_status: observed
    evidence_artifact: authorized-runtime-trace-id
constraints:
  - Never purchase an item or spend premium currency.
  - Never repeat consumption after an unverified attempt.
exploration_required: false
acceptance_criteria:
  - id: AC-1
    behavior: Sufficient stamina follows the no-op path.
    evidence_required: behavioral test
    required: true
  - id: AC-2
    behavior: An owned normal item is used at most once and recovery is observed.
    evidence_required: authorized end-to-end trace
    required: true
  - id: AC-3
    behavior: Missing items, paid-only recovery, and ambiguous recognition stop safely.
    evidence_required: failure-path tests
    required: true
```
