#!/bin/bash
# Initialize a super-research session
# Creates session ID and research_notes directory

# Generate session ID: sr-YYYYMMDD-XXXX
DATE=$(date +%Y%m%d)
RANDOM_SUFFIX=$(cat /dev/urandom | LC_ALL=C tr -dc 'a-z0-9' | fold -w 4 | head -n 1)
SESSION_ID="sr-${DATE}-${RANDOM_SUFFIX}"

# Create research_notes directory in current working directory
NOTES_DIR="research_notes"
mkdir -p "${NOTES_DIR}"

# Initialize session log
cat > "${NOTES_DIR}/session-log.md" << EOF
# Super Research Session Log

## Session Info
- **Session ID**: ${SESSION_ID}
- **Started**: $(date '+%Y-%m-%d %H:%M:%S')
- **Working Directory**: $(pwd)

## Continuation IDs
- Gemini Pro: \`gemini-${SESSION_ID}\`
- GPT-5: \`gpt5-${SESSION_ID}\`
- O3: \`o3-${SESSION_ID}\`

## Phase Progress
- [ ] Phase 1: User Interview
- [ ] Phase 2: Reconnaissance
- [ ] Phase 3: Multi-Model Consultation
  - [ ] Round 1: Clarifying Questions
  - [ ] Round 2: Perspectives
  - [ ] Round 3: Cross-Review
- [ ] Phase 4: Synthesis
- [ ] Phase 5: Delivery

## Session Notes

EOF

# Output session info for Claude to capture
echo "SESSION_ID=${SESSION_ID}"
echo "NOTES_DIR=${NOTES_DIR}"
echo "GEMINI_THREAD=gemini-${SESSION_ID}"
echo "GPT5_THREAD=gpt5-${SESSION_ID}"
echo "O3_THREAD=o3-${SESSION_ID}"
