#!/bin/bash
# PostToolUse hook: log skill invocations to a JSONL file.
# Runs async so it never blocks the conversation.
#
# TOOL_INPUT contains the skill name passed to the Skill tool.

USAGE_FILE="$HOME/.claude/skills/usage.jsonl"

# Extract skill name from TOOL_INPUT (JSON with "skill" key)
SKILL=$(echo "$TOOL_INPUT" | grep -o '"skill"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"skill"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

[ -z "$SKILL" ] && exit 0

mkdir -p "$(dirname "$USAGE_FILE")"
echo "{\"skill\":\"$SKILL\",\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$USAGE_FILE"
