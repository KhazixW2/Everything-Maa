import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const BASE_ARGS = ["--upgrade", "--from", "maafw-cli", "maafw-cli"];

function run(args, cwd) {
  const result = spawnSync("uvx", [...BASE_ARGS, ...args], {
    cwd,
    encoding: "utf8",
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`Command failed (${result.status}): ${result.stderr || result.stdout}`);
  }
  return result.stdout;
}

function runJson(args, cwd) {
  const stdout = run(["--json", ...args], cwd);
  try {
    return JSON.parse(stdout);
  } catch (error) {
    throw new Error(`Expected JSON from ${args.join(" ")}: ${stdout}`, { cause: error });
  }
}

function safeRemoveTemp(target) {
  const tempRoot = path.resolve(os.tmpdir());
  const resolved = path.resolve(target);
  const relative = path.relative(tempRoot, resolved);
  if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`Refusing unsafe temporary cleanup target: ${resolved}`);
  }
  fs.rmSync(resolved, { recursive: true, force: true });
}

const root = fs.mkdtempSync(path.join(os.tmpdir(), "everything-maa-cli-smoke-"));
const pipelinePath = path.join(root, "pipeline.json");
const commandCwd = process.cwd();
const daemonBefore = runJson(["daemon", "status"], commandCwd);
const daemonWasRunning = daemonBefore.status === "running";

try {
  const version = run(["--version"], commandCwd).trim();
  if (!version) throw new Error("maafw-cli --version returned no version");

  const resource = runJson(["resource", "status"], commandCwd);
  if (typeof resource.ocr_model !== "boolean" || typeof resource.ocr_path !== "string") {
    throw new Error(`Unexpected resource report: ${JSON.stringify(resource)}`);
  }

  fs.writeFileSync(
    pipelinePath,
    `${JSON.stringify({ Start: { recognition: "DirectHit", action: "DoNothing" } }, null, 2)}\n`,
    "utf8",
  );
  const validation = runJson(["pipeline", "validate", pipelinePath], commandCwd);
  const nodes = validation.nodes || validation.node_names || [];
  const validated = validation.valid === true && Array.isArray(nodes) && nodes.includes("Start");
  const deferredForResources =
    !resource.ocr_model &&
    validation.valid === false &&
    Array.isArray(nodes) &&
    typeof validation.error === "string";
  if (!validated && !deferredForResources) {
    throw new Error(`Unexpected Pipeline validation: ${JSON.stringify(validation)}`);
  }

  console.log(
    `maafw-cli smoke passed: ${version}; OCR model ${resource.ocr_model ? "ready" : "not downloaded"}; Pipeline validation ${validated ? `found ${nodes.length} node` : "deferred until resources are installed"}.`,
  );
} finally {
  if (!daemonWasRunning) {
    const daemonAfter = runJson(["daemon", "status"], commandCwd);
    if (daemonAfter.status === "running") runJson(["daemon", "stop"], commandCwd);
  }
  safeRemoveTemp(root);
}
