#!/usr/bin/env node

import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const CLI_DIR = path.dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = path.resolve(CLI_DIR, "../../..");
const MANAGED_BEGIN = "# BEGIN EVERYTHING-MAA MCP";
const MANAGED_END = "# END EVERYTHING-MAA MCP";
const STATE_VERSION = 1;

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function stableJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

function sameJson(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function parseArgs(argv) {
  const [command = "help", ...rest] = argv;
  const options = {
    command: command === "init" ? "install" : command,
    target: undefined,
    scope: "project",
    profile: "core",
    projectDir: process.cwd(),
    dryRun: false,
    force: false,
  };

  for (let index = 0; index < rest.length; index += 1) {
    const raw = rest[index];
    if (raw === "--dry-run") {
      options.dryRun = true;
      continue;
    }
    if (raw === "--force") {
      options.force = true;
      continue;
    }
    const [flag, inlineValue] = raw.split("=", 2);
    if (!["--target", "--scope", "--profile", "--project-dir"].includes(flag)) {
      throw new Error(`Unknown option: ${raw}`);
    }
    const value = inlineValue ?? rest[++index];
    if (!value || value.startsWith("--")) {
      throw new Error(`Missing value for ${flag}`);
    }
    if (flag === "--target") options.target = value;
    if (flag === "--scope") options.scope = value;
    if (flag === "--profile") options.profile = value;
    if (flag === "--project-dir") options.projectDir = path.resolve(value);
  }
  return options;
}

function validateOptions(options, catalog) {
  if (!["install", "uninstall"].includes(options.command)) return;
  if (!options.target || !["claude", "codex"].includes(options.target)) {
    throw new Error("Install and uninstall require --target claude|codex.");
  }
  if (!["project", "user"].includes(options.scope)) {
    throw new Error("--scope must be project or user.");
  }
  if (!(options.profile in catalog.profiles)) {
    throw new Error(`Unknown profile: ${options.profile}`);
  }
  if (
    options.command === "install" &&
    options.target === "claude" &&
    options.scope === "user" &&
    options.profile !== "skills-only"
  ) {
    throw new Error(
      "Claude user-scope MCP merging is intentionally unsupported; use --profile skills-only, project scope, or the native plugin.",
    );
  }
}

function targetPaths(options) {
  const root = options.scope === "project" ? options.projectDir : os.homedir();
  if (options.target === "claude") {
    const host = path.join(root, ".claude");
    return {
      root,
      skillRoot: path.join(host, "skills"),
      stateFile: path.join(host, ".everything-maa.json"),
      mcpFile: options.scope === "project" ? path.join(root, ".mcp.json") : null,
      codexConfig: null,
    };
  }

  const codexHome =
    options.scope === "user"
      ? path.resolve(process.env.CODEX_HOME || path.join(root, ".codex"))
      : path.join(root, ".codex");
  return {
    root,
    skillRoot:
      options.scope === "project"
        ? path.join(root, ".agents", "skills")
        : path.join(codexHome, "skills"),
    stateFile: path.join(codexHome, ".everything-maa.json"),
    mcpFile: null,
    codexConfig: path.join(codexHome, "config.toml"),
  };
}

function listFiles(root) {
  const files = [];
  if (!fs.existsSync(root)) return files;
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) {
      files.push(...listFiles(full));
    } else if (entry.isFile()) {
      files.push(full);
    }
  }
  return files.sort((a, b) => a.localeCompare(b));
}

function hashDirectory(root) {
  const hash = createHash("sha256");
  for (const file of listFiles(root)) {
    hash.update(path.relative(root, file).split(path.sep).join("/"));
    hash.update("\0");
    hash.update(fs.readFileSync(file));
    hash.update("\0");
  }
  return hash.digest("hex");
}

function loadState(file) {
  if (!fs.existsSync(file)) return null;
  const state = readJson(file);
  if (state.schemaVersion !== STATE_VERSION) {
    throw new Error(`Unsupported Everything Maa state version in ${file}`);
  }
  return state;
}

