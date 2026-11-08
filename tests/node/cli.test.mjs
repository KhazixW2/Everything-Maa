import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const CLI = path.join(REPO_ROOT, "packages", "cli", "bin", "everything-maa.js");

function run(args, cwd) {
  const result = spawnSync(process.execPath, [CLI, ...args], {
    cwd,
    encoding: "utf8",
  });
  assert.equal(result.status, 0, `stderr:\n${result.stderr}\nstdout:\n${result.stdout}`);
  return result.stdout;
}

function runFailure(args, cwd) {
  const result = spawnSync(process.execPath, [CLI, ...args], {
    cwd,
    encoding: "utf8",
  });
  assert.notEqual(result.status, 0, `command unexpectedly succeeded:\n${result.stdout}`);
  return `${result.stdout}${result.stderr}`;
}

function tempProject(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "everything-maa-test-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return root;
}

test("list reports all skills and MCP profiles", () => {
  const output = run(["list"], REPO_ROOT);
  assert.match(output, /maa-project-init/);
  assert.match(output, /maa-wiki/);
  assert.match(output, /skills-only/);
  assert.match(output, /authoring: maa-mcp, create-maa-project/);
  assert.match(output, /full: maa-mcp, create-maa-project, playwright/);
});

test("dry-run does not create installation directories", (t) => {
  const root = tempProject(t);
  const output = run(
    ["install", "--target", "codex", "--profile", "full", "--dry-run"],
    root,
  );
  assert.match(output, /no files were changed/);
  assert.equal(fs.existsSync(path.join(root, ".agents")), false);
  assert.equal(fs.existsSync(path.join(root, ".codex")), false);
});

test("Claude project install is idempotent, preserves unrelated MCP, and uninstalls cleanly", (t) => {
  const root = tempProject(t);
  const mcpPath = path.join(root, ".mcp.json");
  fs.writeFileSync(
    mcpPath,
    JSON.stringify({ mcpServers: { existing: { command: "existing-server" } } }, null, 2),
  );

  run(["install", "--target", "claude", "--profile", "full"], root);
  run(["install", "--target", "claude", "--profile", "full"], root);

  const skillRoot = path.join(root, ".claude", "skills");
  const expectedSkillCount = fs
    .readdirSync(path.join(REPO_ROOT, "skills"), { withFileTypes: true })
    .filter((entry) => entry.isDirectory()).length;
  assert.equal(fs.readdirSync(skillRoot).length, expectedSkillCount);
  const installedMcp = JSON.parse(fs.readFileSync(mcpPath, "utf8"));
  assert.equal(installedMcp.mcpServers.existing.command, "existing-server");
  assert.deepEqual(installedMcp.mcpServers["maa-mcp"].args, [
    "--from",
    "maa-mcp==1.2.3",
    "maa-mcp",
  ]);
  assert.deepEqual(installedMcp.mcpServers["create-maa-project"].args, [
    "--upgrade",
    "--from",
    "create-maa-project",
    "create-maa-project",
    "--mcp",
  ]);
  assert.equal(installedMcp.mcpServers["create-maa-project"].env, undefined);
  assert.equal(installedMcp.mcpServers.playwright.args.at(-1), "--isolated");

  run(["uninstall", "--target", "claude"], root);
  assert.equal(fs.existsSync(skillRoot), true);
  assert.equal(fs.readdirSync(skillRoot).length, 0);
  const remainingMcp = JSON.parse(fs.readFileSync(mcpPath, "utf8"));
  assert.deepEqual(remainingMcp.mcpServers, { existing: { command: "existing-server" } });
  assert.equal(fs.existsSync(path.join(root, ".claude", ".everything-maa.json")), false);
});

test("Codex project install uses a managed TOML block and preserves other config", (t) => {
  const root = tempProject(t);
  const configPath = path.join(root, ".codex", "config.toml");
  fs.mkdirSync(path.dirname(configPath), { recursive: true });
  fs.writeFileSync(configPath, 'model = "gpt-5"\n', "utf8");

  run(["install", "--target", "codex", "--profile", "full"], root);
  const installed = fs.readFileSync(configPath, "utf8");
  assert.match(installed, /# BEGIN EVERYTHING-MAA MCP/);
  assert.match(installed, /\[mcp_servers\.maa-mcp\]/);
  assert.match(installed, /\[mcp_servers\.create-maa-project\]/);
  assert.doesNotMatch(installed, /CREATE_MAA_PROJECT_AUTO_UPDATE/);
  assert.match(installed, /@playwright\/mcp@0\.0\.78/);

  run(["uninstall", "--target", "codex"], root);
  assert.equal(fs.readFileSync(configPath, "utf8"), 'model = "gpt-5"\n');
  assert.equal(fs.existsSync(path.join(root, ".codex", ".everything-maa.json")), false);
});

test("authoring profile installs project lifecycle MCP without Playwright", (t) => {
  const root = tempProject(t);
  run(["install", "--target", "claude", "--profile", "authoring"], root);
  const document = JSON.parse(fs.readFileSync(path.join(root, ".mcp.json"), "utf8"));
  assert.deepEqual(Object.keys(document.mcpServers).sort(), ["create-maa-project", "maa-mcp"]);
});

test("uninstall preserves a locally modified skill and keeps recovery state", (t) => {
  const root = tempProject(t);
  run(["install", "--target", "claude", "--profile", "skills-only"], root);
  const modified = path.join(root, ".claude", "skills", "maa-project-init", "local-note.txt");
  fs.writeFileSync(modified, "keep me\n", "utf8");

  const output = run(["uninstall", "--target", "claude"], root);
  assert.match(output, /Preserved modified skill maa-project-init/);
  assert.equal(fs.existsSync(modified), true);
  assert.equal(fs.existsSync(path.join(root, ".claude", ".everything-maa.json")), true);
});

test("conflicts are detected before any installation files are written", (t) => {
  const root = tempProject(t);
  fs.writeFileSync(
    path.join(root, ".mcp.json"),
    JSON.stringify({ mcpServers: { "maa-mcp": { command: "custom" } } }),
  );

  const output = runFailure(["install", "--target", "claude"], root);
  assert.match(output, /MCP server maa-mcp already exists/);
  assert.equal(fs.existsSync(path.join(root, ".claude")), false);
});
