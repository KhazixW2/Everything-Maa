# maafw-cli command contract

Resolve the latest external release by default:

```bash
uvx --upgrade --from maafw-cli maafw-cli --version
uvx --upgrade --from maafw-cli maafw-cli --json COMMAND
```

The package requires Python 3.10 or later and is currently alpha software. If the user explicitly requests a fixed version, use `uvx --from maafw-cli==VERSION maafw-cli`; when no version is specified, keep the latest resolution above. The command and JSON contracts may change, so verify `--help` if observed output no longer matches this reference.

## Runtime selection

| Need | Command shape |
| --- | --- |
| Check local models | `--json resource status` |
| Discover controllers | `--json device adb`, `--json device win32`, or `--json device all` |
| Connect ADB | `--on NAME --json connect adb ADDRESS --size short:720` |
| Connect Win32 | `--on NAME --json connect win32 TITLE_OR_HWND --size short:720` |
| List sessions | `--json session list` |
| Inspect daemon | `--json daemon status` |

Put global options such as `--json` and `--on NAME` before the subcommand.

### Screenshot size

For ADB and Win32, `connect` accepts `--size short:<px>`, `--size long:<px>`, or
`--size raw`. Both controller kinds default to `short:720`, matching the
MaaFramework 720p baseline. The other side scales by aspect ratio, so this is a
short-side baseline rather than a guarantee of exactly 720x1280 for every
device. `screenshot` has no separate scaling option; it uses the size configured
when the named session connected.

Use `raw` only when explicitly required for evidence or diagnosis. Raw-size
screenshots no longer match the 720p ROI/template baseline and can make copied
coordinates resolve incorrectly on other devices. In the documented upstream contract, PlayCover
and wlroots do not expose `--size`; their controllers use the runtime defaults.

### MaaFramework scaling behavior

Inside MaaFramework, `ControllerAgent` defaults to a 720-pixel screenshot short
side. When a raw frame's size changes, or the target size is not initialized,
the controller recalculates a target size from the current raw size, then
resizes it with `INTER_AREA` unless raw size was requested. With `short:720`,
the shorter side is exactly 720 and the other side is calculated from the raw
aspect ratio, then rounded. It is therefore a short-side baseline, not a fixed
`720x1280` contract.

Pipeline coordinates are evaluated on this cached, scaled image: `roi`,
`roi_offset`, recognition `box`, `target`, and `target_offset` all use those
coordinates. For touch actions, MaaFramework maps the point back to raw screen
coordinates using the current raw/target ratios. A few controllers declare
`NoScalingTouchPoints` and intentionally skip that final mapping, so their
input contract must be checked separately.

ProjectInterface V2 expresses the same choice per controller:
`display_short_side` and `display_long_side` select the target short or long
side; `display_expand` takes `[width, height]` and applies Unity Canvas Scaler
Expand semantics (`scale = max(width / raw_width, height / raw_height)`), so the
output preserves the raw aspect ratio and both sides are at least the reference;
`display_raw` requests unscaled screenshots. These fields are mutually exclusive
in the PI protocol. When none is set, the PI runtime passes short side 720 to
MaaFramework. The current MaaPiCli runner resolves overlapping settings in
`raw -> expand -> long -> short` order, but a valid Interface must not rely on
that tie-break. `display_raw` is useful for diagnosing a raw frame, but
resources whose ROIs and templates assume the normalized baseline must not be
reused against it.

## Recognition and actions

```bash
uvx --upgrade --from maafw-cli maafw-cli --on phone --json ocr
uvx --upgrade --from maafw-cli maafw-cli --on phone --json reco OCR expected=Settings
uvx --upgrade --from maafw-cli maafw-cli --on phone --json reco TemplateMatch template=button.png threshold=0.8
uvx --upgrade --from maafw-cli maafw-cli --on phone --json click e3
uvx --upgrade --from maafw-cli maafw-cli --on phone --json screenshot
```

Supported recognition types are `TemplateMatch`, `FeatureMatch`, `ColorMatch`, and `OCR`. Use `reco --raw JSON` when the recognition config cannot be represented safely as `key=value` arguments.

## Pipeline operations

The `./assets/resource/base/...` paths below are examples from a boilerplate-family packaged layout. In a Project Interface V2 project, derive resource paths from the main Interface's `resource[].path`, which resolves relative to that Interface.

```bash
uvx --upgrade --from maafw-cli maafw-cli --json pipeline validate ./assets/resource/base/pipeline
uvx --upgrade --from maafw-cli maafw-cli --json pipeline load ./assets/resource/base/pipeline
uvx --upgrade --from maafw-cli maafw-cli --json pipeline show Start
uvx --upgrade --from maafw-cli maafw-cli --on phone --json pipeline run ./assets/resource/base/pipeline Start
uvx --upgrade --from maafw-cli maafw-cli --on phone --json pipeline run ./pipeline.json Start --override '{"Start":{"timeout":5000}}'
```

`pipeline validate` and `pipeline load` do not execute a task. `pipeline run` uses the selected controller and may perform every action reachable from the entry node.

## Resources and custom code

```bash
uvx --upgrade --from maafw-cli maafw-cli --json resource status
uvx --upgrade --from maafw-cli maafw-cli --json resource download-ocr
uvx --upgrade --from maafw-cli maafw-cli --json resource load-image ./assets/resource/base/image
uvx --upgrade --from maafw-cli maafw-cli --json custom list
uvx --upgrade --from maafw-cli maafw-cli --json custom load ./agent/main.py
```

Resource download changes the user cache. `custom load` imports and executes Python code; inspect the file and dependencies first.

## Output contract

- Parse stdout as one JSON value when `--json` is present.
- Treat a nonzero process status as command failure even when stderr contains a structured explanation.
- Do not assume all successful commands return the same keys; validate the fields needed by the operation.
- Keep screenshot paths and element references tied to the named session that produced them.
