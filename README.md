# Dev Team: a multi-agent development team for Claude Code

A Claude Code plugin that turns one session into a coordinated software
team. The main session becomes the **orchestrator**: it decomposes the work,
dispatches scoped **specialist subagents**, fans out in parallel through
**workflows**, and tracks every task in a `TASKS.md` ledger maintained by a
script rather than by a model.

Version 2 is a rebuild for the Claude 5 generation of models. The agents are
fewer and more capable, review and planning fan out and verify themselves,
and you choose how many tokens the team spends.

## What the team does

Each mode of work fails differently, so each gets its own agent with its own
context, tools, and definition of done:

- **Planning is separate from coding.** Most agent failures are planning failures, so the plan is written first, by an agent that reads the real code and writes no code.
- **Review is never self-review.** The reviewer is always a different dispatch from the implementer, and on fan-out each finding is independently refuted before you see it.
- **Tests report ground truth.** A real test run beats any agent's reasoning about whether code works, and the tester never fixes the code under test.
- **Debugging is its own mode.** Reproduce, hypothesize, instrument, observe, repeat; fix the cause, never the symptom.

## The team

| Agent | Role | Default model and effort |
|-------|------|--------------------------|
| *(main session)* | **Orchestrator**: sizes the work, plans, dispatches, judges, reports | your session's model |
| `planner` | Reads the real code and writes a plan precise enough to build from, with parallel-safe slices | inherit, xhigh |
| `implementer` | Builds one slice of the plan in the codebase's style, runs lint, typecheck and build | inherit, high |
| `reviewer` | Reviews a diff it did not write through one lens, or refutes another reviewer's finding | inherit, xhigh |
| `tester` | Writes and runs tests, reports GREEN or RED with the real output | inherit, high |
| `debugger` | Chases failures to a confirmed root cause and makes the smallest fix | inherit, xhigh |
| `explorer` | Cheap read-only scout the other agents dispatch for "where is X, who calls Y" | sonnet, medium |

`inherit` means the agent runs on whatever model your session runs on. The
profile setting below overrides these per role without editing files.

## Install

The repo is both a plugin and its own marketplace:

```
/plugin marketplace add TheTylerCampbell/dev-team
/plugin install dev-team@dev-team
```

Or from a local clone:

```
/plugin marketplace add /absolute/path/to/dev-team
/plugin install dev-team@dev-team
```

Restart Claude Code after installing. For the parallel review and planning
panels, turn on **Dynamic workflows** in `/config`; without it the orchestrator
falls back to dispatching the reviewers itself.

## Use

Start the team by describing the work or by invoking the skill:

- `/dev-team add team invitations with email and a pending state`
- "Use the dev team to fix the empty export bug."
- "Run the team on the settings page redesign."

The orchestrator sizes the request (trivial, small, standard, large, or bug)
and runs only the steps that earn their cost:

1. **Intake**: logs one task per deliverable in `TASKS.md`.
2. **Plan**: the planner writes `docs/plans/<T-id>-<slug>.md`; open questions come to you before any code. On the quality profile, a panel of planners drafts from different lenses, judges score them, and one planner synthesizes the winner.
3. **Build**: one implementer per slice; parallel-safe slices run concurrently up to the team size.
4. **Review**: the `dev-team:review` workflow runs one reviewer per lens (correctness, plan drift, security, error handling, tests, simplicity), deduplicates findings in code, and has independent reviewers refute each one. Blocking findings go back to the implementer; the loop is capped at two rounds.
5. **Test**: the tester writes and runs tests and reports the real result.
6. **Debug**: on RED, the debugger finds the cause and the tester confirms the fix; capped at three rounds.
7. **Done**: the ledger records the outcome and you get a short report.

Other commands:

- `/dev-team status`: what is active, blocked, and recently logged.
- `/dev-team resume T-003`: pick a task up from where it stopped.
- `/dev-team config profile=quality fanout=large`: change the settings for this project.

## Choosing how many tokens the team spends

Two settings control cost and width. Set them any of three ways, highest
precedence first:

1. Per project, in `.claude/dev-team.local.md` (written by `/dev-team config ...`):
   ```markdown
   ---
   profile: economy
   fanout: small
   tracker: true
   ---
   ```
2. Per machine, with `claude plugin configure dev-team@dev-team`.
3. Defaults: `balanced`, `standard`, tracker on.

