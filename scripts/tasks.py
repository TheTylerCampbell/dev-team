#!/usr/bin/env python3
"""dev-team task ledger: a deterministic TASKS.md maintained in code, not by a model.

The ledger's source of truth is a JSON block in an HTML comment at the end of
TASKS.md. The tables above it are rendered from that block on every write, so
hand edits to the tables are overwritten; edit through this script instead.

Usage (run from the project root, or pass --file):
  tasks.py init                                   create TASKS.md if missing
  tasks.py add "<title>" [--owner A] [--status S] [--note N] [--parent T-001]
  tasks.py set T-001 [--status S] [--owner A] [--title T] [--note N]
                     [--plan PATH] [--outcome TEXT]
  tasks.py log T-001 "<note>"                     append to the activity log
  tasks.py show [T-001] [--json]                  print the ledger or one task
  tasks.py list [--status S] [--json]             one line per matching task
  tasks.py next                                   the first task not done or blocked

Statuses: todo planning ready in-progress review testing blocked done
Dates default to today (local time); pass --date YYYY-MM-DD to override.
Exit codes: 0 ok, 1 usage or validation error, 2 ledger missing or unreadable.
"""
import argparse
import datetime as _dt
import json
import os
import re
import sys

STATUSES = ["todo", "planning", "ready", "in-progress", "review", "testing", "blocked", "done"]
OPEN_STATUSES = [s for s in STATUSES if s not in ("done", "blocked")]
MARK_START = "<!-- dev-team:ledger"
MARK_END = "-->"
HEADER = (
    "# TASKS\n\n"
    "_Task ledger for the dev-team plugin. Maintained by `scripts/tasks.py`; "
    "the tables are rendered from the ledger block at the bottom, so change "
    "tasks through the script (or `/dev-team`), not by editing the tables._\n"
)


def today(override):
    if override:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", override):
            fail("--date must be YYYY-MM-DD")
        return override
    return _dt.date.today().isoformat()


def fail(msg, code=1):
    print(f"tasks.py: {msg}", file=sys.stderr)
    sys.exit(code)


def empty_ledger():
    return {"version": 1, "next_id": 1, "tasks": []}


def load(path, create=False):
    if not os.path.exists(path):
        if create:
            return empty_ledger()
        fail(f"{path} not found; run `tasks.py init` first", 2)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    start = text.rfind(MARK_START)
    if start < 0:
        fail(f"{path} has no dev-team ledger block; move it aside and run `tasks.py init`", 2)
    end = text.find(MARK_END, start)
    if end < 0:
        fail(f"{path}: ledger block is not terminated", 2)
    raw = text[start + len(MARK_START):end].strip()
    try:
        ledger = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"{path}: ledger block is not valid JSON ({exc})", 2)
    ledger.setdefault("version", 1)
    ledger.setdefault("next_id", 1)
    ledger.setdefault("tasks", [])
    return ledger


def cell(value):
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def render(ledger):
    active = [t for t in ledger["tasks"] if t["status"] != "done"]
    done = [t for t in ledger["tasks"] if t["status"] == "done"]
    out = [HEADER, "\n## Active\n\n", "| ID | Title | Owner | Status | Updated |\n", "|----|-------|-------|--------|---------|\n"]
    for t in active:
        out.append(f"| {t['id']} | {cell(t['title'])} | {cell(t.get('owner'))} | {t['status']} | {t['updated']} |\n")
    if not active:
        out.append("| | _nothing active_ | | | |\n")
    out += ["\n## Done\n\n", "| ID | Title | Outcome | Completed |\n", "|----|-------|---------|-----------|\n"]
    for t in done:
        out.append(f"| {t['id']} | {cell(t['title'])} | {cell(t.get('outcome'))} | {t['updated']} |\n")
    if not done:
        out.append("| | _nothing finished yet_ | | |\n")
    out.append("\n---\n\n## Activity log\n")
    for t in ledger["tasks"]:
        out.append(f"\n### {t['id']} — {t['title']}\n")
        if t.get("plan"):
            out.append(f"Plan: `{t['plan']}`\n")
        for entry in t.get("log", []):
            out.append(f"- {entry['date']} — {entry['note']}\n")
    out.append(f"\n{MARK_START}\n{json.dumps(ledger, indent=2, ensure_ascii=False)}\n{MARK_END}\n")
    return "".join(out)


def save(path, ledger):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(render(ledger))
    os.replace(tmp, path)


def find(ledger, task_id):
    for t in ledger["tasks"]:
        if t["id"] == task_id:
            return t
    fail(f"no task {task_id}")


def check_status(status):
    if status not in STATUSES:
        fail(f"unknown status {status!r}; one of: {', '.join(STATUSES)}")


def add_log(task, date, note):
    task.setdefault("log", []).append({"date": date, "note": note})
    task["updated"] = date


def cmd_init(args, path):
    if os.path.exists(path):
        load(path)  # validates
        print(f"{path} already exists")
        return
    save(path, empty_ledger())
    print(f"created {path}")


