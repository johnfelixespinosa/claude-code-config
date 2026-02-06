# Claude Code Configuration

Personal Claude Code configuration for John Espinosa -- a staff software engineer's opinionated setup for building Rails applications with Claude Code.

## Structure

```
.claude/
├── CLAUDE.md              # Global conventions and rules
├── settings.json          # Settings (thinking, plugins, hooks, permissions)
├── settings.local.json    # Local permission overrides
├── .mcp.json              # MCP server configurations
├── hooks/                 # Custom hooks
│   ├── hooks.json         # Hook definitions (from superpowers plugin)
│   ├── rails-conventions.sh  # Rails file-editing gate
│   ├── session-start.sh   # Session initialization (superpowers bootstrap)
│   └── run-hook.cmd       # Cross-platform hook runner (legacy)
├── skills/                # Custom skills (flat namespace)
├── orc-agent/             # Multi-instance agent orchestration
└── plugins/               # Installed plugins (superpowers, etc.)
```

## Tools

### MCP Servers

| Server | Package | Purpose |
|--------|---------|---------|
| **Context7** | `@upstash/context7-mcp` | Fetches up-to-date library documentation and code examples on demand. Ask about any framework and get current docs instead of relying on training data. |
| **Memory** | `@modelcontextprotocol/server-memory` | Persistent knowledge graph that survives across sessions. Stores entities, relations, and observations so Claude remembers project context between conversations. |
| **Zen** | External MCP | Deep thinking, code review, debugging, and pre-commit validation using multiple AI models (Gemini, GPT-5, O3). Provides `thinkdeep`, `codereview`, `debug`, `analyze`, `precommit`, and `chat` tools. |
| **Puppeteer** | External MCP | Browser automation for navigating pages, taking screenshots, clicking elements, filling forms, and running JavaScript in the browser console. |

### Plugins

| Plugin | Purpose |
|--------|---------|
| **Superpowers** (`claude-plugins-official`) | The skill system backbone. Injects the `using-superpowers` skill at session start via a `SessionStart` hook, which teaches Claude how to discover and invoke all other skills. Also provides workflow skills like brainstorming, debugging, TDD, and code review. |

## Skills

Skills are reusable instruction sets that Claude loads on demand. They live in `~/.claude/skills/` using a flat namespace with naming prefixes.

### Rails Generator Skills

Invoked with `/skill-name` to create new things:

| Skill | Purpose |
|-------|---------|
| `/rails-architect` | Plan and orchestrate multi-step Rails feature implementations |
| `/rails-inspect` | Inspect runtime state -- schema, routes, models, associations |
| `/rails-models` | Create models with migrations, associations, validations, scopes |
| `/rails-controllers` | Create RESTful controllers with strong parameters |
| `/rails-views` | Create views, partials, layouts, and view helpers |
| `/rails-services` | Create service objects with result patterns and error handling |
| `/rails-frontend` | Create Stimulus controllers, Turbo patterns, React components |
| `/rails-jobs` | Create background jobs with Solid Queue, retries, idempotency |
| `/rails-api` | Create versioned API endpoints with authentication |
| `/rails-tests` | Create tests with proper patterns and coverage strategies |
| `/write-tests` | Generate Minitest tests following project conventions |

### Rails Convention Skills

