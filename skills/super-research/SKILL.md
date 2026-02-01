---
name: super-research
description: Generate comprehensive implementation plans by consulting multiple AI models (Gemini Pro, GPT-5) through structured multi-round discussions using parallel subagents
user_invocable: true
arguments: "task description"
---

# Super Research Skill

Generate comprehensive implementation plans by consulting Gemini Pro and GPT-5 through zen MCP tools, using parallel Task subagents for speed. Uses 3 consultation rounds where models ask clarifying questions, provide perspectives, and cross-review each other's recommendations.

## Workflow Overview

```
Phase 1: User Interview     → Gather requirements and constraints
Phase 2: Reconnaissance     → Explore codebase for context
Phase 3: Multi-Model Consultation (adaptive, up to 3 rounds)
  - Round 1: Clarifying questions (parallel subagents)
  - Round 2: Perspectives (parallel subagents)
  - Round 3: Cross-review (parallel subagents) — ONLY if perspectives conflict
Phase 4: Synthesis          → Combine into final plan
Phase 5: Delivery           → Present plan and offer next steps
```

## Instructions

When this skill is invoked, follow these phases exactly:

### Phase 1: User Interview

1. If the user provided a task description with the skill invocation, acknowledge it
2. Ask clarifying questions about:
   - Specific requirements and constraints
   - Performance considerations
   - Integration points with existing code
   - Any preferences for implementation approach
3. Summarize understanding before proceeding

### Phase 2: Reconnaissance

1. Initialize the session:
   ```bash
   bash ~/.claude/skills/super-research/scripts/init_session.sh
   ```
2. Use the Task tool with `subagent_type=Explore` to analyze:
   - Relevant existing code patterns
   - Architecture and file organization
   - Dependencies and integrations
   - Similar implementations to reference
3. Save findings to `research_notes/00-reconnaissance.md`

### Phase 3: Multi-Model Consultation

Generate a session ID for continuation tracking:
```
session_id = "sr-{YYYYMMDD}-{4-char-random}"
```

#### Round 1: Clarifying Questions (Parallel Subagents)

Dispatch two Task subagents in a **single message** (parallel), each calling `mcp__zen__thinkdeep`:

**Subagent 1 — Gemini Pro** (architecture focus):
```
Task subagent_type: "general-purpose"
→ calls mcp__zen__thinkdeep with:
  continuation_id: "gemini-{session_id}"
  model: "pro"
  thinking_mode: "high"
  prompt: [Use Round 1 template from references/prompt-templates.md]
  focus_areas: ["architecture", "system design", "scalability"]
→ returns the model's questions
```

**Subagent 2 — GPT-5** (implementation + edge cases focus):
```
Task subagent_type: "general-purpose"
→ calls mcp__zen__thinkdeep with:
  continuation_id: "gpt5-{session_id}"
  model: "gpt-5"
  thinking_mode: "high"
  prompt: [Use Round 1 template]
  focus_areas: ["implementation", "code patterns", "edge cases", "security"]
→ returns the model's questions
```

Collect questions from both subagents, deduplicate, and present to user. Save to `research_notes/01-round1-questions.md`.

#### Round 2: Perspectives (Parallel Subagents)

After user answers Round 1 questions, dispatch two Task subagents in a **single message** (parallel):

**Subagent 1 — Gemini Pro**: Architecture and system design perspective
**Subagent 2 — GPT-5**: Implementation patterns, code structure, edge cases, and security

Each subagent calls `mcp__zen__thinkdeep` using the same continuation_ids to maintain context. Save to `research_notes/02-round2-perspectives.md`.

**After Round 2, evaluate whether Round 3 is needed:**
- Compare the two perspectives for alignment
- If both models broadly agree on architecture, implementation approach, and key decisions → **skip Round 3** and proceed directly to Phase 4 (Synthesis)
- If there are meaningful conflicts, gaps, or contradictions → proceed to Round 3

#### Round 3: Cross-Review (Parallel Subagents) — Conditional

**Only run this round if Round 2 perspectives have significant conflicts or gaps.**

Dispatch two Task subagents in a **single message** (parallel):

1. Each subagent receives all Round 2 perspectives and calls `mcp__zen__thinkdeep`
2. Each model reviews the other's perspective:
   - Identifies gaps or conflicts
   - Suggests improvements to the combined approach
   - Flags any concerns or risks
3. Both run in parallel since they review Round 2 outputs (not each other's Round 3 reviews)
4. Save to `research_notes/03-round3-synthesis.md`

### Phase 4: Synthesis

Use `mcp__zen__thinkdeep` with model "pro" and thinking_mode "max" to:

1. Combine all perspectives into a unified implementation plan
2. Resolve any conflicts between model recommendations
3. Structure the plan with:
   - Executive summary
   - Implementation steps (ordered)
   - File changes required
   - Testing strategy
   - Risk mitigation
   - Alternative approaches considered

Save final plan to `research_notes/04-final-plan.md`

### Phase 5: Delivery

1. Present the final implementation plan to the user
2. Highlight key decisions and tradeoffs
3. Offer next steps:
   - "Would you like me to begin implementation?"
   - "Would you like to discuss any specific aspect in more detail?"
   - "Should we explore alternative approaches?"

## Model Specializations

| Model | Zen ID | Strengths | Use For |
|-------|--------|-----------|---------|
| Gemini Pro | `pro` | Deep reasoning, 1M context | Architecture, system design, complex analysis |
| GPT-5 | `gpt-5` | Code generation, patterns, reasoning | Implementation details, code structure, edge cases, security |
| Flash | `flash` | Speed, 1M context | Quick validations, simple queries |

## Tool Selection Guide

- **thinkdeep**: Primary tool for all consultation rounds (complex reasoning)
- **chat**: Quick follow-up questions, clarifications
- **codereview**: When reviewing existing code or proposed changes
- **analyze**: For codebase exploration during reconnaissance

## Output Structure

All outputs saved to `research_notes/` in the current working directory:

```
research_notes/
├── 00-reconnaissance.md      # Codebase analysis
├── 01-round1-questions.md    # Model questions + user answers
├── 02-round2-perspectives.md # Individual model perspectives
├── 03-round3-synthesis.md    # Cross-review results
├── 04-final-plan.md          # Final implementation plan
└── session-log.md            # Session metadata and summary
```

## Example Invocation

```
/super-research implement user authentication with OAuth2 and JWT tokens
```

## References

See `references/prompt-templates.md` for detailed prompt templates used in each phase.
