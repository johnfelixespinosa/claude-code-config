#!/bin/bash
# PostToolUse hook: detect git push / gh pr create and trigger babysit-pr skill.
#
# Claude Code passes tool input/output via environment variables:
#   TOOL_NAME — the tool that just ran
#   TOOL_INPUT — the command string (for Bash tool)
#   TOOL_OUTPUT — stdout from the command
#
# When this script prints to stdout, that text becomes a system message
# that Claude sees and acts on.

# Only care about Bash tool calls
if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

INPUT="$TOOL_INPUT"
OUTPUT="$TOOL_OUTPUT"

# Detect git push or gh pr create
IS_PUSH=false
IS_PR_CREATE=false
PR_URL=""

if echo "$INPUT" | grep -qE '^\s*git\s+push\b'; then
  IS_PUSH=true
fi

if echo "$INPUT" | grep -qE '^\s*gh\s+pr\s+create\b'; then
  IS_PR_CREATE=true
fi

# Nothing relevant
if [ "$IS_PUSH" = false ] && [ "$IS_PR_CREATE" = false ]; then
  exit 0
fi

# Extract PR URL from output if present
if [ "$IS_PR_CREATE" = true ]; then
  PR_URL=$(echo "$OUTPUT" | grep -oE 'https://github\.com/[^[:space:]]+/pull/[0-9]+' | head -1)
fi

# For pushes, try to find the PR for the current branch
if [ "$IS_PUSH" = true ] && [ -z "$PR_URL" ]; then
  PR_URL=$(gh pr view --json url --jq '.url' 2>/dev/null)
fi

if [ -n "$PR_URL" ]; then
  echo "<babysit-pr-trigger>"
  echo "A PR was just pushed/created: $PR_URL"
  echo "Invoke the babysit-pr skill now to monitor this PR for code review bot comments (Cubic, Greptile)."
  echo "Use: /babysit-pr $PR_URL"
  echo "</babysit-pr-trigger>"
fi
