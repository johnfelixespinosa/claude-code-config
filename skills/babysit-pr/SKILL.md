---
name: babysit-pr
description: >
  Automatically monitor a pull request for code review bot comments (Cubic, Greptile, CodeRabbit, etc.)
  and address their feedback. This skill MUST be invoked automatically after any `git push` or
  `gh pr create` command — the PostToolUse hook will trigger it. Also invoke manually with
  `/babysit-pr <PR-URL-or-number>`. Triggers on: pushing code, creating PRs, "monitor PR",
  "check PR reviews", "babysit", "address review comments", "fix bot feedback", or any mention
  of Cubic, Greptile, or code review bots.
---

# Babysit PR

Monitor a pull request for code review bot comments, address their feedback, resolve conversations, and re-request review — all automatically. Escalate items that need human judgment.

## When This Runs

This skill is triggered in two ways:

1. **Automatically** — A PostToolUse hook detects `git push` or `gh pr create` output and injects a `<babysit-pr-trigger>` tag with the PR URL. When you see this tag, invoke this skill immediately.
2. **Manually** — The user types `/babysit-pr` or `/babysit-pr <PR-URL-or-number>`.

## How It Works

### Phase 1: Identify the PR

If a PR URL or number was provided (from hook or user), use it directly. Otherwise:

```bash
gh pr view --json url,number,headRefName --jq '{url, number, headRefName}'
```

If no PR exists for the current branch, tell the user and stop.

### Phase 1.5: Trigger Bots (Only If Not Already Running)

Before triggering any bot, **check if it is already running or has already reviewed the latest commit**. This prevents duplicate reviews and bot confusion.

**Step 1: Get the latest commit SHA:**

```bash
LATEST_SHA=$(gh pr view {number} --repo {owner}/{repo} --json headRefOid --jq '.headRefOid')
```

**Step 2: Check all bot check runs and statuses:**

```bash
# Check runs (GitHub Actions, Cubic, CodeRabbit, etc.)
gh api repos/{owner}/{repo}/commits/{LATEST_SHA}/check-runs \
  --jq '.check_runs[] | {name, status, conclusion, app: .app.slug}'

# Commit statuses (some bots use these instead)
gh api repos/{owner}/{repo}/commits/{LATEST_SHA}/status \
  --jq '.statuses[] | {context, state, description}'
```

**Step 3: Determine bot state before acting:**

| Bot State | Action |
|-----------|--------|
| Check run `status: "queued"` or `"in_progress"` | **Do NOT trigger.** Bot is actively working. |
| Check run `status: "completed"` on latest SHA | **Do NOT trigger.** Bot already reviewed this commit. |
| No check run found for latest SHA | **Trigger.** Bot hasn't started. |
| Check run `status: "completed"` on older SHA only | **Trigger.** New commits need review. |

**Step 4: Trigger bots that need it:**

Only trigger bots that are in the "Trigger" state above.

```bash
# Greptile — only if not already running or completed on latest SHA
gh pr comment {number} --repo {owner}/{repo} --body "@greptileai review"
```

**Bot trigger summary:**
| Bot | Auto-runs on push? | How to trigger | How to detect running |
|-----|-------------------|----------------|----------------------|
| Cubic | Yes | Automatic | Check runs with app slug containing `cubic` |
| Greptile | No | Comment `@greptileai review` | Check runs/statuses with name containing `greptile` |
| CodeRabbit | Yes | Automatic | Check runs with app slug containing `coderabbit` |

### Phase 2: Wait for All Bots to Finish

**Do NOT start processing comments until all active bots have completed.** This ensures you see the full picture before making any fixes.

**Polling loop:**
1. **Check every 60 seconds** for bot completion
2. Query check runs and statuses (same as Phase 1.5, Step 2)
3. A bot is "done" when its check run status is `"completed"` or no check run exists (bot not installed)
4. **All known bots must be done** before proceeding to Phase 3
5. **Timeout after 10 minutes of waiting** — proceed with whatever comments are available and note which bots are still running

Announce to the user:
"Waiting for review bots to finish analyzing PR #N. Will start processing once all bots complete."

### Phase 3: Check for Bot Comments

