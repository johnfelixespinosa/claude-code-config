---
name: rails-frontend
description: Create Stimulus controllers, Turbo patterns, and React components following project conventions
user_invocable: true
arguments: "action name [options]"
---

# Rails Frontend Skill

Generate frontend components following project conventions: Stimulus + Turbo for SPA-like navigation, React + TypeScript + Zustand for complex interactive UIs.

## Usage

```
/rails-frontend stimulus dropdown
/rails-frontend stimulus modal --with-animation
/rails-frontend turbo-frame posts/show --lazy
/rails-frontend turbo-stream comments/create
/rails-frontend react ViolationsPanel
/rails-frontend react-store tabs
/rails-frontend react-api violations
```

## When to Use What

| Pattern | Use Case | Example |
|---------|----------|---------|
| Stimulus | Simple interactivity, dropdowns, modals, form validation | Navigation menus, accordions |
| Turbo Frame | Partial page updates, lazy loading | Comment sections, inline editing |
| Turbo Stream | Real-time DOM updates | Live notifications, chat |
| React | Complex interactive UIs with heavy state | PDF viewers, data grids, dashboards |

## Stimulus Patterns

### Basic Controller

```javascript
// app/javascript/controllers/dropdown_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["menu", "button", "selected"]
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

  closeOnClickOutside(event) {
    if (!this.element.contains(event.target)) {
      this.close()
    }
  }
}
```

### Standard Dropdown (RailsUI Pattern)

```erb
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
    <li><a href="#" class="dropdown-item">Option 1</a></li>
  </ul>
</div>
```

### Modal Controller

```javascript
// app/javascript/controllers/modal_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["dialog", "backdrop"]
  static values = {
    open: { type: Boolean, default: false }
  }

  connect() {
    this.boundKeydown = this.handleKeydown.bind(this)
    document.addEventListener("keydown", this.boundKeydown)
  }

  disconnect() {
    document.removeEventListener("keydown", this.boundKeydown)
  }

  open() {
    this.openValue = true
    document.body.classList.add("overflow-hidden")
  }

  close() {
    this.openValue = false
    document.body.classList.remove("overflow-hidden")
  }

  openValueChanged() {
    if (this.openValue) {
      this.dialogTarget.classList.remove("hidden")
      this.backdropTarget.classList.remove("hidden")
      this.dialogTarget.querySelector("input, button")?.focus()
    } else {
      this.dialogTarget.classList.add("hidden")
      this.backdropTarget.classList.add("hidden")
    }
  }

  handleKeydown(event) {
    if (event.key === "Escape" && this.openValue) {
      this.close()
    }
  }

  closeOnBackdrop(event) {
    if (event.target === this.backdropTarget) {
      this.close()
    }
  }
}
```

### Stimulus Guidelines

- Register controllers in `app/javascript/controllers/index.js`
- Use kebab-case for controller names (e.g., `modal-dropdown`)
- Use descriptive target names that reflect their purpose
- Use values for state management instead of class toggling
- Always update ARIA attributes for accessibility

## Turbo Patterns

### Turbo Frame (Lazy Loading)

```erb
<%# Lazy load comments %>
<%= turbo_frame_tag "comments", src: post_comments_path(@post), loading: :lazy do %>
  <div class="animate-pulse">Loading comments...</div>
<% end %>
```

### Turbo Frame (Inline Editing)

```erb
<%# app/views/posts/show.html.erb %>
<%= turbo_frame_tag @post do %>
  <article>
    <h1><%= @post.title %></h1>
    <p><%= @post.body %></p>
    <%= link_to "Edit", edit_post_path(@post) %>
  </article>
<% end %>

<%# app/views/posts/edit.html.erb %>
<%= turbo_frame_tag @post do %>
  <%= render "form", post: @post %>
<% end %>
```

### Turbo Stream (Create)

```erb
<%# app/views/comments/create.turbo_stream.erb %>
<%= turbo_stream.prepend "comments" do %>
  <%= render @comment %>
<% end %>

<%= turbo_stream.update "comments_count", @post.comments.count %>

<%= turbo_stream.replace "new_comment" do %>
  <%= render "form", comment: Comment.new(post: @post) %>
<% end %>
```

