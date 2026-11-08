import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function readJson(relative) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, relative), "utf8"));
}

function fail(message) {
  throw new Error(message);
}

function checkVersions() {
  const pkg = readJson("package.json");
  const codex = readJson(".codex-plugin/plugin.json");
  const claude = readJson(".claude-plugin/plugin.json");
  const marketplace = readJson(".claude-plugin/marketplace.json");
  const distribution = readJson("distribution/catalog.json");
  const semver = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$/;
  if (!semver.test(pkg.version)) fail(`package version is not semver: ${pkg.version}`);
  if (codex.version !== pkg.version || claude.version !== pkg.version) {
    fail(`version mismatch: package=${pkg.version}, codex=${codex.version}, claude=${claude.version}`);
  }
  const marketplacePlugin = marketplace.plugins.find((item) => item.name === "everything-maa");
  if (!marketplacePlugin || marketplacePlugin.version !== pkg.version) {
    fail(`Claude marketplace does not expose everything-maa@${pkg.version}`);
  }
  if (distribution.version !== pkg.version) {
    fail(`distribution catalog version ${distribution.version} does not match ${pkg.version}`);
  }
  return pkg;
}

function checkTag(version) {
  const index = process.argv.indexOf("--tag");
  const explicit = index >= 0 ? process.argv[index + 1] : undefined;
  const tag = explicit || (process.env.GITHUB_REF_TYPE === "tag" ? process.env.GITHUB_REF_NAME : undefined);
  if (index >= 0 && !explicit) fail("--tag requires a value");
  if (tag && tag !== `v${version}`) fail(`release tag ${tag} does not match package v${version}`);
}

function checkIntegrations() {
  const integrations = readJson("integrations/catalog.json");
  const mcp = readJson("mcp/catalog.json");
  const notices = fs.readFileSync(path.join(ROOT, "THIRD_PARTY_NOTICES.md"), "utf8");

  for (const [name, tool] of Object.entries(integrations.tools)) {
    if (tool.mcpServer && !mcp.servers[tool.mcpServer]) {
      fail(`integration ${name} points to missing MCP server ${tool.mcpServer}`);
    }
    const metadata = tool.mcpServer ? mcp.servers[tool.mcpServer] : tool;
    if (tool.cli) {
      if (metadata.version === "latest") {
        const packageFlag = tool.cli.command === "npx" ? "--package" : "--from";
        const packageIndex = tool.cli.args.indexOf(packageFlag);
        const expectedPackage = tool.cli.command === "npx"
          ? `${metadata.package}@latest`
          : metadata.package;
        const freshnessFlag = tool.cli.command === "npx" ? "--yes" : "--upgrade";
        const resolvesLatest = (
          tool.cli.args.includes(freshnessFlag) &&
          packageIndex >= 0 &&
          tool.cli.args[packageIndex + 1] === expectedPackage
        );
        if (!resolvesLatest) fail(`integration ${name} CLI does not resolve ${metadata.package}@latest`);
      } else {
        const pin = tool.cli.command === "npx"
          ? `${metadata.package}@${metadata.version}`
          : `${metadata.package}==${metadata.version}`;
        if (!tool.cli.args.includes(pin)) fail(`integration ${name} CLI does not pin ${pin}`);
      }
    }
    if (metadata.package && (!notices.includes(metadata.package) || !notices.includes(metadata.version))) {
      fail(`THIRD_PARTY_NOTICES.md is missing ${metadata.package}@${metadata.version}`);
    }
  }
}

function inspectTarball() {
  const npmArgs = ["pack", "--dry-run", "--json", "--ignore-scripts"];
  const command = process.env.npm_execpath ? process.execPath : process.platform === "win32" ? "npm.cmd" : "npm";
  const args = process.env.npm_execpath ? [process.env.npm_execpath, ...npmArgs] : npmArgs;
  const result = spawnSync(command, args, {
    cwd: ROOT,
    encoding: "utf8",
    shell: process.platform === "win32" && !process.env.npm_execpath,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) fail(result.stderr || result.stdout || "npm pack failed");
  const report = JSON.parse(result.stdout)[0];
  const files = new Set(report.files.map((item) => item.path.replaceAll("\\", "/")));
  const required = [
    "LICENSE",
    "CHANGELOG.md",
    "README.md",
    "README.zh-CN.md",
    "package.json",
    "packages/cli/bin/everything-maa.js",
    "integrations/catalog.json",
    "mcp/catalog.json",
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "distribution/catalog.json",
  ];
  for (const skill of fs.readdirSync(path.join(ROOT, "skills"), { withFileTypes: true })) {
    if (!skill.isDirectory()) continue;
    required.push(`skills/${skill.name}/SKILL.md`, `skills/${skill.name}/agents/openai.yaml`);
  }
  for (const file of required) {
    if (!files.has(file)) fail(`npm tarball is missing ${file}`);
  }

  const forbidden = [...files].filter(
    (file) =>
      file.startsWith("tests/") ||
      file.startsWith("evals/") ||
      file.startsWith(".github/") ||
      file.includes("__pycache__") ||
      file.endsWith(".pyc"),
  );
  if (forbidden.length) fail(`npm tarball contains development files: ${forbidden.join(", ")}`);
  return report;
}

const pkg = checkVersions();
checkTag(pkg.version);
checkIntegrations();
const changelog = fs.readFileSync(path.join(ROOT, "CHANGELOG.md"), "utf8");
if (!changelog.includes("## [Unreleased]")) fail("CHANGELOG.md is missing an Unreleased section");
const report = inspectTarball();
console.log(
  `Release contract passed for everything-maa@${pkg.version}: ${report.files.length} files, ${report.size} packed bytes.`,
);