A SessionStart hook announces the resolved values to every session so the
orchestrator dispatches accordingly.

**Profile** sets model, effort and verification depth per role:

| Role | economy | balanced | quality |
|------|---------|----------|---------|
| planner | effort high | inherit, xhigh | effort max, planning panel |
| implementer | Sonnet, effort medium | inherit, high | effort xhigh |
| reviewer | Sonnet, effort high, 1 refuter vote | inherit, xhigh, 2 votes | 3 votes |
| tester | Sonnet, effort medium | inherit, high | same |
| debugger | effort high | inherit, xhigh | effort max |
| explorer | Sonnet, low | Sonnet, medium | same |

**Fanout** sets how wide the team goes:

| fanout | parallel implementers | review lenses |
|--------|-----------------------|---------------|
| small | 2 | 2 |
| standard | 4 | 4 |
| large | 8 | 6 |

Workflows are additionally capped by the **Dynamic workflow size** setting in
`/config` and by `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` (default 16).
Raise those to let a large fanout actually run that wide.

## TASKS.md

The ledger lives at your project root. Its tables are rendered from a JSON
block at the bottom of the file by `scripts/tasks.py`, so the orchestrator
updates it with a command, not a model call, at every state change:

```
python3 "$PLUGIN/scripts/tasks.py" add "Add login flow" --status planning
python3 "$PLUGIN/scripts/tasks.py" set T-001 --status ready --plan docs/plans/T-001-login.md
python3 "$PLUGIN/scripts/tasks.py" log T-001 "review: 1 blocking finding, routed back"
python3 "$PLUGIN/scripts/tasks.py" set T-001 --status done --outcome "shipped, 14 tests green"
python3 "$PLUGIN/scripts/tasks.py" show
```

Statuses flow `todo → planning → ready → in-progress → review → testing → done`,
with `blocked` when waiting on you. IDs are stable and never reused; the log is
append-only. Set `tracker: false` to skip the ledger for throwaway work.

## Works best with a project CLAUDE.md

Every agent reads your project's `CLAUDE.md` for stack, conventions, and the
commands for lint, typecheck, build and tests. A short one makes the whole
team noticeably sharper, and it is where the implementer learns which design
skill to use for UI work.

## Customizing

- **Models and effort**: edit `model:` and `effort:` in any `agents/*.md`. Values: `inherit`, `sonnet`, `opus`, `haiku`, `fable`, or a full model ID; effort `low` to `max`.
- **Tools**: edit `tools:` to widen or restrict an agent. Agents may dispatch each other only where `Agent(dev-team:<name>)` is listed.
- **Lenses, votes and panel size**: edit the `PROFILES`, `FANOUT` and `LENSES` tables at the top of `workflows/review.js` and `workflows/plan.js`.
- **Flow and briefs**: the orchestrator playbook is `skills/dev-team/SKILL.md`; the brief templates are `skills/dev-team/references/briefs.md`.

## Layout

```
dev-team/
├── .claude-plugin/
│   ├── plugin.json            manifest, with the profile / fanout / tracker settings
│   └── marketplace.json       lets this repo install as its own marketplace
├── agents/                    planner, implementer, reviewer, tester, debugger, explorer
├── skills/dev-team/
│   ├── SKILL.md               the orchestrator playbook
│   └── references/briefs.md   brief templates per role
├── workflows/
│   ├── review.js              lenses → dedup → adversarial refutation
│   └── plan.js                planner panel → judges → synthesis
├── hooks/
│   ├── hooks.json             SessionStart: announce settings
│   └── session-start.sh
├── scripts/tasks.py           the TASKS.md ledger
└── evals/                     starter eval cases for `claude plugin eval`
```

## Migrating from 1.x

- `frontend-implementer` and `backend-implementer` are one `implementer`; the plan's slices decide the split, and UI work still uses a project design skill when one is installed.
- `project-manager` is gone; `scripts/tasks.py` maintains `TASKS.md` deterministically. An existing 1.x `TASKS.md` is not in the new format: move it aside and let the orchestrator run `tasks.py init`.
- Models default to `inherit` with per-role effort instead of fixed opus/sonnet/haiku; use the profile setting to trade quality for tokens.

## License

MIT, see [LICENSE](LICENSE).
