---
name: super-research
description: Generate comprehensive implementation plans by consulting multiple AI models (Gemini Pro, GPT-5, O3) through structured multi-round discussions
user_invocable: true
arguments: "task description"
---

# Super Research Skill

Generate comprehensive implementation plans by consulting Gemini and OpenAI models through zen MCP tools. Uses 3 consultation rounds where models ask clarifying questions, provide perspectives, and cross-review each other's recommendations.

## Workflow Overview

```
Phase 1: User Interview     → Gather requirements and constraints
Phase 2: Reconnaissance     → Explore codebase for context
Phase 3: Multi-Model Consultation (3 Rounds)
  - Round 1: Clarifying questions (parallel)
  - Round 2: Perspectives (parallel)
  - Round 3: Cross-review (sequential)
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

#### Round 1: Clarifying Questions (Parallel)

Call all three models in parallel using `mcp__zen__thinkdeep`:

**Gemini Pro** (architecture focus):
```
continuation_id: "gemini-{session_id}"
model: "pro"
thinking_mode: "high"
prompt: [Use Round 1 template from references/prompt-templates.md]
focus_areas: ["architecture", "system design", "scalability"]
```

**GPT-5** (implementation focus):
```
continuation_id: "gpt5-{session_id}"
model: "gpt-5"
thinking_mode: "high"
prompt: [Use Round 1 template]
focus_areas: ["implementation", "code patterns", "best practices"]
```

**O3** (edge cases focus):
```
continuation_id: "o3-{session_id}"
model: "o3"
thinking_mode: "high"
prompt: [Use Round 1 template]
focus_areas: ["edge cases", "error handling", "security"]
```

Collect questions from all models, deduplicate, and present to user. Save to `research_notes/01-round1-questions.md`.

#### Round 2: Perspectives (Parallel)

After user answers Round 1 questions, call models in parallel:

**Gemini Pro**: Architecture and system design perspective
**GPT-5**: Implementation patterns and code structure
**O3**: Edge cases, error handling, and security

Use the same continuation_ids to maintain context. Save to `research_notes/02-round2-perspectives.md`.

#### Round 3: Cross-Review (Sequential)

1. Share all Round 2 perspectives with each model
2. Ask each model to:
   - Identify gaps or conflicts in other perspectives
   - Suggest improvements to the combined approach
   - Flag any concerns or risks
3. This round is sequential to allow each model to see previous reviews
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
| GPT-5 | `gpt-5` | Code generation, patterns | Implementation details, code structure |
| O3 | `o3` | Logical reasoning | Edge cases, error handling, validation |
| Flash | `flash` | Speed, 1M context | Quick validations, simple queries |
| O3-mini | `o3-mini` | Fast reasoning | Moderate complexity checks |

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
