---
name: rails-architect
description: Plan and orchestrate Rails feature implementation by analyzing requirements and delegating to specialized skills
user_invocable: true
arguments: "feature description"
---

# Rails Architect Skill

The Architect is an orchestrator that plans Rails feature implementations and delegates work to specialized skills. It analyzes your request, inspects the current application state, creates an implementation plan, and executes it step-by-step.

## Usage

```
/rails-architect add user comments to blog posts
/rails-architect implement order checkout with payment processing
/rails-architect add admin dashboard for managing users
/rails-architect refactor authentication to use sessions
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     Rails Architect                          │
├─────────────────────────────────────────────────────────────┤
│  1. Analyze Request                                          │
│  2. Inspect Application State (via /rails-inspect)          │
│  3. Create Implementation Plan                               │
│  4. Execute Plan (delegate to skills)                        │
│  5. Verify & Summarize                                       │
└─────────────────────────────────────────────────────────────┘
                              │
    ┌───────────┬─────────────┼─────────────┬───────────┐
    ▼           ▼             ▼             ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ inspect │ │ models  │ │controllers│ │services │ │  jobs   │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
    ┌───────────┬─────────────┼─────────────┬───────────┐
    ▼           ▼             ▼             ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│frontend │ │  views  │ │   api   │ │  tests  │ │   ...   │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

## Instructions

When this skill is invoked, follow this workflow:

### Phase 1: Analyze the Request

Parse the feature description to identify:
- **Domain entities**: What models/tables are involved?
- **Relationships**: How do entities relate to each other?
- **Actions**: What CRUD operations are needed?
- **UI components**: Views, forms, navigation?
- **Background work**: Jobs, mailers, broadcasts?

**Example Analysis:**
```
Request: "add user comments to blog posts"

Entities: Comment (new), User (existing), Post (check if exists)
Relationships: Comment belongs_to User, Comment belongs_to Post
Actions: Create comment, list comments, delete comment
UI: Comment form, comments list partial
```

### Phase 2: Inspect Application State

**ALWAYS** run these inspections before planning:

```bash
# Get full picture of current state
bin/rails runner ~/.claude/skills/rails-inspect/scripts/environment.rb
bin/rails runner ~/.claude/skills/rails-inspect/scripts/schema.rb
bin/rails runner ~/.claude/skills/rails-inspect/scripts/models.rb
bin/rails runner ~/.claude/skills/rails-inspect/scripts/routes.rb
```

Use inspection results to:
- Verify assumptions (does Post model exist?)
- Detect existing patterns (UUID keys? String enums? Service objects?)
- Identify integration points (existing controllers, routes)
- Avoid conflicts (duplicate associations, tables)

### Phase 3: Create Implementation Plan

Structure the plan as an ordered list of steps:

```markdown
## Implementation Plan: [Feature Name]

### Overview
[2-3 sentence summary]

### Prerequisites
- [x] Post model exists
- [ ] User authentication in place

### Steps

#### Step 1: Create Comment Model
**Skill**: /rails-models create
**Command**:
```
/rails-models create Comment user:references post:references body:text
```
**Creates**:
- Migration: db/migrate/xxx_create_comments.rb
- Model: app/models/comment.rb

#### Step 2: Add Associations
**Skill**: /rails-models add_association
**Commands**:
```
/rails-models add_association Post has_many:comments dependent:destroy
/rails-models add_association User has_many:comments
```

#### Step 3: Add Validations
**Skill**: /rails-models add_validation
**Command**:
```
/rails-models add_validation Comment presence:body presence:user presence:post
```

[Continue with controllers, views, routes, tests...]

### Files to be Created/Modified
| File | Action | Description |
|------|--------|-------------|
| db/migrate/xxx_create_comments.rb | Create | Migration |
| app/models/comment.rb | Create | Model |
| app/models/post.rb | Modify | Add has_many |
| app/models/user.rb | Modify | Add has_many |

