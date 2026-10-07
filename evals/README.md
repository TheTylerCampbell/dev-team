# Evals

Starter cases for `claude plugin eval`. The case scaffolds a tiny Python CLI
and asks the team to add a flag, then checks that the skill fired, a planner
ran before code, the ledger was created, and the report is honest.

The scaffold writes files, so the run needs the scaffold and write tools
granted explicitly:

```
claude plugin eval /path/to/dev-team --scaffold --allow-tools Bash Write Edit
```

Add a case by copying the directory: `prompt.md` carries the prompt and run
settings, `graders/*.md` carry one check each.