def cmd_add(args, path):
    ledger = load(path, create=True)
    date = today(args.date)
    status = args.status or "todo"
    check_status(status)
    task_id = f"T-{ledger['next_id']:03d}"
    ledger["next_id"] += 1
    task = {
        "id": task_id,
        "title": args.title.strip(),
        "owner": args.owner,
        "status": status,
        "parent": args.parent,
        "plan": None,
        "outcome": None,
        "created": date,
        "updated": date,
        "log": [],
    }
    if args.parent:
        find(ledger, args.parent)
    add_log(task, date, f"created ({status})" + (f": {args.note}" if args.note else ""))
    ledger["tasks"].append(task)
    save(path, ledger)
    print(task_id)


def cmd_set(args, path):
    ledger = load(path)
    task = find(ledger, args.id)
    date = today(args.date)
    changes = []
    if args.status:
        check_status(args.status)
        if args.status != task["status"]:
            changes.append(f"{task['status']} → {args.status}")
            task["status"] = args.status
    if args.owner is not None:
        task["owner"] = args.owner or None
        changes.append(f"owner {args.owner or '(none)'}")
    if args.title:
        task["title"] = args.title.strip()
        changes.append("retitled")
    if args.plan is not None:
        task["plan"] = args.plan or None
        changes.append(f"plan {args.plan or '(cleared)'}")
    if args.outcome is not None:
        task["outcome"] = args.outcome or None
    if args.outcome and task["status"] == "done":
        changes.append(f"outcome: {args.outcome}")
    if not changes and not args.note:
        fail("nothing to change")
    note = "; ".join(changes)
    if args.note:
        note = f"{note}: {args.note}" if note else args.note
    add_log(task, date, note)
    save(path, ledger)
    print(f"{task['id']} {task['status']}")


def cmd_log(args, path):
    ledger = load(path)
    task = find(ledger, args.id)
    add_log(task, today(args.date), args.note.strip())
    save(path, ledger)
    print(f"{task['id']} logged")


def cmd_show(args, path):
    ledger = load(path)
    if args.id:
        task = find(ledger, args.id)
        if args.json:
            print(json.dumps(task, indent=2, ensure_ascii=False))
        else:
            print(f"{task['id']} [{task['status']}] {task['title']}")
            print(f"  owner: {task.get('owner') or '-'}  created: {task['created']}  updated: {task['updated']}")
            if task.get("parent"):
                print(f"  parent: {task['parent']}")
            if task.get("plan"):
                print(f"  plan: {task['plan']}")
            if task.get("outcome"):
                print(f"  outcome: {task['outcome']}")
            for entry in task.get("log", []):
                print(f"  - {entry['date']} — {entry['note']}")
        return
    if args.json:
        print(json.dumps(ledger, indent=2, ensure_ascii=False))
        return
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    print(text[: text.rfind(MARK_START)].rstrip())


def cmd_list(args, path):
    ledger = load(path)
    tasks = ledger["tasks"]
    if args.status:
        check_status(args.status)
        tasks = [t for t in tasks if t["status"] == args.status]
    if args.json:
        print(json.dumps(tasks, indent=2, ensure_ascii=False))
        return
    for t in tasks:
        print(f"{t['id']}\t{t['status']}\t{t.get('owner') or '-'}\t{t['title']}")


def cmd_next(args, path):
    ledger = load(path)
    for t in ledger["tasks"]:
        if t["status"] in OPEN_STATUSES:
            print(f"{t['id']}\t{t['status']}\t{t['title']}")
            return
    print("no open tasks")


def main(argv):
    p = argparse.ArgumentParser(prog="tasks.py", description="dev-team TASKS.md ledger")
    p.add_argument("--file", default="TASKS.md", help="ledger path (default: ./TASKS.md)")
    p.add_argument("--date", help="override today's date, YYYY-MM-DD")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init").set_defaults(fn=cmd_init)

    s = sub.add_parser("add")
    s.add_argument("title")
    s.add_argument("--owner")
    s.add_argument("--status")
    s.add_argument("--note")
    s.add_argument("--parent")
    s.set_defaults(fn=cmd_add)

    s = sub.add_parser("set")
    s.add_argument("id")
    s.add_argument("--status")
    s.add_argument("--owner")
    s.add_argument("--title")
    s.add_argument("--note")
    s.add_argument("--plan")
    s.add_argument("--outcome")
    s.set_defaults(fn=cmd_set)

    s = sub.add_parser("log")
    s.add_argument("id")
    s.add_argument("note")
    s.set_defaults(fn=cmd_log)

    s = sub.add_parser("show")
    s.add_argument("id", nargs="?")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_show)

    s = sub.add_parser("list")
    s.add_argument("--status")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_list)

    sub.add_parser("next").set_defaults(fn=cmd_next)

    args = p.parse_args(argv)
    args.fn(args, args.file)


if __name__ == "__main__":
    main(sys.argv[1:])
