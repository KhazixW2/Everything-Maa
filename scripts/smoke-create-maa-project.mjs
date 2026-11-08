import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const BASE_ARGS = ["--upgrade", "--from", "create-maa-project", "create-maa-project"];
const ENVIRONMENT = {
  ...process.env,
};

function runReport(args, cwd, allowedStatuses = [0]) {
  const result = spawnSync("uvx", [...BASE_ARGS, ...args], {
    cwd,
    encoding: "utf8",
    env: ENVIRONMENT,
  });
  if (result.error) throw result.error;
  if (!allowedStatuses.includes(result.status)) {
    throw new Error(`Command failed (${result.status}): ${result.stderr || result.stdout}`);
  }
  try {
    return JSON.parse(result.stdout);
  } catch (error) {
    throw new Error(`Expected a JSON report, received: ${result.stdout || result.stderr}`, {
      cause: error,
    });
  }
}

function listMcpTools(cwd) {
  return new Promise((resolve, reject) => {
    const child = spawn("uvx", [...BASE_ARGS, "--mcp"], {
      cwd,
      env: ENVIRONMENT,
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    let settled = false;

    const finish = (error, tools) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      child.once("close", () => {
        if (error) reject(error);
        else resolve(tools);
      });
      child.stdin.end();
      child.kill();
    };
    const timer = setTimeout(
      () => finish(new Error(`MCP handshake timed out. ${stderr}`)),
      20_000,
    );

    child.on("error", (error) => finish(error));
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
      let newline;
      while ((newline = stdout.indexOf("\n")) >= 0) {
        const line = stdout.slice(0, newline).trim();
        stdout = stdout.slice(newline + 1);
        if (!line) continue;
        let message;
        try {
          message = JSON.parse(line);
        } catch {
          continue;
        }
        if (message.id === 1) {
          child.stdin.write(
            `${JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized", params: {} })}\n`,
          );
          child.stdin.write(
            `${JSON.stringify({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} })}\n`,
          );
        }
        if (message.id === 2) finish(null, message.result.tools);
      }
    });

    child.stdin.write(
      `${JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "initialize",
        params: {
          protocolVersion: "2025-03-26",
          capabilities: {},
          clientInfo: { name: "everything-maa-smoke", version: "0.1.0" },
        },
      })}\n`,
    );
  });
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

const parent = fs.mkdtempSync(path.join(os.tmpdir(), "everything-maa-create-smoke-"));
const target = path.join(parent, "sample-project");

try {
  const create = runReport(
    [
      target,
      "--template",
      "pipeline",
      "--controller",
      "Adb",
      "--license",
      "MIT",
      "--add",
      "dev-tools",
      "--add",
      "github",
      "--no-git",
      "--skip-download",
      "--no-interactive",
      "--yes",
      "--report",
    ],
    parent,
  );
  if (!create.ok || create.command !== "create") {
    throw new Error(`Unexpected create report: ${JSON.stringify(create)}`);
  }
  for (const relative of ["interface.json", "maa-project.json", "package.json"]) {
    if (!fs.existsSync(path.join(target, relative))) {
      throw new Error(`Created project is missing ${relative}`);
    }
  }

  const doctor = runReport(["--doctor", "--report"], target, [0, 1]);
  if (doctor.command !== "doctor" || !doctor.doctor) {
    throw new Error(`Unexpected doctor report: ${JSON.stringify(doctor)}`);
  }

  const tools = await listMcpTools(parent);
  const names = new Set(tools.map((tool) => tool.name));
  for (const required of [
    "get_project_context",
    "create_project",
    "doctor",
    "sync",
    "update",
    "add",
    "list_backups",
  ]) {
    if (!names.has(required)) throw new Error(`MCP server is missing tool ${required}`);
  }

  console.log(
    `create-maa-project smoke passed: ${create.written.length} files, ${create.pending.length} pending actions, ${tools.length} MCP tools.`,
  );
} finally {
  safeRemoveTemp(parent);
}