Automatically enforced by hooks when editing matching files (see [Rails Conventions Hook](#rails-conventions-hook) below):

| Skill | Triggers on |
|-------|-------------|
| `rails-model-conventions` | `app/models/*.rb` |
| `rails-controller-conventions` | `app/controllers/*.rb` |
| `rails-view-conventions` | `app/views/*.erb`, `app/helpers/*.rb`, `app/components/*.rb` |
| `rails-stimulus-conventions` | `*_controller.js` in components or packs |
| `rails-policy-conventions` | `app/policies/*.rb` |
| `rails-job-conventions` | `app/jobs/*.rb` |
| `rails-migration-conventions` | `db/migrate/*.rb` |
| `rails-testing-conventions` | `spec/*.rb` |

### Workflow Skills

Process-oriented skills that guide how to approach work (provided by Superpowers + custom):

| Skill | Purpose |
|-------|---------|
| `brainstorming` | Explores intent, requirements, and design before any creative/feature work |
| `writing-plans` | Structures multi-step implementation plans before touching code |
| `executing-plans` | Executes written plans in isolated sessions with review checkpoints |
| `test-driven-development` | Red-green-refactor workflow -- write tests before implementation |
| `systematic-debugging` | Root cause analysis before proposing fixes |
| `verification-before-completion` | Run tests and linting before claiming work is done |
| `requesting-code-review` | Structured code review after completing features |
| `receiving-code-review` | Verify feedback technically before implementing suggestions |
| `subagent-driven-development` | Execute plans with parallel independent subagents |
| `dispatching-parallel-agents` | Distribute 2+ independent tasks across parallel agents |
| `using-git-worktrees` | Isolate feature work in git worktrees |
| `finishing-a-development-branch` | Guides merge, PR, or cleanup after implementation is complete |
| `writing-skills` | Guide for creating and editing new skills |

### Utility Skills

| Skill | Purpose |
|-------|---------|
| `/super-research` | Consults Gemini Pro and GPT-5 via parallel subagents for multi-model implementation plans |
| `/sandi-metz-rules` | Reviews Ruby code against Sandi Metz's four rules for maintainable OO code |
| `/nanobanana` | Generates and edits images using Gemini CLI |
| `/pulse` | Researches any topic across Reddit, X, HN, GitHub, and the web from the last 30 days |
| `/skill-creator` | Guide for creating new skills with proper structure |

### OrcAgent Skills

Multi-instance orchestration for running multiple Claude Code agents in separate iTerm2 windows, coordinated via Redis:

| Skill | Purpose |
|-------|---------|
| `/register-agent` | Register this Claude Code instance as an agent with a specific role |
| `/send-task` | Send a task to another running agent instance |
| `/task-complete` | Signal that the current agent's task is complete |

## Rails Conventions Hook

The centerpiece of this config's Rails support is a **PreToolUse hook** (`hooks/rails-conventions.sh`) that enforces a "deny until skill loaded" pattern.

### How it works

1. Every `Edit`, `Write`, or `MultiEdit` tool call passes through the hook
2. The hook inspects the target file path against Rails directory patterns
3. If the file matches a Rails pattern (e.g. `app/models/*.rb`), the hook checks whether the corresponding conventions skill has been loaded in the current session transcript
4. **If the skill hasn't been loaded, the edit is blocked** with exit code 2 and a message telling Claude to load the skill first
5. Once the skill is loaded, subsequent edits to matching files are allowed

### Why this matters

This prevents Claude from editing Rails files using generic patterns. Instead, it forces Claude to first read the project's specific conventions for that file type -- how models should be structured, what patterns controllers should follow, which testing approaches to use, etc. The result is consistently high-quality code that follows your team's standards, not just generic Rails patterns.

### Pattern matching

```
app/controllers/*.rb   → rails-controller-conventions
app/models/*.rb        → rails-model-conventions
app/views/*.erb        → rails-view-conventions
app/helpers/*.rb       → rails-view-conventions
app/components/*.rb    → rails-view-conventions
*_controller.js        → rails-stimulus-conventions
app/policies/*.rb      → rails-policy-conventions
app/jobs/*.rb          → rails-job-conventions
db/migrate/*.rb        → rails-migration-conventions
spec/*.rb              → rails-testing-conventions
```

Files outside these patterns are not gated and can be edited freely.

## Superpowers

[Superpowers](https://github.com/claude-plugins-official/superpowers) is a Claude Code plugin that provides a **skill-driven development workflow**. It's the engine behind most of the workflow skills listed above.

### What it does

1. **Session bootstrap**: On every session start (including resume/clear/compact), a `SessionStart` hook injects the `using-superpowers` skill into Claude's context. This teaches Claude the fundamental rule: *check for and invoke relevant skills before taking any action*.

2. **Skill enforcement**: The `using-superpowers` skill establishes that if there's even a 1% chance a skill applies to the current task, Claude must invoke it. This prevents Claude from skipping structured workflows in favor of ad-hoc approaches.

3. **Workflow skills**: Superpowers bundles a set of process-oriented skills (brainstorming, TDD, debugging, planning, code review, etc.) that guide Claude through disciplined development practices rather than jumping straight to code.

4. **Skill priority**: Process skills (brainstorming, debugging) are invoked first to determine *how* to approach a task, then implementation skills (rails-models, frontend) guide *what* to build.

### The skill lifecycle

```
User sends message
  → Claude checks: does any skill apply?
  → If yes: invoke the Skill tool to load it
  → Announce: "Using [skill] to [purpose]"
  → Follow the skill's instructions exactly
  → Then respond to the user
```

### Rigid vs flexible skills

- **Rigid skills** (TDD, systematic-debugging): Must be followed exactly as written. The discipline is the point.
- **Flexible skills** (design patterns, conventions): Adapt principles to context while maintaining the core intent.

## Maintenance

After making changes:
```bash
cd ~/.claude
git add -A
git commit -m "Description of changes"
git push
```

---

*Last updated: 2026-02-06*
