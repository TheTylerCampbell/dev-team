#!/bin/sh
# dev-team SessionStart hook.
# Resolves the token profile, team size and tracker switch, then hands them to
# the session as additionalContext so the orchestrator skill can honor them.
#
# Precedence, highest first:
#   1. .claude/dev-team.local.md in the project (YAML frontmatter: profile, fanout, tracker)
#   2. plugin settings (claude plugin configure dev-team), which arrive as
#      CLAUDE_PLUGIN_OPTION_PROFILE / _FANOUT / _TRACKER
#   3. defaults: balanced / standard / true
# Every value is validated against its allowed set; anything else falls back.

profile="${CLAUDE_PLUGIN_OPTION_PROFILE:-}"
fanout="${CLAUDE_PLUGIN_OPTION_FANOUT:-}"
tracker="${CLAUDE_PLUGIN_OPTION_TRACKER:-}"
source="plugin settings"

local_file=".claude/dev-team.local.md"
if [ -f "$local_file" ]; then
  fm=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$local_file")
  v=$(printf '%s\n' "$fm" | sed -n 's/^profile:[[:space:]]*"\{0,1\}\([a-z]*\)"\{0,1\}.*/\1/p' | head -1)
  [ -n "$v" ] && profile="$v" && source="$local_file"
  v=$(printf '%s\n' "$fm" | sed -n 's/^fanout:[[:space:]]*"\{0,1\}\([a-z]*\)"\{0,1\}.*/\1/p' | head -1)
  [ -n "$v" ] && fanout="$v" && source="$local_file"
  v=$(printf '%s\n' "$fm" | sed -n 's/^tracker:[[:space:]]*"\{0,1\}\([a-zA-Z]*\)"\{0,1\}.*/\1/p' | head -1)
  [ -n "$v" ] && tracker="$v" && source="$local_file"
fi

case "$profile" in economy|balanced|quality) ;; *) profile="balanced" ;; esac
case "$fanout" in small|standard|large) ;; *) fanout="standard" ;; esac
case "$tracker" in false|FALSE|False|0|no|off) tracker="off" ;; *) tracker="on" ;; esac

case "$fanout" in
  small) width=2; lenses=2 ;;
  large) width=8; lenses=6 ;;
  *) width=4; lenses=4 ;;
esac

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"dev-team settings (from %s): profile=%s fanout=%s (up to %s agents in parallel, %s review lenses) tracker=%s. The dev-team skill reads these when it runs; change them with `claude plugin configure dev-team@dev-team`, with .claude/dev-team.local.md, or with `/dev-team config profile=<economy|balanced|quality> fanout=<small|standard|large>`."}}\n' "$source" "$profile" "$fanout" "$width" "$lenses" "$tracker"
exit 0
