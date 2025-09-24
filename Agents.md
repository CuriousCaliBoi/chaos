# AGENTS.md — North Star for the Coding Agent

**Purpose:** Make the coding agent a _reliable teammate_ that ships small, verified improvements every day, and scales up to large refactors when the guardrails say it’s safe. Treat this document as the agent’s _operational doctrine_.

---

## Core Principles (non‑negotiable)

1. **Test‑first, patch‑small.** Prefer “add (or tighten) a failing test → make it pass → open a PR” loops. Enforce change budgets per task (e.g., ≤ 200 LOC changed unless `risk=high`).  
2. **Verifiable autonomy.** Every action must be observable: diffs, commands run, test output, and rationale are logged and attached to PRs/artifacts.  
3. **Idempotence.** Agent steps must be safe to retry (e.g., rerun after crash or resume tomorrow).  
4. **Approval modes = risk gates.** Default to **Auto** (write‑in‑workspace + prompts before untrusted actions); use **Read‑only** for planning; **Full access** only in disposable sandboxes. Never on dev laptops or prod hosts.  
5. **MCP everywhere.** Access tools (FS, GitHub, Notion, Web, etc.) via Model Context Protocol so we don’t write bespoke adapters; transports are chosen for latency + trust.  
6. **Reproducibility.** Pin models/flags, record environment, store rollout logs (`~/.codex/sessions/**/rollout-*.jsonl`) as CI artifacts.  
7. **Security & privacy by default.** Least privilege, scoped tokens, no secrets in chat. Dangerous modes are isolated (containers/ephemeral runners) and time‑boxed.

---

## System Sketch

- **Planner (orchestrator):** OpenAI Agents SDK “Conductor”. Owns agenda and decides **what** to do.  
- **Executor (code specialist):** OpenAI **Codex CLI** exposed as an MCP server (`codex mcp`). Owns the **how**: edit, run, test, verify.  
- **Tool belt (MCP servers):** Filesystem, GitHub, Notion, Web, internal APIs — all discovered via `tools/list`, invoked via `tools/call`.  
- **Transports:** `stdio` for local subprocesses; **Streamable HTTP** for remote servers; Hosted MCP to push tool round‑trips into the model when latency matters.  
- **Observability:** Rollout JSONL, TUI logs, Agents SDK traces, Action artifacts, PR comments with checklists.

> Why MCP? It standardizes discovery (`tools/list`), execution (`tools/call`), optional `resources` and `prompts`, over JSON‑RPC with stdio and Streamable HTTP transports. The client negotiates capabilities on `initialize`, then calls tools.


---

## Operating Modes & Risk Gates

| Mode | Typical Use | Guardrails |
|---|---|---|
| **Read‑only** | Design review, code spelunking | No writes. May run safe, deterministic commands. |
| **Auto (default)** | Daily PR valet, bug fixes, API drift | Writes inside workspace. Approvals for untrusted actions. |
| **Full access (“danger”)** | Ephemeral refactors in a sandbox | Only in disposable runners/containers. Short TTL. Extra reviews required. |

**Policy:** The agent must record its mode for every action. CI fails if mode ≠ policy for the task.

---

## Plays (high‑leverage patterns)

### 1) PR Valet (nightly maintenance)
- **Goal:** Keep repos green: dependency bumps, flake quarantine, API drift fixes, changelogs.  
- **Loop:** For each repo → detect candidates → add/adjust failing test → make it pass → open PR → tag owners.  
- **Resume:** Carry state across nights; skip if CI red or policy blocks.

### 2) Monorepo Migrator
- **Goal:** Cross‑tree refactors (TS+Py), codemods, interface shifts.  
- **Guard:** Tool approvals required for destructive ops; budget per package; test shard mapping.

### 3) Repo Q&A + Patch Loop
- **Goal:** Answer questions from code and _offer_ a patch (PR) that proves the answer.  
- **Guard:** Minimum test coverage delta; “no tests, no merge” policy.

### 4) Ephemeral “danger” mode
- **Goal:** Large refactors with full autonomy — _only_ inside a disposable runner.  
- **Guard:** Hard kill‑switch, branch protections, artifacted audit trail, human review.

### 5) Observability by default
- **Goal:** Every run is reproducible.  
- **Guard:** Persist rollout JSONL + TUI logs; surface traces; link PRs to artifacts.

---

## Implementation Templates

### A. Conductor agent (Python, stdio to Codex MCP)

```python
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents.model_settings import ModelSettings

async def main():
    async with MCPServerStdio(
        name="codex-cli",
        params={"command": "codex", "args": ["mcp"]},  # Codex as MCP server
    ) as codex_server:
        agent = Agent(
            name="Conductor",
            instructions=(
                "Plan work. Prefer test-first small patches. "
                "Use Codex MCP to edit/run/tests. Explain rationale. "
                "Respect approval mode policy from AGENTS.md."
            ),
            mcp_servers=[codex_server],
            model_settings=ModelSettings(tool_choice="required"),
        )
        result = await Runner.run(agent, "Add a failing test for slugify() then make it pass, open PR.")
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

**When to switch transports:**  
- Use `MCPServerStdio` for local/dev and private tools.  
- Use `MCPServerStreamableHttp` for remote servers you control.  
- Use **Hosted MCP** when you want the model to call the server directly (cuts an extra round‑trip).

### B. Minimal Codex client config to consume MCP servers

`~/.codex/config.toml`

```toml
# Model & policy defaults
model = "gpt-5-codex"
model_reasoning_effort = "high"
# Safer default than full access
sandbox = "workspace-write"      # read-only | workspace-write | danger-full-access
ask_for_approval = "on-failure"  # never | on-request | on-failure | untrusted

