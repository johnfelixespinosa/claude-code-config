---
name: rails-inspect
description: Inspect Rails application runtime state - schema, routes, models, and associations
user_invocable: true
arguments: "target [options]"
---

# Rails Inspect Skill

Query Rails runtime for ground truth about the application state. This skill provides accurate, up-to-date information by executing Ruby scripts via `rails runner` rather than parsing static files.

## Why Runtime Introspection?

- **Accuracy**: Catches metaprogramming, concerns, and dynamic associations
- **Completeness**: Includes inherited columns, default values, indexes
- **Efficiency**: Returns structured JSON instead of raw file contents
- **Filtering**: Supports targeted queries to minimize context usage

## Usage

```
/rails-inspect schema                    # Full database schema as JSON
/rails-inspect schema User Order         # Schema for specific tables only
/rails-inspect models                    # All models with associations
/rails-inspect models User               # Single model with full details
/rails-inspect routes                    # All routes as structured data
/rails-inspect routes users              # Routes matching 'users'
/rails-inspect gems                      # Key gems and versions
/rails-inspect environment               # Rails version, environment, config
```
https://github.com/obie/claude-on-rails/tree/main/lib/generators/claude_on_rails/swarm/templates/prompts
## Instructions

When this skill is invoked, follow these steps:

### 1. Parse the Target

Supported targets:
- `schema` - Database tables, columns, indexes, foreign keys
- `models` - ActiveRecord models, associations, validations, scopes
- `routes` - Rails routes with controller#action mappings
- `gems` - Gemfile dependencies (rails, database, auth, etc.)
- `environment` - Rails version, environment, database adapter

### 2. Check Rails Project

Verify we're in a Rails project:
```bash
test -f Gemfile.lock && grep -q "rails" Gemfile.lock
```

If not a Rails project, inform the user and exit.

### 3. Execute Appropriate Script

Run the corresponding script from `scripts/` directory:

```bash
# Schema inspection
bin/rails runner ~/.claude/skills/rails-inspect/scripts/schema.rb [table_names]

# Model inspection
bin/rails runner ~/.claude/skills/rails-inspect/scripts/models.rb [model_names]

# Routes inspection
bin/rails runner ~/.claude/skills/rails-inspect/scripts/routes.rb [filter]

# Gems inspection
bin/rails runner ~/.claude/skills/rails-inspect/scripts/gems.rb

# Environment inspection
bin/rails runner ~/.claude/skills/rails-inspect/scripts/environment.rb
```

### 4. Format Output

Present the JSON output in a readable format. For large outputs, summarize key points:
- Number of tables/models/routes
- Notable patterns (STI, polymorphic, JSONB columns)
- Potential issues (missing indexes, orphaned tables)

## Output Formats

### Schema Output
```json
{
  "tables": [
    {
      "name": "users",
      "primary_key": "id",
      "primary_key_type": "uuid",
      "columns": [
        {"name": "email", "type": "string", "null": false, "default": null},
        {"name": "role", "type": "integer", "null": false, "default": 0}
      ],
      "indexes": [
        {"name": "index_users_on_email", "columns": ["email"], "unique": true}
      ],
      "foreign_keys": []
    }
  ],
  "metadata": {
    "total_tables": 12,
    "rails_version": "8.0.1",
    "adapter": "postgresql"
  }
}
```

### Models Output
```json
{
  "models": [
    {
      "name": "User",
      "table_name": "users",
      "associations": {
        "has_many": ["posts", "comments"],
        "belongs_to": [],
        "has_one": ["profile"]
      },
      "validations": ["email (presence, uniqueness)", "name (presence)"],
      "scopes": ["active", "admins"],
      "concerns": ["Trackable", "Authenticatable"]
    }
  ]
}
```

### Routes Output
```json
{
  "routes": [
    {
      "verb": "GET",
      "path": "/users",
      "controller": "users",
      "action": "index",
      "name": "users"
    }
  ],
  "metadata": {
    "total_routes": 45,
    "namespaces": ["api/v1", "admin"]
  }
}
```

## Error Handling

- **Not a Rails project**: Check for Gemfile.lock with rails dependency
- **Database not migrated**: Catch and report pending migrations
- **Script errors**: Show the error message and suggest fixes
- **Timeout**: Large apps may need increased timeout (default 30s)

## Safety

- Read-only operations only
- No database modifications
- No file writes
- Safe to run in any environment (dev/test/prod)

## Examples

### Inspect before adding a feature
```
User: "I want to add comments to posts"
Claude: Let me check the current schema first.
/rails-inspect models Post User
```

### Verify routes before adding controller
```
User: "Add an admin dashboard"
Claude: Checking existing admin routes.
/rails-inspect routes admin
```

### Full application overview
```
User: "What does this app do?"
Claude: Let me inspect the application.
/rails-inspect environment
/rails-inspect schema
/rails-inspect routes
```
