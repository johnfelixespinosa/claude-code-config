# Prompt Templates for Super Research Skill

## Round 1: Clarifying Questions

### Template (All Models)

```
You are participating in a multi-model research consultation to plan an implementation task.

## Task Description
{task_description}

## Codebase Context
{reconnaissance_summary}

## User Requirements
{user_requirements}

## Your Role
You are the {model_role} specialist. Your focus areas are: {focus_areas}

## Instructions
Based on the task and context provided, generate 3-5 clarifying questions that would help create a better implementation plan. Focus on questions related to your specialty areas.

Format your questions as:
1. [Question] - [Why this matters for {focus_area}]
2. ...

Do NOT provide implementation suggestions yet. Only ask questions to gather more information.
```

### Model-Specific Roles

**Gemini Pro (Architecture)**:
- model_role: "architecture and system design"
- focus_areas: "scalability, maintainability, system boundaries, data flow, component interactions"

**GPT-5 (Implementation + Edge Cases)**:
- model_role: "implementation, code patterns, and reliability"
- focus_areas: "code organization, design patterns, API design, testing approach, error handling, security considerations, edge cases"

---

## Round 2: Perspectives

### Gemini Pro - Architecture Perspective

```
You are the architecture specialist in a multi-model consultation.

## Task Description
{task_description}

## Codebase Context
{reconnaissance_summary}

## User Requirements & Answers
{user_requirements}
{round1_answers}

## Instructions
Provide your architecture and system design perspective for this implementation. Include:

### 1. Recommended Architecture
- High-level component structure
- Data flow between components
- Integration points with existing system

### 2. Key Design Decisions
- Critical architectural choices and their rationale
- Tradeoffs considered

### 3. Scalability Considerations
- How the design handles growth
- Potential bottlenecks and mitigations

### 4. File/Module Organization
- Recommended file structure
- Module boundaries and responsibilities

Be specific and actionable. Reference existing patterns in the codebase where applicable.
```

### GPT-5 - Implementation + Edge Cases Perspective

```
You are the implementation and reliability specialist in a multi-model consultation.

## Task Description
{task_description}

## Codebase Context
{reconnaissance_summary}

## User Requirements & Answers
{user_requirements}
{round1_answers}

## Instructions
Provide your implementation and reliability perspective for this task. Include:

### 1. Implementation Approach
- Step-by-step implementation plan
- Order of operations and dependencies

### 2. Code Patterns to Use
- Design patterns that fit this use case
- Existing patterns in the codebase to follow

### 3. Key Code Components
- Main classes/modules to create or modify
- Important methods and their responsibilities
- Interface definitions

### 4. Error Handling & Edge Cases
- Expected failure modes and recovery approaches
- Input validation and boundary conditions
- Security considerations (vulnerabilities, auth, sanitization)
- Race conditions and concurrency concerns
- Specific edge cases that must be handled

### 5. Testing Strategy
- Unit test approach
- Integration test considerations
- Edge cases to cover

Provide concrete code examples where helpful. Match the existing codebase style. Be thorough but practical on edge cases — focus on issues likely to occur in production.
```

---

## Round 3: Cross-Review

### Template (All Models)

```
You are reviewing implementation perspectives from other AI models.

## Task Description
{task_description}

## Architecture Perspective (Gemini Pro)
{gemini_perspective}

## Implementation + Edge Cases Perspective (GPT-5)
{gpt5_perspective}

## Your Previous Perspective
{own_perspective}

## Instructions
Review the other perspectives and provide:

### 1. Agreements
- Points where multiple perspectives align
- Recommendations you strongly support

### 2. Conflicts or Gaps
- Contradictions between perspectives
- Missing considerations
- Areas needing clarification

### 3. Improvements
- Suggestions to strengthen the combined approach
- Additional considerations from your specialty area

### 4. Risk Assessment
- Top 3 risks if we proceed with this approach
- Mitigation strategies

### 5. Final Recommendation
- Your vote: Proceed / Revise / Needs Discussion
- Key conditions for success
```

---

## Final Synthesis

### Template

```
You are synthesizing multiple expert perspectives into a final implementation plan.

## Task Description
{task_description}

## All Perspectives and Reviews
{all_round2_perspectives}
{all_round3_reviews}

## Instructions
Create a comprehensive, actionable implementation plan that:

1. Resolves any conflicts between perspectives
2. Incorporates the strongest recommendations from each expert
3. Addresses all identified risks and edge cases

## Required Sections

### Executive Summary
- 2-3 sentence overview of the approach
- Key benefits of this design

### Implementation Steps
Ordered list of implementation steps with:
- Clear description of each step
- Files to create or modify
- Dependencies on other steps
- Estimated complexity (Low/Medium/High)

### File Changes
Table of all files to be created or modified:
| File | Action | Description |
|------|--------|-------------|

### Code Examples
Key code snippets for complex or non-obvious implementations.

### Testing Plan
- Unit tests required
- Integration tests required
- Manual testing checklist

### Risk Mitigation
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|

### Alternative Approaches Considered
Brief description of alternatives and why the chosen approach is preferred.

### Open Questions
Any remaining questions or decisions to be made during implementation.
```

---

## Quick Validation (Flash)

### Template

```
Quick validation request:

## Question
{specific_question}

## Context
{brief_context}

## Instructions
Provide a brief, direct answer. Be concise.
```