[mcp_servers.files]
command = "npx"
args = ["-y","@modelcontextprotocol/server-filesystem","/path/to/workdir"]
env = { ALLOW_WRITE = "1" }

# Example: GitHub MCP (replace with your managed server)
# [mcp_servers.github]
# sse_url = "https://mcp.example.com/github"
# headers = { Authorization = "Bearer ${GITHUB_TOKEN}" }
```

### C. CI — headless Codex runs with resume + artifacts (GitHub Actions)

```yaml
name: codex-nightly
on:
  schedule: [{ cron: "35 3 * * *" }]
  workflow_dispatch: {}

jobs:
  valet:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Install Codex
        run: |
          npm i -g @openai/codex@latest
          codex --version

      - name: Configure Codex (safer defaults)
        run: |
          mkdir -p ~/.codex
          cat > ~/.codex/config.toml <<'EOF'
          model = "gpt-5-codex"
          model_reasoning_effort = "medium"
          sandbox = "workspace-write"
          ask_for_approval = "on-failure"
          EOF

      - name: Nightly valet task
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          # Headless exec (non-interactive)
          codex exec --full-auto "Update CHANGELOG for next release and open PR."
          # Tip: --full-auto maps to workspace-write + on-failure approvals

      - name: Archive Codex rollout logs
        if: always()
        run: |
          tar -czf codex-rollouts.tgz -C ~/.codex/sessions . || true
        continue-on-error: true

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: codex-rollouts
          path: codex-rollouts.tgz
```

**Resuming:** Prefer `codex resume --last` for interactive recovery. In headless flows, store rollout JSONL as artifacts and resume locally if needed. If your Codex build exposes a session id for `exec`, record it and gate a follow‑up `codex exec resume <id> "…"`. Keep a fallback that picks the latest rollout file by timestamp.

---

## Tooling Choices

- **Transports:**  
  - `stdio` — quickest for local/serverless dev.  
  - **Streamable HTTP** — remote server, multi‑client, optional SSE streaming.  
  - **Hosted MCP** — model calls the server directly inside Responses API for lower latency.

- **Inspector & tracing:** Use MCP Inspector to list tools and simulate `tools/call`; tail `~/.codex/log/codex-tui.log` in interactive sessions; upload rollout JSONL in CI.

---

## Playbooks (checklists)

### A. Failing test → fix → PR
1. “Add failing test” patch (or tighten existing test).  
2. Run tests; capture failure output.  
3. Implement smallest fix; re‑run.  
4. Generate PR with: diff summary, commands run, test output, and rationale.  
5. If green, auto‑label + request review.

### B. Dependency bump
1. Detect outdated deps (lockfile + release notes).  
2. Bump with minimal surface area; run tests.  
3. If flaky tests, quarantine behind tag; open tracking issue.  
4. PR with changelog and breakage notes.

### C. Monorepo interface change
1. Plan codemod; enumerate packages.  
2. Batch by risk/owner; run shard tests.  
3. Open parallel PRs with consistent templates; coordinate merges.

---

## Safety Practices

- Never run **Full access** on persistent machines. Use Docker/K8s runners with short TTLs and no prod creds.  
- Require human review on PRs from agent branches.  
- Redact secrets in logs.  
- Restrict networked tools to allow‑lists where possible.  
- Keep `AGENTS.md` in repo root as the agent’s memory and update it as policies evolve.

---

## Evolving the Agent

- Add richer MCP servers (DB schema, feature flags, build artifacts).  
- Bake domain‑specific prompts as MCP `prompts/…` resources so they’re discoverable.  
- Log quality signals: flaky test hit rate, PR acceptance rate, revert rate.  
- Graduated autonomy: raise budgets only after green streaks.  
- Maintain a backlog of stubborn failures and create new tools (via MCP) to unblock them.

---

## References & Notes

- MCP concepts (tools, resources, prompts), transports (stdio & Streamable HTTP), and lifecycle are defined in the official spec and docs.  
- Hosted MCP and Agents SDK support both Python and JS; choose Hosted MCP to eliminate an orchestrator hop when the model can call the remote server directly.  
- Codex CLI supports MCP servers through `~/.codex/config.toml`, has approval/sandbox modes, TUI logs under `~/.codex/log/codex-tui.log`, and stores rollout JSONL under `~/.codex/sessions/**/rollout-*.jsonl`. `codex resume` restores interactive sessions.

**Selected sources** (skim as needed):
- Model Context Protocol — Tools / Resources / Prompts / Transports / Lifecycle. citeturn2search1turn0search14turn1search1turn2search11  
- Official transport guidance: stdio + Streamable HTTP (SSE optional / legacy SSE deprecated). citeturn1search0turn1search1turn1search4  
- Agents SDK + Hosted MCP (Python & JS). citeturn3search0turn3search2  
- MCP Inspector and server‑filesystem. citeturn0search1turn0search10  
- Codex CLI docs & repo (MCP support, resume, logs). citeturn6search14turn8view0turn7search3

---

_This file is living documentation. Update it when policies or tools change. Keep it short enough that the agent (and humans) actually read it._
