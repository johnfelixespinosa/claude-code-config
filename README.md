# Claude Code Configuration

Personal Claude Code configuration for John Espinosa.

## Structure

```
.claude/
├── CLAUDE.md              # Global conventions and rules
├── settings.json          # Claude Code settings (thinking, plugins, hooks)
├── settings.local.json    # Local permission overrides
├── .mcp.json              # MCP server configurations
├── hooks/                 # Custom hooks (PreToolUse, PostToolUse)
│   └── rails-conventions.sh
└── skills/                # Custom skills (flat namespace)
    ├── rails-*            # Rails-related skills
    ├── workflow-*         # Workflow/process skills (brainstorming, plans, etc.)
    └── ...                # Other skills
```

## Skills Organization

Skills use a **flat namespace** (Claude Code requirement) with naming prefixes:

| Prefix | Category | Examples |
|--------|----------|----------|
| `rails-*` | Rails development | rails-models, rails-controller-conventions |
| `workflow-*` | Development workflow | writing-plans, executing-plans |
| `*-conventions` | Hook-triggered standards | rails-model-conventions |
| (none) | General tools/techniques | pulse, nanobanana, systematic-debugging |

### Convention Skills vs Action Skills

- **`-conventions` skills**: Triggered by hooks when EDITING files
- **Action skills**: User-invoked for CREATING new things

Example: `rails-model-conventions` enforces rules when editing models, while `rails-models` creates new models.

## Hooks

`hooks/rails-conventions.sh` - "Deny until skill loaded" pattern that blocks edits to Rails files until the appropriate conventions skill is loaded.

## MCP Servers

- `context7` - Upstash context management
- `memory` - Model Context Protocol memory server

## Maintenance

After making changes:
```bash
cd ~/.claude
git add -A
git commit -m "Description of changes"
git push
```

---

*Last updated: 2026-01-30*