### Estimated Changes
- New files: 3
- Modified files: 2
- New routes: 4
- Database changes: 1 table, 2 indexes
```

### Phase 4: Execute Plan

Present the plan and ask for approval before executing.

For each step:
1. **Announce**: "Executing Step 1: Create Comment Model"
2. **Run**: Execute the skill command
3. **Verify**: Check the result
4. **Report**: Show what was created/modified
5. **Continue**: Move to next step

If a step fails:
- Stop execution
- Report the error
- Suggest fixes
- Ask how to proceed

### Phase 5: Verify & Summarize

After all steps complete:

1. **Run verification commands**:
```bash
bin/rails db:migrate:status
bin/rails routes | grep [relevant_pattern]
```

2. **Summarize changes**:
```markdown
## Implementation Complete

### Created
- Comment model with associations to User and Post
- Migration for comments table
- 4 RESTful routes for comments

### Modified
- Post model (added has_many :comments)
- User model (added has_many :comments)

### Next Steps
- [ ] Add comment form partial
- [ ] Add comments list to post show page
- [ ] Add system tests for commenting
- [ ] Consider adding real-time updates via Turbo Streams

### Commands to Test
```bash
bin/rails console
# Create a comment
Comment.create!(user: User.first, post: Post.first, body: "Test comment")
```
```

## Available Skills

The Architect can delegate to these skills:

| Skill | Purpose | Status |
|-------|---------|--------|
| `/rails-inspect` | Query application state (schema, models, routes) | ✅ Available |
| `/rails-models` | Create/modify ActiveRecord models | ✅ Available |
| `/rails-controllers` | Create RESTful and API controllers | ✅ Available |
| `/rails-services` | Create service objects for business logic | ✅ Available |
| `/rails-jobs` | Create background jobs with Solid Queue | ✅ Available |
| `/rails-frontend` | Create Stimulus controllers, Turbo patterns, and React components | ✅ Available |
| `/rails-views` | Create ERB views, partials, layouts | ✅ Available |
| `/rails-api` | Create API endpoints with serializers | ✅ Available |
| `/rails-tests` | Create tests (Minitest/RSpec) | ✅ Available |

All skills follow conventions from CLAUDE.md and use `/rails-inspect` for context.

## Conventions

The Architect enforces these conventions from CLAUDE.md:

### Database
- UUID primary keys: `id: :uuid`
- Foreign keys with UUID type: `t.references :user, type: :uuid`
- String-backed enums: `enum :status, { active: "active" }`
- JSONB for flexible data: `t.jsonb :metadata, default: {}`
- Always add indexes for foreign keys

### Code Style
- Thin controllers, fat models (but not too fat)
- Service objects for complex business logic
- Concerns for shared model behavior
- Strong parameters in controllers
- RESTful routes with standard 7 actions

### Rails 8 Specific
- Solid Queue for background jobs
- Solid Cache for caching
- Solid Cable for WebSocket
- Propshaft + esbuild (jsbundling-rails) for assets
- Turbo + Stimulus for SPA-like navigation
- React + TypeScript + Zustand for complex interactive UIs

## Example Session

```
User: /rails-architect add tagging system to posts

Architect: I'll implement a tagging system for posts. Let me first inspect the application.

[Runs /rails-inspect schema posts]
[Runs /rails-inspect models Post]

## Analysis
- Post model exists with standard columns
- Using UUID primary keys
- No existing tag-related tables

## Implementation Plan

### Step 1: Create Tag Model
/rails-models create Tag name:string:unique

### Step 2: Create Tagging Join Model
/rails-models create Tagging tag:references post:references

### Step 3: Add Associations
/rails-models add_association Tag has_many:taggings has_many:posts,through:taggings
/rails-models add_association Post has_many:taggings has_many:tags,through:taggings

### Step 4: Add Validations
/rails-models add_validation Tag presence:name uniqueness:name
/rails-models add_validation Tagging uniqueness:tag_id,scope:post_id

Shall I proceed with this plan?
```

## Safety

- **NEVER** execute destructive operations without confirmation
- **ALWAYS** show plan before executing
- **PAUSE** between major steps for verification
- **ROLLBACK** guidance if something goes wrong
- **BACKUP** recommendations for production data