Once all bots are done, fetch all review comments and PR reviews in one pass:

```bash
# Get all PR review comments (inline comments)
gh api repos/{owner}/{repo}/pulls/{number}/comments \
  --jq '.[] | {id, user: .user.login, body, path, line: .original_line, created_at, in_reply_to_id}'

# Get all PR reviews (top-level reviews)
gh api repos/{owner}/{repo}/pulls/{number}/reviews \
  --jq '.[] | {id, user: .user.login, body, state, submitted_at}'
```

**Known bot usernames to watch for:**
- `cubic-dev[bot]` or `cubic-bot` — Cubic
- `greptile[bot]` or `greptile-io[bot]` — Greptile
- `coderabbitai[bot]` — CodeRabbit (if present)
- Any username containing `[bot]` that posts code review content

**Filter for actionable comments:**
- Has a non-empty body
- Is NOT a reply to another comment (unless it's a new thread)
- Has not already been resolved
- Was created after the monitoring started (track timestamps)

### Phase 4: Triage and Classify Comments

Before making any fixes, classify **every** bot comment into one of two categories:

#### Auto-Fix (handle autonomously):
- Style/formatting issues
- Naming suggestions (simple renames)
- Missing null checks
- Unused imports/variables
- Simple performance fixes (e.g., `select` instead of `map.compact`)
- Documentation/comment suggestions

#### Escalate to User (needs human judgment):
- Security concerns (injection, auth, data exposure)
- Architectural changes (extract class/service, change patterns)
- Business logic changes (altering behavior, not just fixing bugs)
- Performance changes that alter semantics (caching, eager loading that changes data freshness)
- Conflicting bot feedback (one bot says X, another says the opposite)
- Any fix that would touch more than 3 files
- Anything the bot explicitly flags as high severity

**For critical escalations (security, data loss):** Immediately notify the user — do not wait for the summary. Present the full escalation detail (see Phase 7 format) inline and ask if they want to proceed or handle it themselves.

**For non-critical escalations:** Collect them for the final summary.

### Phase 5: Batch Fix All Auto-Fix Items

Process all auto-fixable comments from **all bots** together:

1. **Make all fixes** across all files — do not commit between individual fixes.

2. **Reply to each addressed comment** on GitHub:
   ```bash
   gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
     -f body="Addressed — {brief description of what was changed}."
   ```

3. **Resolve each conversation:**
   ```bash
   # Get thread node IDs
   gh api graphql -f query='query { repository(owner: "OWNER", name: "REPO") { pullRequest(number: NUMBER) { reviewThreads(first: 100) { nodes { id isResolved comments(first: 1) { nodes { databaseId } } } } } } }'

   # Resolve each thread
   gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "THREAD_NODE_ID"}) { thread { isResolved } } }'
   ```

4. **Reply to escalated comments** explaining they've been flagged for human review:
   ```bash
   gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
     -f body="Flagged for human review — this requires manual assessment."
   ```

5. **Single commit** with all fixes from all bots:
   ```
   fix: address review bot feedback (Cubic, Greptile)
   ```

6. **Single push:**
   ```bash
   git push
   ```

### Phase 6: Re-monitor After Push (Max 3 Cycles)

The fix-push-review loop runs for a **maximum of 3 cycles**. Track the cycle count starting from the first batch fix.

**Each cycle:**
1. **Check bot states again** (Phase 1.5 logic) — only re-trigger bots that need it
2. **Wait for all bots to finish** (Phase 2 logic)
3. **Check for new comments** (Phase 3)
4. **Triage and fix** (Phases 4-5) if there are new actionable comments
5. **Record cycle stats**: how many comments were fixed, which bots generated them

**Stop monitoring when:**
- No new comments after all bots complete their re-review — **clean exit**
- All comments are resolved or escalated — **clean exit**
- **3 fix-push cycles completed and bots are still generating new comments** — **loop detected, escalate**
- 30-minute maximum time cap reached — **timeout, escalate**

#### When a Loop Is Detected (3 cycles exhausted)

If bots are still generating new comments after 3 cycles, **stop fixing and escalate to the user** with a loop report:

```
🔄 Review loop detected after 3 fix cycles.

Cycle history:
- Cycle 1: Fixed 8 comments (Cubic: 5, Greptile: 3), pushed
- Cycle 2: Fixed 3 new comments (Cubic: 1, Greptile: 2), pushed
- Cycle 3: Fixed 2 new comments (Cubic: 2), pushed → 2 new comments appeared

Still unresolved (2 items):
1. [LOOP] Cubic keeps flagging method length in orders_controller.rb:23
   after each fix — likely a false positive or requires architectural change
   File: app/controllers/orders_controller.rb:23
   Bot says: "Method too long (12 lines)"
   Fix attempted: Extracted helper method → Cubic flagged the helper too
   Link: https://github.com/...

2. [LOOP] Fixing Greptile suggestion triggers Cubic comment
   Greptile: "Use `find_each` instead of `each`" (app/jobs/sync_job.rb:15)
   Fix applied → Cubic: "Avoid `find_each` in jobs with small datasets"
   Link (Greptile): https://github.com/...
   Link (Cubic): https://github.com/...

Recommendation: Review these manually — they appear to be either false
positives or conflicting bot opinions that can't be resolved automatically.
```

Do NOT continue fixing after 3 cycles. Present the loop report and wait for user input.

### Phase 7: Final Summary

After monitoring ends, report to the user with two sections:

**Section 1: Auto-fixed items**

```
PR #N monitoring complete.
- Comments addressed: X
- Files modified: Y
- Commits added: Z
- Bots that reviewed: Cubic, Greptile
- Status: All auto-fixable comments resolved
```

**Section 2: Items needing your input**

If there are escalated items, present each with full context:

```
⚠️ Needs your input (N items):

1. [CRITICAL] SQL injection risk — Cubic
   File: app/controllers/search_controller.rb:45
   Bot says: "Raw SQL interpolation in search query"
   Code: `where("name LIKE '%#{params[:q]}%'")`
   Why escalated: Security concern — fix changes query behavior
   Link: https://github.com/owner/repo/pull/123#discussion_r456

2. [HIGH] Extract service object — Greptile
   File: app/controllers/orders_controller.rb:12-57
   Bot says: "Create action is 45 lines with mixed concerns — order
   validation, payment processing, and notification all in one method"
   Why escalated: Architectural change beyond auto-fix scope
   Link: https://github.com/owner/repo/pull/123#discussion_r789

3. [MEDIUM] Conflicting feedback — Cubic vs Greptile
   File: app/models/user.rb:23
   Cubic says: "Add presence validation for email"
   Greptile says: "Email validation should be in a form object, not the model"
   Why escalated: Bots disagree on approach — needs human decision
   Link (Cubic): https://github.com/...
   Link (Greptile): https://github.com/...
```

**Priority labels:**
- `[CRITICAL]` — Security, data loss, authentication/authorization issues
- `[HIGH]` — Architectural changes, business logic alterations, 3+ file changes
- `[MEDIUM]` — Conflicting bot feedback, semantic performance changes, non-trivial refactors

## Important Behavior Rules

- **Never force-push.** Always create new commits for fixes.
- **Never skip a comment.** Every bot comment gets either a fix, a reply explaining why no change was made, or an escalation to the user.
- **Wait for all bots before fixing.** Do not start fixing comments while any bot is still reviewing — you'll miss comments and trigger unnecessary re-reviews.
- **Batch all fixes into a single commit.** Never commit fixes from one bot separately from another. One commit, one push per cycle.
- **Do not re-trigger bots that are already running.** Always check check-run/status state before tagging a bot.
- **Escalate immediately for critical items.** Security and data-loss concerns get surfaced to the user as soon as they're identified, not held for the final summary.
- **Respect existing code style.** Match the patterns already in the codebase.
- **Track what you've seen.** Keep a list of comment IDs you've already processed so you don't address the same comment twice across check cycles.
- **Hard limit of 3 fix-push cycles.** If bots are still generating new comments after 3 rounds of fixes, stop and escalate with a loop report. Do not attempt a 4th cycle.
- **Track cycle history.** Record how many comments were fixed per cycle and which bots generated them. This data is required for the loop report if the limit is hit.