function writeFile(file, content, dryRun) {
  if (dryRun) return;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content, "utf8");
}

function removeFileIfEmptyParent(file, dryRun) {
  if (dryRun || !fs.existsSync(file)) return;
  fs.rmSync(file);
}

function selectedServers(profile, catalog) {
  return Object.fromEntries(
    catalog.profiles[profile].map((name) => {
      const server = catalog.servers[name];
      const expected = { command: server.command, args: server.args };
      if (server.env) expected.env = server.env;
      return [name, expected];
    }),
  );
}

function installSkills(paths, previousState, options) {
  const sourceRoot = path.join(PACKAGE_ROOT, "skills");
  const entries = fs
    .readdirSync(sourceRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort()
    .map((name) => {
      const source = path.join(sourceRoot, name);
      return {
        name,
        source,
        destination: path.join(paths.skillRoot, name),
        sourceHash: hashDirectory(source),
      };
    });
  const installed = {};

  for (const { name, destination } of entries) {
    if (fs.existsSync(destination)) {
      const currentHash = hashDirectory(destination);
      const recorded = previousState?.skills?.[name];
      const safeToReplace = recorded && recorded.path === destination && recorded.hash === currentHash;
      if (!safeToReplace && !options.force) {
        throw new Error(
          `Refusing to overwrite unmanaged or modified skill ${destination}; pass --force to replace it.`,
        );
      }
    }
  }

  for (const { name, source, destination, sourceHash } of entries) {
    console.log(`${options.dryRun ? "Would install" : "Installing"} skill ${name}`);
    if (!options.dryRun) {
      fs.rmSync(destination, { recursive: true, force: true });
      fs.mkdirSync(path.dirname(destination), { recursive: true });
      fs.cpSync(source, destination, { recursive: true });
    }
    installed[name] = { path: destination, hash: sourceHash };
  }
  return installed;
}

function planClaudeMcp(paths, servers, previousState, options) {
  if (!paths.mcpFile) return null;
  const existed = fs.existsSync(paths.mcpFile);
  const document = existed ? readJson(paths.mcpFile) : {};
  if (document.mcpServers !== undefined && typeof document.mcpServers !== "object") {
    throw new Error(`${paths.mcpFile} has a non-object mcpServers field.`);
  }
  document.mcpServers ||= {};
  const oldServers = previousState?.mcp?.servers || {};

  for (const [name, expected] of Object.entries(oldServers)) {
    if (name in servers) continue;
    if (sameJson(document.mcpServers[name], expected)) {
      delete document.mcpServers[name];
    } else if (document.mcpServers[name] !== undefined) {
      throw new Error(`Refusing to replace modified MCP server ${name} in ${paths.mcpFile}.`);
    }
  }
  for (const [name, expected] of Object.entries(servers)) {
    const current = document.mcpServers[name];
    const previouslyManaged = sameJson(current, oldServers[name]);
    if (current !== undefined && !sameJson(current, expected) && !previouslyManaged && !options.force) {
      throw new Error(`MCP server ${name} already exists in ${paths.mcpFile}; pass --force to replace it.`);
    }
    document.mcpServers[name] = expected;
  }

  return { document, existed };
}

function mergeClaudeMcp(paths, servers, previousState, options) {
  const plan = planClaudeMcp(paths, servers, previousState, options);
  if (!plan) return null;

  console.log(`${options.dryRun ? "Would update" : "Updating"} ${paths.mcpFile}`);
  writeFile(paths.mcpFile, stableJson(plan.document), options.dryRun);
  return { type: "claude-json", path: paths.mcpFile, servers, created: !plan.existed };
}

function tomlString(value) {
  return JSON.stringify(value);
}

function tomlEnvEntries(env) {
  return Object.entries(env).map(
    ([key, value]) => `${tomlString(key)} = ${tomlString(value)}`,
  );
}

function renderCodexBlock(servers) {
  const chunks = [MANAGED_BEGIN];
  for (const [name, server] of Object.entries(servers)) {
    chunks.push(
      `[mcp_servers.${name}]`,
      `command = ${tomlString(server.command)}`,
      `args = [${server.args.map(tomlString).join(", ")}]`,
      ...(server.env
        ? [`env = { ${tomlEnvEntries(server.env).join(", ")} }`]
        : []),
      "",
    );
  }
  if (chunks.at(-1) === "") chunks.pop();
  chunks.push(MANAGED_END);
  return chunks.join("\n");
}

function findManagedBlock(content) {
  const start = content.indexOf(MANAGED_BEGIN);
  const endStart = content.indexOf(MANAGED_END);
  if ((start === -1) !== (endStart === -1)) {
    throw new Error("Codex config contains an incomplete Everything Maa managed block.");
  }
  if (start === -1) return null;
  if (content.indexOf(MANAGED_BEGIN, start + 1) !== -1 || content.indexOf(MANAGED_END, endStart + 1) !== -1) {
    throw new Error("Codex config contains multiple Everything Maa managed blocks.");
  }
  const end = endStart + MANAGED_END.length;
  return { start, end, text: content.slice(start, end) };
}

function withoutManagedBlock(content, block) {
  if (!block) return content.trimEnd();
  return `${content.slice(0, block.start)}${content.slice(block.end)}`.trimEnd();
}

function planCodexMcp(paths, servers, previousState, options) {
  const content = fs.existsSync(paths.codexConfig) ? fs.readFileSync(paths.codexConfig, "utf8") : "";
  const block = findManagedBlock(content);
  if (block && previousState?.mcp?.block && block.text !== previousState.mcp.block && !options.force) {
    throw new Error(`Everything Maa MCP block in ${paths.codexConfig} was modified; pass --force to replace it.`);
  }
  const unmanaged = withoutManagedBlock(content, block);
  for (const name of Object.keys(servers)) {
    const section = `[mcp_servers.${name}]`;
    if (unmanaged.includes(section)) {
      throw new Error(`Unmanaged ${section} already exists in ${paths.codexConfig}.`);
    }
  }

  const nextBlock = Object.keys(servers).length ? renderCodexBlock(servers) : "";
  const next = [unmanaged, nextBlock].filter(Boolean).join("\n\n");
  return { next, nextBlock };
}

function mergeCodexMcp(paths, servers, previousState, options) {
  const plan = planCodexMcp(paths, servers, previousState, options);
  console.log(`${options.dryRun ? "Would update" : "Updating"} ${paths.codexConfig}`);
  if (plan.next) {
    writeFile(paths.codexConfig, `${plan.next}\n`, options.dryRun);
  } else {
    removeFileIfEmptyParent(paths.codexConfig, options.dryRun);
  }
  return plan.nextBlock
    ? { type: "codex-toml", path: paths.codexConfig, servers, block: plan.nextBlock }
    : null;
}

function install(options, catalog) {
  const paths = targetPaths(options);
  const previousState = loadState(paths.stateFile);
  if (
    previousState &&
    (previousState.target !== options.target || previousState.scope !== options.scope)
  ) {
    throw new Error(`State file ${paths.stateFile} belongs to a different target or scope.`);
  }
  const servers = selectedServers(options.profile, catalog);
  if (options.target === "claude") planClaudeMcp(paths, servers, previousState, options);
  else planCodexMcp(paths, servers, previousState, options);
  const skills = installSkills(paths, previousState, options);
  const mcp =
    options.target === "claude"
      ? mergeClaudeMcp(paths, servers, previousState, options)
      : mergeCodexMcp(paths, servers, previousState, options);
  const state = {
    schemaVersion: STATE_VERSION,
    packageVersion: readJson(path.join(PACKAGE_ROOT, "package.json")).version,
    target: options.target,
    scope: options.scope,
    profile: options.profile,
    skills,
    mcp,
  };
  console.log(`${options.dryRun ? "Would write" : "Writing"} state ${paths.stateFile}`);
  writeFile(paths.stateFile, stableJson(state), options.dryRun);
  console.log(options.dryRun ? "Dry run complete; no files were changed." : "Everything Maa installation complete.");
}

function uninstallClaudeMcp(state, options, retained) {
  const mcp = state.mcp;
  if (!mcp || !fs.existsSync(mcp.path)) return;
  const document = readJson(mcp.path);
  document.mcpServers ||= {};
  const keptServers = {};
  for (const [name, expected] of Object.entries(mcp.servers)) {
    if (sameJson(document.mcpServers[name], expected)) {
      delete document.mcpServers[name];
      console.log(`${options.dryRun ? "Would remove" : "Removing"} MCP server ${name}`);
    } else if (document.mcpServers[name] !== undefined) {
      keptServers[name] = expected;
      retained.push(`modified MCP server ${name}`);
    }
  }
  if (Object.keys(keptServers).length) {
    state.mcp.servers = keptServers;
  } else {
    state.mcp = null;
  }
  const canRemoveCreatedFile =
    mcp.created === true &&
    Object.keys(document).every((key) => key === "mcpServers") &&
    Object.keys(document.mcpServers).length === 0;
  if (canRemoveCreatedFile) removeFileIfEmptyParent(mcp.path, options.dryRun);
  else writeFile(mcp.path, stableJson(document), options.dryRun);
}

function uninstallCodexMcp(state, options, retained) {
  const mcp = state.mcp;
  if (!mcp || !fs.existsSync(mcp.path)) return;
  const content = fs.readFileSync(mcp.path, "utf8");
  const block = findManagedBlock(content);
  if (!block) {
    state.mcp = null;
    return;
  }
  if (block.text !== mcp.block) {
    retained.push("modified Codex MCP block");
    return;
  }
  const next = withoutManagedBlock(content, block);
  console.log(`${options.dryRun ? "Would remove" : "Removing"} Everything Maa MCP block`);
  if (next) writeFile(mcp.path, `${next}\n`, options.dryRun);
  else removeFileIfEmptyParent(mcp.path, options.dryRun);
  state.mcp = null;
}

function uninstall(options) {
  const paths = targetPaths(options);
  const state = loadState(paths.stateFile);
  if (!state) {
    console.log("Nothing to uninstall: no Everything Maa state file was found.");
    return;
  }
  if (state.target !== options.target || state.scope !== options.scope) {
    throw new Error(`State file ${paths.stateFile} belongs to a different target or scope.`);
  }
  const retained = [];
  for (const [name, record] of Object.entries(state.skills || {})) {
    const expectedPath = path.join(paths.skillRoot, name);
    if (path.resolve(record.path) !== path.resolve(expectedPath)) {
      throw new Error(`Refusing unsafe skill path in ${paths.stateFile}: ${record.path}`);
    }
    if (!fs.existsSync(record.path)) {
      delete state.skills[name];
      continue;
    }
    if (hashDirectory(record.path) !== record.hash) {
      retained.push(`modified skill ${name}`);
      continue;
    }
    console.log(`${options.dryRun ? "Would remove" : "Removing"} skill ${name}`);
    if (!options.dryRun) fs.rmSync(record.path, { recursive: true });
    delete state.skills[name];
  }
  if (state.mcp?.type === "claude-json") uninstallClaudeMcp(state, options, retained);
  if (state.mcp?.type === "codex-toml") uninstallCodexMcp(state, options, retained);

  if (options.dryRun) {
    console.log("Dry run complete; no files were changed.");
    return;
  }
  if (retained.length) {
    writeFile(paths.stateFile, stableJson(state), false);
    console.log(`Preserved ${retained.join(", ")}; state was kept for a later uninstall.`);
  } else {
    fs.rmSync(paths.stateFile, { force: true });
    console.log("Everything Maa uninstall complete.");
  }
}

function list(catalog) {
  const skillRoot = path.join(PACKAGE_ROOT, "skills");
  console.log("Skills:");
  for (const name of fs.readdirSync(skillRoot).sort()) console.log(`  - ${name}`);
  console.log("Profiles:");
  for (const [name, servers] of Object.entries(catalog.profiles)) {
    console.log(`  - ${name}: ${servers.length ? servers.join(", ") : "skills only"}`);
  }
}

function checkCommand(label, command) {
  const result =
    process.platform === "win32" && command.toLowerCase().endsWith(".cmd")
      ? spawnSync(process.env.ComSpec || "C:\\Windows\\System32\\cmd.exe", [
          "/d",
          "/s",
          "/c",
          `${command} --version`,
        ], { encoding: "utf8" })
      : spawnSync(command, ["--version"], { encoding: "utf8", shell: false });
  if (result.error || result.status !== 0) {
    console.log(`  [missing] ${label} (${command})`);
    return false;
  }
  const version = (result.stdout || result.stderr).trim().split(/\r?\n/, 1)[0];
  console.log(`  [ok] ${label}: ${version}`);
  return true;
}

function doctor(catalog, integrations) {
  console.log(`Everything Maa ${readJson(path.join(PACKAGE_ROOT, "package.json")).version}`);
  const checks = [
    checkCommand("Node.js", process.execPath),
    checkCommand("Python", process.platform === "win32" ? "python" : "python3"),
    checkCommand("uvx (required by Maa MCP integrations)", "uvx"),
    checkCommand(
      "npx (required by Playwright MCP and MaaEvidenceKit)",
      process.platform === "win32" ? "npx.cmd" : "npx",
    ),
  ];
  console.log("Configured integrations:");
  for (const [name, tool] of Object.entries(integrations.tools)) {
    if (tool.mcpServer) {
      const server = catalog.servers[tool.mcpServer];
      console.log(`  [mcp] ${name}: ${server.package}@${server.version}`);
    } else if (tool.cli) {
      console.log(
        `  [optional cli] ${name}: ${tool.package}@${tool.version} (${tool.status || "stable"}, ${tool.install || "on-demand"})`,
      );
    } else if (tool.package) {
      console.log(
        `  [external runtime] ${name}: ${tool.package}@${tool.version} (${tool.status || "stable"}, ${tool.install || "user-managed"})`,
      );
    }
  }
  if (!checks.every(Boolean)) process.exitCode = 1;
}

function help() {
  console.log(`Everything Maa

Usage:
  everything-maa list
  everything-maa doctor
  everything-maa install --target claude|codex [options]
  everything-maa uninstall --target claude|codex [options]

Options:
  --scope project|user          Installation scope (default: project)
  --profile skills-only|core|authoring|full
                                authoring adds create-maa-project; full also adds Playwright MCP
  --project-dir <path>          Project root (default: current directory)
  --dry-run                     Preview changes without writing files
  --force                       Replace conflicting managed destinations

The init command is an alias for install.`);
}

function main() {
  const catalog = readJson(path.join(PACKAGE_ROOT, "mcp", "catalog.json"));
  const integrations = readJson(path.join(PACKAGE_ROOT, "integrations", "catalog.json"));
  const options = parseArgs(process.argv.slice(2));
  validateOptions(options, catalog);
  if (["help", "--help", "-h"].includes(options.command)) return help();
  if (options.command === "list") return list(catalog);
  if (options.command === "doctor") return doctor(catalog, integrations);
  if (options.command === "install") return install(options, catalog);
  if (options.command === "uninstall") return uninstall(options);
  throw new Error(`Unknown command: ${options.command}`);
}

try {
  main();
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exitCode = 1;
}
