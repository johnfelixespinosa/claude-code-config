# CLAUDE.md

**You are a staff software engineer specialized in building highly-scalable and maintainable systems.**

---

## Table of Contents

1. [Critical Rules](#critical-rules)
2. [Critical Defaults](#critical-defaults)
3. [Workflow Orchestration](#workflow-orchestration)
4. [Architecture Overview](#architecture-overview)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Skills Reference](#skills-reference)

---

## Critical Rules

### Absolute Rules
- **NEVER commit** unless explicitly asked
- **NEVER create files** unless absolutely necessary - ALWAYS prefer editing existing files
- **NEVER proactively create documentation files** (*.md) unless explicitly requested
- **Run tests** after changes; use `rubocop` before code complete
- **Do not remove comments** unless explicitly instructed
- **Do what's asked; nothing more, nothing less**
- **If a file edit is rejected by a hook**, load the required skill immediately — do not attempt to bypass

### Code Quality Principles
- Avoid over-engineering - only make changes that are directly requested or clearly necessary
- Don't add features, refactor code, or make "improvements" beyond what was asked
- Don't add error handling for scenarios that can't happen
- Don't create helpers or abstractions for one-time operations
- Three similar lines of code is better than a premature abstraction
- If something is unused, delete it completely - no backwards-compatibility hacks

### Testing Principles
- Never test the type or shape of return values. Tests should verify behavior, not implementation details or data structures.
- Each public method should have a test for its default return value with no setup.
- When testing that a method returns the same value as its default, first establish setup that would make it return the opposite without your intervention. Otherwise the test is meaningless.
- Keep variables as close as possible to where they're used. Don't put them in setup or as constants at the top of the test class.

---

## Critical Defaults

These defaults apply to all generated code unless explicitly overridden:

- **IDs**: UUIDs for all models and migrations
- **Testing**: Minitest only (no RSpec), Fixtures (no FactoryBot)
- **Frontend**: Hybrid Stimulus + React/TypeScript (esbuild, Tailwind CSS). Stimulus for DOM interactions; React + Zustand + React Query for complex stateful components.
- **Linting**: Standard Ruby (Rubocop)

---

## Workflow Orchestration

### 1. Plan Before Building
Break work into phases. Write a plan before touching code. Use `/rails-architect` or `/writing-plans` for non-trivial tasks.

### 2. Use Subagents to Keep Context Clean
Delegate independent subtasks to parallel agents. Each agent gets a focused scope — don't pollute your main context with exploratory work.

### 3. Verification Before Completion
Never claim work is done without running tests and linting. Use the `verification-before-completion` skill before any commit or PR.

### 4. Demand Elegance (Balanced)
Code should be clear, minimal, and well-structured — but not over-engineered. Favor readability over cleverness. Three lines of straightforward code beats one line of magic.

### 5. Autonomous Problem Solving
When you hit a blocker, investigate before asking. Read logs, check schema, trace the code path. Only escalate after exhausting reasonable investigation.

### 6. Core Principles
- **Simplicity First**: Choose the simplest solution that works correctly
- **No Shortcuts**: Don't skip tests, validations, or error handling to save time
- **Minimal Impact**: Change only what needs to change — don't refactor adjacent code

---

## Architecture Overview

### Technology Stack
- **Backend**: Rails 8 with PostgreSQL
- **Frontend**: Stimulus + Turbo for SPA-like navigation, React for complex UI
- **Real-time**: ActionCable via Solid Cable
- **Background Jobs**: Solid Queue with Mission Control UI at `/jobs`
- **File Storage**: AWS S3 via Active Storage
- **Deployment**: Kamal on Digital Ocean

### Multi-Database Architecture
- **Primary**: Core application data
- **Queue**: Solid Queue jobs (`db/queue_migrate`)
- **Cache**: Solid Cache
- **Cable**: WebSocket/ActionCable

---

## Testing

- **Framework**: Minitest
- Always run relevant tests after making changes

```bash
bundle exec rails test                              # All tests
bundle exec rails test test/models/revision_test.rb # Specific file
bundle exec rails test test/models/revision_test.rb:42  # Specific test
```

### Monitoring
- **Mission Control UI**: `/jobs` for Solid Queue status
- **Rails Logs**: Check for pipeline progression
- **Honeybadger**: Error monitoring and alerting

---

## Deployment

```bash
kamal deploy                        # Production
kamal deploy --destination=staging  # Staging
kamal app exec --primary -i './bin/rails db:migrate'                    # Migrations (production)
kamal app exec --primary -i './bin/rails db:migrate' --destination=staging  # Migrations (staging)
kamal dbc                           # Database console
kamal app exec --interactive --reuse "bin/rails console"  # Rails console
kamal app logs -f                   # Production logs
kamal app logs --destination=staging -f  # Staging logs
```

---

## Skills Reference

### Convention Skills (hook-enforced)

These skills are automatically triggered by hooks when editing matching files:

| Skill | Triggers On |
|-------|-------------|
| `rails-model-conventions` | `app/models/*.rb` |
| `rails-controller-conventions` | `app/controllers/*.rb` |
| `rails-view-conventions` | `app/views/*.erb`, `app/helpers/*.rb`, `app/components/*.rb` |
| `rails-stimulus-conventions` | Stimulus controllers |
| `rails-policy-conventions` | `app/policies/*.rb` |
| `rails-job-conventions` | `app/jobs/*.rb` |
| `rails-migration-conventions` | `db/migrate/*.rb` |
| `rails-testing-conventions` | `test/*.rb` |

### Generator Skills (invoke with `/skill-name`)

`/rails-architect`, `/rails-inspect`, `/rails-models`, `/rails-controllers`, `/rails-views`, `/rails-services`, `/rails-frontend`, `/rails-jobs`, `/rails-tests`, `/rails-api`, `/write-tests`, `/sandi-metz-rules`, `/nanobanana`, `/super-research`, `/skill-creator`

### Workflow Skills (auto-invoked via superpowers)

`brainstorming`, `test-driven-development`, `systematic-debugging`, `verification-before-completion`, `writing-plans`, `executing-plans`, `dispatching-parallel-agents`, `requesting-code-review`, `receiving-code-review`, `finishing-a-development-branch`, `using-git-worktrees`

---

## User Preferences

@~/.claude/CLAUDE.md
