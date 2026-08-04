# Exploration Protocol

Use this protocol when any required runtime UI state, transition, or action target is not `observed`. Keep the phase as `DISCOVER` and the run-state mode as `exploration-first` until the design gate passes.

## Evidence classes

- `observed`: confirmed on the current UI by a screenshot, OCR/TemplateMatch result, or runtime trace.
- `source-backed`: inferred from current Pipeline, Python, image, or interface files but not confirmed on the current UI.
- `assumed`: a plausible working hypothesis without supporting current evidence.
- `unknown`: not yet described well enough to test.

Never promote `source-backed`, `assumed`, or `unknown` evidence to `observed` without a visual or runtime artifact. An `observed` item must cite a current screenshot, recognition result, or runtime trace; a source path alone can support only `source-backed`. User-supplied current screenshots or traces may count as observed when their screen, locale, resolution, and place in the flow are identifiable.

## Observe-act-observe loop

1. Capture or inspect the current stable screen. Record the screenshot or trace, visible text, recognition boxes or ROIs, and the state name it supports.
2. Choose one minimal action whose expected effect is stated and whose side effects are allowed by the task contract.
3. Prefer acting on the current recognition result. Re-observe after every click, swipe, navigation, timing change, or unexpected output; never chain blind clicks.
4. Record the transition as `state_before -> observation -> guarded_action -> state_after`, including artifact paths or stable trace identifiers.
5. Continue one transition at a time until every `required: true` UI fact is observed and at least one representative required path reaches the success or handoff state and then a stable return, terminal, or safe-stop state.

Use temporary recognition probes rather than deliverable nodes during exploration. Do not draft the complete Pipeline, a full CustomAction, or a fixed coordinate route and then search for UI evidence that fits it.

## Action-target evidence

- For a clickable text control, prefer OCR plus `Click` and omit `target` and `target_offset`; MaaFramework then clicks the current recognition box.
- For a stable non-text button or icon, capture a lossless 720p template and prefer TemplateMatch plus `Click`.
- Treat `DirectHit` plus a fixed target, an explicit coordinate target, or `target_offset` from a different recognition as an evidence-required exception. Use one only when the actual control cannot be recognized reliably, the current screenshot and coordinate basis justify it, and a focused runtime check verifies the click.
- Do not invent a `run_pipeline` ROI parameter or another provider capability. Inspect the active tool schema and use direct OCR/recognition with a bounded ROI when supported; otherwise use the available screenshot and recognition results.

## Safety and stop conditions

- Use a non-mutating probe before purchases, resource consumption, battle entry, confirmations, or other account-changing actions.
- Cross a side-effect boundary only when it is explicitly allowed and the pre-action state is observed.
- If no device or current visual artifact is available, the next action is unauthorized, or the state remains ambiguous, set the design gate to `blocked` and request only the smallest missing evidence or decision.
- Do not force a round trip through a destructive or naturally terminal flow. An authorized end-to-end trace ending in a known terminal or safe handoff state satisfies the path requirement.

## Design gate

Set `design_gate: pass` only when all of the following are true:

- every required start and success state used by the proposed flow is observed;
- every `required: true` transition and action target is observed;
- at least one representative required path reaches a success or handoff state and a stable return, terminal, or safe-stop state;
- optional or deferred branches are marked `required: false` and explicitly bounded as safe stop, user handoff, or later acceptance work;
- each observation has a screenshot, recognition result, or runtime trace identifier.

Never defer a `required: true` fact to make the gate pass. Otherwise keep `design_gate: blocked` and remain in `DISCOVER`.

When the gate passes, update the contract and run state as one phase transition: set `exploration_required: false`, set `mode: standard`, preserve `design_gate: pass`, and set `phase: DESIGN`. Then use the observed state and transition records to design the complete state machine.