### Turbo Stream (Controller)

```ruby
def create
  @comment = @post.comments.build(comment_params)
  @comment.user = current_user

  respond_to do |format|
    if @comment.save
      format.html { redirect_to @post, notice: "Comment added." }
      format.turbo_stream
    else
      format.html { render "posts/show", status: :unprocessable_entity }
      format.turbo_stream do
        render turbo_stream: turbo_stream.replace(
          "new_comment",
          partial: "form",
          locals: { comment: @comment }
        )
      end
    end
  end
end
```

### Broadcasting (Real-time)

```ruby
# app/models/comment.rb
class Comment < ApplicationRecord
  after_create_commit -> {
    broadcast_prepend_to(
      post,
      :comments,
      target: "comments",
      partial: "comments/comment"
    )
  }

  after_destroy_commit -> {
    broadcast_remove_to(post, :comments)
  }
end
```

```erb
<%# app/views/posts/show.html.erb %>
<%= turbo_stream_from @post, :comments %>

<div id="comments">
  <%= render @post.comments %>
</div>
```

## React Component Patterns

Use React for complex interactive UIs that require heavy state management.

### Component Structure

```
app/javascript/components/
  ComponentName/
    index.tsx          # Entry point, mounts from data attributes
    ComponentName.tsx  # Primary component
    hooks/             # Custom hooks (useXxxQuery for data fetching)
    api/               # API client functions with CSRF handling
    stores/            # Zustand stores with selector hooks
    types.ts           # TypeScript interfaces
```

### Entry Point (index.tsx)

```typescript
// app/javascript/components/ViolationsPanel/index.tsx
import React from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ViolationsPanel } from './ViolationsPanel'

const queryClient = new QueryClient()

document.addEventListener('turbo:load', () => {
  const container = document.getElementById('violations-panel')
  if (!container) return

  const revisionId = container.dataset.revisionId
  const status = container.dataset.status

  const root = createRoot(container)
  root.render(
    <QueryClientProvider client={queryClient}>
      <ViolationsPanel revisionId={revisionId} status={status} />
    </QueryClientProvider>
  )
})
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

export const updateViolation = async (id: string, data: Partial<Violation>) => {
  const response = await fetch(`/api/violations/${id}`, {
    method: 'PATCH',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'X-CSRF-Token': getCsrfToken(),
    },
    body: JSON.stringify(data),
  })
  return response.json()
}
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
export const useSetActivePanel = () => usePanelStore((state) => state.setActivePanel)
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
const mutation = useMutation({
  mutationFn: updateViolation,
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
})
```

### Types Definition

```typescript
// types.ts
export interface Violation {
  id: string
  type: 'error' | 'warning' | 'info'
  message: string
  location: {
    page: number
    x: number
    y: number
    width: number
    height: number
  }
  status: 'open' | 'resolved' | 'ignored'
  createdAt: string
}

export interface ViolationsPanelProps {
  revisionId: string
  status: string
}
```

### ERB Mount Point

```erb
<%# app/views/revisions/show.html.erb %>
<div
  id="violations-panel"
  data-revision-id="<%= @revision.id %>"
  data-status="<%= @revision.processing_status %>"
></div>
```

## File Locations

| Type | Location |
|------|----------|
| Stimulus Controllers | `app/javascript/controllers/` |
| React Components | `app/javascript/components/` |
| Turbo Streams | `app/views/[resource]/[action].turbo_stream.erb` |

## Safety Rules

1. **Progressive Enhancement** - Stimulus features should work without JS
2. **Accessibility** - Always include ARIA attributes
3. **No Inline JS** - Use data attributes and controllers
4. **Debounce** - Throttle frequent events (input, scroll)
5. **Cleanup** - Remove listeners in disconnect() / useEffect cleanup
6. **CSRF** - Always include CSRF token in API calls
7. **Type Safety** - Use TypeScript for React components
