# Brief templates

Every dispatch is an Agent call whose prompt is one of these briefs, filled in.
Keep each brief to what the role needs. Replace every `<...>`; delete lines that
do not apply. Prepend the model and effort from the profile table as Agent
parameters, not as prose.

## Explorer (`dev-team:explorer`)

```
Question: <one specific question about the codebase>
Why: <one line on what the answer will be used for>
Start from: <paths or symbols if known>
Return the direct answer, the path:line evidence, and up to ten key files.
```

## Planner (`dev-team:planner`)

```
Task <T-id>: <title>
Goal: <what the user wants, in their words where useful>
Non-goals: <what is explicitly out of scope, if the user said so>
Context: <constraints, related tasks, decisions already made, answers to earlier questions>
Start from: <paths, modules or features the change is near>
Write the plan to: docs/plans/<T-id>-<slug>.md
Return the plan as markdown and end with open questions.
```

For a panel candidate (used by the plan workflow, rarely by hand), add:
`Lens: <minimal | clean | pragmatic | risk>. Plan from this lens only; a judge will compare.`

## Implementer (`dev-team:implementer`)

```
Task <T-id>: <title>
Plan: docs/plans/<T-id>-<slug>.md (read it first)
Your slice: <slice name from the plan>
Files you own: <the slice's file set; do not edit others>
Contracts you build against: <signatures, routes, shapes from the plan that this slice consumes or provides>
Parallel siblings: <other slices being built at the same time, so you know what not to touch; or "none">
Definition of done: <from the plan; include the lint, typecheck, build commands to run>
Report files changed, contracts implemented, deviations with reasons, commands run with results, and what the reviewer should look at hardest.
```

Rework after review:

```
Task <T-id> rework, round <n>
Plan: docs/plans/<T-id>-<slug>.md
Fix these blocking findings and nothing else:
1. <path:line> — <summary> — <failure scenario> — <suggested direction>
2. ...
Cheap nits to take if trivial: <list or "none">
Run <lint/typecheck/test commands> and report each finding with how it was fixed.
```

## Reviewer (`dev-team:reviewer`)

Full review (small fanout, or no Workflow tool):

```
Task <T-id>: review <scope: git range | staged | working tree>
Plan: docs/plans/<T-id>-<slug>.md
Built: <one sentence on what the implementer reports building>
Lens: <one of correctness | plan-drift | security | error-handling | tests | simplicity>, or "all"
Report only findings at confidence 70 or above, blocking first, each with path:line, failure scenario, and suggested direction.
```

Refute mode:

```
Refute this finding. Open the cited code yourself and decide whether it is real as described; default to refuted when the evidence is not in the code.
Finding: <path:line> [<lens>, <severity>, confidence <n>]
Summary: <summary>
Failure scenario: <scenario>
Return real (true/false), confidence, reason, and an adjusted severity only if the original is clearly wrong.
```

## Tester (`dev-team:tester`)

```
Task <T-id>: verify <title>
Plan verification section: <paste it, or the path and section name>
Changed files: <list from the implementer's report>
Contracts to exercise: <routes, functions, components>
Test commands (if known): <from CLAUDE.md or the plan>
Write tests for the new behavior in the project's style, run them and the nearest existing suite, and report GREEN or RED with the exact commands and output.
```

Characterize a bug:

```
Task <T-id>: reproduce <title>
Report: <the user's description, verbatim>
Where it likely lives: <paths if known>
Write the smallest failing test that reproduces it. Do not fix the code. Report the command and the failing output, or that it could not be reproduced and what you tried.
```

## Debugger (`dev-team:debugger`)

```
Task <T-id>: <title>
Failing output (verbatim from the tester):
<paste>
Changed files in this task: <list>
Plan: docs/plans/<T-id>-<slug>.md (for the intended behavior)
Find the root cause, make the smallest fix for the cause, re-run the failing case and the surrounding suite, and report the cause with path:line, the fix, and the real results. Three dead hypotheses without progress: stop and report.
```
