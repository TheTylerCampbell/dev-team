# Dev Team — a multi-agent development team for Claude Code

A portable Claude Code plugin that turns one session into a coordinated software
development team. An **orchestrator** skill makes the main session act as the lead/router; it
dispatches **scoped specialist subagents** and tracks every task in a central `TASKS.md`.

The design follows one core idea: **separate the modes of work**. Planning, implementing,
reviewing, testing, and debugging are different jobs that fail in different ways — so each gets
its own agent with its own context, tools, and success criteria. The most important splits:

- **Planning is separate from coding** — most agent failures are planning failures, not syntax
  failures. A cheap-but-wrong plan executed flawlessly is still wrong.
- **Review is always a separate agent from the implementer** — self-review by the same context
  is weak.
- **Testing reports ground truth** — a real test run beats any agent's reasoning about whether
  code works.

## The team

| Agent | Role | Model |
|-------|------|-------|
| *(main session)* | **Orchestrator** — decomposes work, routes to specialists, sequences | — |
| `planner` | **Planner/Architect** — produces a technical plan before any code | opus |
| `frontend-implementer` | **Frontend coder** — UI; uses the `ui-ux-pro-max` skill if installed | sonnet |
| `backend-implementer` | **Backend/Data coder** — APIs, business logic, schema, migrations | sonnet |
| `reviewer` | **Critic** — reviews the diff vs. the plan and conventions (never self-review) | opus |
| `tester` | **QA** — writes and runs tests, reports real pass/fail | sonnet |
| `debugger` | **Fixer** — hypothesis → instrument → observe → fix loop | sonnet |
| `project-manager` | **PM** — the sole owner/writer of `TASKS.md` | haiku |

Models are sensible defaults — override them in each agent's frontmatter to fit your plan.

## Install

This repo is both a plugin and its own marketplace, so installation is two commands inside
Claude Code:

```
/plugin marketplace add <your-github-username>/dev-team
/plugin install dev-team@dev-team
```

- The first command registers this repo as a plugin marketplace.
- The second installs the `dev-team` plugin from it.

You can also point the marketplace at a local clone:

```
/plugin marketplace add /absolute/path/to/dev-team
/plugin install dev-team@dev-team
```

Restart Claude Code (or reload plugins) after installing. The agents then appear to the
`Agent`/Task tool, and the orchestrator skill becomes available.

### Recommended companion

The `frontend-implementer` uses the **[`ui-ux-pro-max`](https://uupm.cc)** skill as its design
authority when present. Install it separately for the best UI results; without it, the frontend
agent falls back to its own defaults.

## Use

**Start the team** by either:

- invoking the skill: `/dev-team`, or
- just describing the work: *"Use the dev team to build the login flow"* or *"Run the team on
  this bug."*

The orchestrator then:

1. has the **project-manager** log the request as task(s) in `TASKS.md` (created if missing),
2. has the **planner** produce a technical plan,
3. dispatches the **implementer(s)** to build against the plan (in parallel where independent),
4. dispatches the **reviewer** on the diff — always a fresh agent, never the implementer,
5. has the **tester** write and run tests,
6. sends failures to the **debugger** until green,
7. has the PM mark the task done.

You stay in the loop the whole time — the orchestrator confirms its decomposition before
fanning out on large work, and you can intervene at any step.

### `TASKS.md`

The project-manager maintains a `TASKS.md` at your project root: a task table (ID, title, owner
agent, status) plus an append-only activity log. It is the shared source of truth for what's in
flight, and the **only** file the PM writes. Status flows
`todo → planning → in-progress → review → testing → done` (with `blocked` when waiting).

### Works best with a project `CLAUDE.md`

Every agent reads your project's `CLAUDE.md` (if present) for stack, conventions, and commands,
then stays in its lane. A short `CLAUDE.md` describing your stack and how to run lint/tests makes
the whole team noticeably sharper.

## Customizing

- **Models:** edit the `model:` field in any `agents/*.md` (`opus` / `sonnet` / `haiku`).
- **Tools:** edit the `tools:` field to widen or restrict an agent's permissions.
- **Behavior:** the agent bodies are plain markdown system prompts — tune them to your team's
  standards. The orchestrator playbook lives in `skills/dev-team/SKILL.md`.

## Layout

```
dev-team/
├── .claude-plugin/
│   ├── plugin.json        # plugin manifest
│   └── marketplace.json   # lets this repo install as its own marketplace
├── agents/                # the 7 specialist subagents
│   ├── planner.md
│   ├── frontend-implementer.md
│   ├── backend-implementer.md
│   ├── reviewer.md
│   ├── tester.md
│   ├── debugger.md
│   └── project-manager.md
└── skills/
    └── dev-team/
        └── SKILL.md       # the orchestrator playbook
```

## License

MIT — see [LICENSE](LICENSE).
