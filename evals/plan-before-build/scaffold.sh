#!/bin/sh
# Creates a tiny Python CLI project for the eval workspace.
set -e
mkdir -p tinycli tests
cat > pyproject.toml <<'PY'
[project]
name = "tinycli"
version = "0.3.1"
PY
cat > tinycli/__init__.py <<'PY'
PY
cat > tinycli/cli.py <<'PY'
import sys


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "hello":
        print("hello")
        return 0
    print("usage: tinycli hello", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
PY
cat > tests/test_cli.py <<'PY'
from tinycli.cli import main


def test_hello(capsys):
    assert main(["hello"]) == 0
    assert capsys.readouterr().out.strip() == "hello"
PY
cat > CLAUDE.md <<'MD'
# tinycli
Python 3, no dependencies. Run tests with `python3 -m pytest -q`.
MD
