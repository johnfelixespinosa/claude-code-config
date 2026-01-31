# CLAUDE.md - Comprehensive Development Guide

This file provides guidance to Claude Code when working with this repository. It synthesizes best practices, patterns, and conventions from the entire codebase.

**You are a staff software engineer specialized in building highly-scalable and maintainable systems.**

---

## Table of Contents

1. [Critical Rules](#critical-rules)
2. [Architecture Overview](#architecture-overview)
3. [Rails Conventions](#rails-conventions)
4. [Background Jobs](#background-jobs)
5. [State Machines](#state-machines)
6. [Frontend Development](#frontend-development)
7. [React Components](#react-components)
8. [UI Standards](#ui-standards)
9. [Testing](#testing)
10. [Debugging](#debugging)
11. [Deployment](#deployment)
12. [Gold Standard Patterns](#gold-standard-patterns)
13. [Custom Skills](#custom-skills)

---

## Critical Rules

### Absolute Rules
- **NEVER commit** unless explicitly asked
- **NEVER create files** unless absolutely necessary - ALWAYS prefer editing existing files
- **NEVER proactively create documentation files** (*.md) unless explicitly requested
- **Run tests** after changes; use `rubocop` before code complete
- **Do not remove comments** unless explicitly instructed
- **Do what's asked; nothing more, nothing less**

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

## Architecture Overview

### Technology Stack
- **Backend**: Rails 8 with PostgreSQL
- **Frontend**: Stimulus + Turbo for SPA-like navigation, React for complex UI (PDF viewer)
- **Real-time**: ActionCable via Solid Cable
- **Background Jobs**: Solid Queue with Mission Control UI at `/jobs`
- **File Storage**: AWS S3 via Active Storage
- **Deployment**: Kamal on Digital Ocean

### Multi-Database Architecture
- **Primary**: Core application data
- **Queue**: Solid Queue jobs (`db/queue_migrate`)
- **Cache**: Solid Cache
- **Cable**: WebSocket/ActionCable


## Rails Conventions

### Enums (Project-Specific Syntax)

```ruby
# CORRECT syntax (Rails 8)
enum :status_name, {
  value1: "value1",
  value2: "value2"
}

# WRONG - causes "wrong number of arguments" errors
enum status_name: { value1: "value1" }
```

### Migrations

```ruby
# Version 8.0 format
class CreateTableName < ActiveRecord::Migration[8.0]
  def change
    # UUID primary keys (standard for this project)
    create_table :table_name, id: :uuid do |t|
      # UUID references
      t.references :model, type: :uuid, foreign_key: true

      # String status fields for state machines
      t.string :status, null: false, default: 'initial'

      # JSONB for flexible metadata
      t.jsonb :metadata, default: {}
      t.jsonb :pipeline_state, default: {}

      t.timestamps
    end

    add_index :table_name, :status
  end
end
```

**Important**:
- Requires `enable_extension 'pgcrypto'` for UUID support
- Use real timestamps (YYYYMMDDHHMMSS), never placeholders

### Controller Patterns

```ruby
# Thin controller pattern - delegate to services
class ExampleController < ApplicationController
  def create
    result = ExampleService.call(params)

    if result.success?
      redirect_to result.resource, notice: "Created successfully"
    else
      flash.now[:alert] = result.errors.join(", ")
      render :new
    end
  end
end
```

### Service Object Pattern

```ruby
class ExampleService
  def self.call(*args)
    new(*args).call
  end

  def initialize(params)
    @params = params
  end

  def call
    # Business logic here
    Result.new(success: true, resource: resource)
  rescue => e
    Result.new(success: false, errors: [e.message])
  end

  Result = Struct.new(:success, :resource, :errors, keyword_init: true) do
    alias_method :success?, :success
  end
end
```

---

## Background Jobs

### Core Principles
- All jobs must be **idempotent** for retry safety
- Use `perform_later` for async processing
- Pipeline jobs use PostgreSQL advisory locks to prevent concurrent processing
- Failed jobs visible in Mission Control UI at `/jobs`

### Job Base Classes

```ruby
# Standard job
class ExampleJob < ApplicationJob
  queue_as :default

  retry_on StandardError, wait: :exponentially_longer, attempts: 3
  retry_on Net::ReadTimeout, wait: 30.seconds, attempts: 5

  def perform(resource_id)
    resource = Resource.find(resource_id)
    # Job logic
  end
end

# Idempotent job (for analysis jobs that shouldn't run twice)
class Pipeline::AnalysisJob < Pipeline::IdempotentJob
  def generate_job_key
    "#{self.class.name}:#{arguments.join(':')}"
  end

  def perform(chunk_id, chunk_count, chunk_index)
    perform_with_idempotency(chunk_id) do
      # Analysis logic
    end
  end
end
```

### Orchestrator Pattern

```ruby
class Pipeline::OrchestratorJob < ApplicationJob
  def perform(revision_id, completed_job_type = nil)
    revision = Revision.find(revision_id)

    # PostgreSQL advisory lock prevents concurrent runs
    lock_key = "orchestrator_#{revision_id}".hash

    ActiveRecord::Base.transaction do
      unless acquire_advisory_lock(lock_key)
        Rails.logger.info "Orchestrator already running"
        return
      end

      # Determine and schedule next action
      next_action = determine_next_action(revision)
      schedule_next_job(revision, next_action)
    end
  end
end
```

### Pipeline State Management

```ruby
# Mark job complete and notify orchestrator
PipelineStateManager.complete_job_and_check_progress(
  revision_id,
  'job_type_name',
  required_jobs: ['other_job']
)

# Advisory lock wrapper for atomic state updates
def with_content_lock(content_id)
  lock_key = "content_pipeline_#{content_id}".hash

  Content.transaction do
    ActiveRecord::Base.connection.execute(
      "SELECT pg_advisory_xact_lock(#{lock_key})"
    )
    content = Content.find(content_id)
    yield(content)
  end
end
```

### Queue Configuration

```yaml
# config/solid_queue.yml
production:
  dispatchers:
    - polling_interval: 0.5
      batch_size: 1000
  workers:
    - queues: [default, api_calls, notifications, captures]
      threads: 5
      processes: 2
    - queues: [ai_analysis, annotations]
      threads: 6
      processes: 2
```

### Error Handling Pattern

```ruby
def perform(revision_id)
  @revision = Revision.find(revision_id)

  # State guard - check before executing
  return unless @revision.analyzing?

  # Job logic here

rescue => e
  Rails.logger.error "Job failed for Revision #{@revision.id}: #{e.message}"
  Rails.logger.error e.backtrace.first(5).join("\n")
  @revision.update!(processing_status: :failed)
  raise  # Let Solid Queue handle retry/Honeybadger catch it
end
```

---

## State Machines

### AASM State Machine Pattern

```ruby
module ContentStateMachine
  extend ActiveSupport::Concern

  included do
    include AASM

    aasm column: :status do
      # Pipeline states
      state :initial, initial: true
      state :uploading
      state :converting
      state :chunking
      state :analyzing
      state :annotating

      # Review states
      state :open
      state :changes_requested
      state :approved
      state :complete

      # Terminal states
      state :failed
      state :archived

      # Pipeline events
      event :start_upload do
        transitions from: :initial, to: :uploading
      end

      # Review events
      event :request_changes do
        transitions from: :open, to: :changes_requested
      end

      event :approve do
        transitions from: [:open, :changes_requested], to: :approved
      end
    end
  end
end
```

### Best Practices
- Always check transitions before executing: `resource.may_approve?`
- Use state services for review updates, not manual state changes
- All transitions are logged via content_events for audit trail
- Check `processing_status` for pipeline, `review_status` for workflow

---

## Frontend Development

### Stimulus Controllers

```javascript
// app/javascript/controllers/example_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["button", "menu", "selected"]
  static values = {
    open: { type: Boolean, default: false }
  }

  connect() {
    this.close()
  }

  toggle() {
    this.openValue = !this.openValue
  }

  select(event) {
    const value = event.currentTarget.dataset.value
    this.selectedTarget.textContent = value
    this.close()
  }

  close() {
    this.openValue = false
  }

  openValueChanged() {
    this.menuTarget.classList.toggle("hidden", !this.openValue)
    this.buttonTarget.setAttribute("aria-expanded", this.openValue)
  }
}
```

### Stimulus Guidelines
- Register controllers in `app/javascript/controllers/index.js`
- Use kebab-case for controller names (e.g., `modal-dropdown`)
- Use descriptive target names that reflect their purpose
- Use values for state management instead of class toggling
- Always update ARIA attributes for accessibility

---

## React Components

### Structure

```
component_name/
  index.tsx          # Entry point, mounts from data attributes
  ComponentName.tsx  # Primary component
  hooks/             # Custom hooks (useXxxQuery for data fetching)
  api/               # API client functions with CSRF handling
  stores/            # Zustand stores with selector hooks
  types.ts           # TypeScript interfaces
```

### Zustand Store Pattern

```typescript
// stores/panel.store.ts
import { create } from 'zustand'

interface PanelStore {
  activePanel: string
  setActivePanel: (panel: string) => void
}

export const usePanelStore = create<PanelStore>((set) => ({
  activePanel: 'issues',
  setActivePanel: (panel) => set({ activePanel: panel }),
}))

// Export selector hooks (prevents unnecessary re-renders)
export const useActivePanel = () => usePanelStore((state) => state.activePanel)
```

### API Client Pattern

```typescript
// api/violations.api.ts
const getCsrfToken = (): string =>
  document.querySelector("meta[name='csrf-token']")?.getAttribute("content") || ""

export const fetchViolations = async (revisionId: string) => {
  const response = await fetch(`/api/revisions/${revisionId}/violations`, {
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'X-CSRF-Token': getCsrfToken(),
    },
  })
  return response.json()
}
```

### React Query with Polling

```typescript
const { data, isLoading } = useQuery({
  queryKey: ['violations', revisionId],
  queryFn: () => fetchViolations(revisionId),
  refetchInterval: (query) => {
    const processing = ['initial', 'uploading', 'chunking', 'analyzing']
    return processing.includes(status) ? 10000 : false
  }
})
```

### Optimistic Updates

```typescript
onMutate: async (newData) => {
  await queryClient.cancelQueries({ queryKey })
  const snapshot = queryClient.getQueryData(queryKey)
  queryClient.setQueryData(queryKey, optimisticData)
  return { snapshot }
},
onError: (err, vars, context) => {
  queryClient.setQueryData(queryKey, context?.snapshot)
},
onSettled: () => queryClient.invalidateQueries({ queryKey })
```

---

## UI Standards

### Button Classes (RailsUI)

```html
<!-- Primary -->
<button class="btn-primary">Primary Button</button>

<!-- Secondary -->
<button class="btn-secondary">Secondary Button</button>

<!-- Danger -->
<button class="btn-danger">Danger Button</button>

<!-- Sizes -->
<button class="btn-primary btn-sm">Small</button>
<button class="btn-primary btn-lg">Large</button>
```

### Form Elements

```html
<div class="form-group">
  <label class="form-label">Label</label>
  <input type="text" class="form-input" placeholder="Enter text..." />
</div>

<select class="form-select">
  <option>Option 1</option>
</select>

<textarea class="form-textarea"></textarea>

<input type="checkbox" class="form-input-checkbox" />
<input type="radio" class="form-input-radio" />
<input type="checkbox" class="form-input-switch" />
```

### Dropdown Pattern (Standard)

```html
<div class="relative" data-controller="railsui-dropdown">
  <button
    type="button"
    data-action="click->railsui-dropdown#toggle click@window->railsui-dropdown#hide"
    class="input-standard appearance-none text-left cursor-pointer relative"
  >
    <span class="text-gray-900">Selected Option</span>
    <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-4">
      <svg class="h-4 w-4 text-gray-600" fill="none" viewBox="0 0 20 20" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M6 8l4 4 4-4" />
      </svg>
    </span>
  </button>

  <ul
    data-railsui-dropdown-target="menu"
    class="hidden absolute top-full mt-2 left-0 border border-gray-300/70 dropdown-menu bg-white rounded-md shadow-lg py-1 z-50 w-full"
  >
    <li>
      <a href="#" class="dropdown-item">Option 1</a>
    </li>
  </ul>
</div>
```

### Table Pattern (Standard)

```html
<div class="mt-2 hidden sm:block">
  <div class="inline-block min-w-full border border-gray-200 rounded-lg align-middle overflow-hidden">
    <table class="min-w-full">
      <thead>
        <tr class="h-8 whitespace-nowrap">
          <th class="border-b border-slate-200 bg-slate-50 px-6 py-3 text-left text-2xs font-semibold uppercase tracking-wider text-slate-500" scope="col">
            Column Name
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100 bg-white">
        <tr data-controller="table-row" data-action="click->table-row#show">
          <td class="whitespace-nowrap px-6 py-3 text-xs text-left text-gray-700 font-normal">
            Cell content
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

### Empty State Pattern

```erb
<%= render "shared/empty_state",
    icon: '<svg>...</svg>',
    title: "No records found",
    description: "Get started by creating a new record.",
    button_text: "Create New",
    button_url: new_record_path %>
```

### Tab Navigation

```erb
<%
  active_class = "border-b-2 border-primary-500 px-4 py-3 text-primary-500 font-semibold text-base"
  inactive_class = "text-slate-400 font-semibold px-4 py-3 border-b-2 border-transparent text-[15px]"
%>

<ul class="flex items-center border-b border-gray-200/80 mb-6">
  <li><%= link_to "Tab 1", path1, class: active_tab == "tab1" ? active_class : inactive_class %></li>
  <li><%= link_to "Tab 2", path2, class: active_tab == "tab2" ? active_class : inactive_class %></li>
</ul>
```

### Color Guidelines
- Use `slate` colors for neutral UI elements (not `gray`)
- `slate-400` for inactive tabs and secondary text
- `slate-500` for table headers
- `slate-700` for form labels
- `primary-500`/`primary-600` for active states and buttons

---

## Testing

### Framework
- **Minitest** for Ruby tests
- Always run relevant tests after making changes

### Test Commands

```bash
# Run all tests
bundle exec rails test

# Run specific test file
bundle exec rails test test/models/revision_test.rb

# Run specific test
bundle exec rails test test/models/revision_test.rb:42
```

### Monitoring
- **Mission Control UI**: `/jobs` for Solid Queue status
- **Rails Logs**: Check for pipeline progression
- **Honeybadger**: Error monitoring and alerting

---

## Deployment

### Commands

```bash
# Deploy to production
kamal deploy

# Deploy to staging
kamal deploy --destination=staging

# Run migrations
kamal app exec --primary -i './bin/rails db:migrate'
kamal app exec --primary -i './bin/rails db:migrate' --destination=staging

# Connect to database
kamal dbc

# Rails console
kamal app exec --interactive --reuse "bin/rails console"

# View logs
kamal app logs -f
kamal app logs --destination=staging -f
```

### CI/CD Workflow
1. Create feature branch from `main` (use Linear ticket ID: `feature/LUT-XXX/description`)
2. Create PR to `staging` branch for testing
3. After successful staging tests, create PR to `main` for production
4. Merges trigger automatic deployments

---

## Guidelines for Code Changes

### When Writing Code
1. Read existing code before suggesting modifications
2. Follow existing patterns in the codebase
3. Keep solutions simple and focused
4. Run tests and rubocop before completing

### When Files Get Long
- Split into smaller, focused files
- Extract functions when they become too long
- Consider scalability and maintainability

### PRD Handling
- If provided markdown files, use as reference for structure
- Do not update PRD files unless explicitly asked

---

## Custom Skills

Use `/skill-name` to invoke these specialized workflows:

| Skill | Description |
|-------|-------------|
| `/nanobanana` | Generate, edit, and restore images using Gemini CLI with the Nano Banana extension |
| `/rails-architect` | Plan and orchestrate Rails feature implementation by analyzing requirements |
| `/rails-inspect` | Inspect Rails application runtime state - schema, routes, models, associations |
| `/rails-models` | Create and modify ActiveRecord models with Rails conventions |
| `/sandi-metz-rules` | Apply Sandi Metz's four rules for maintainable Ruby code |
| `/skill-creator` | Guide for creating new custom skills |
| `/super-research` | Generate implementation plans by consulting multiple AI models (Gemini Pro, GPT-5, O3) |

---

## User Preferences

@~/.claude/CLAUDE.md
