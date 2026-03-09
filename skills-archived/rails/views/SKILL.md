---
name: rails-views
description: Create Rails views, partials, layouts, and view helpers following ERB best practices
user_invocable: true
arguments: "action resource/template [options]"
---

# Rails Views Skill

Generate ERB templates, partials, layouts, and view helpers following Rails conventions and accessibility best practices.

## Usage

```
/rails-views create posts/index
/rails-views create posts/_post --partial
/rails-views create posts/_form --form
/rails-views create shared/_navbar
/rails-views layout admin
/rails-views helper posts
```

## Supported Actions

### create
Create a new view template or partial.

```
/rails-views create resource/template [options]
```

**Options:**
- `--partial` - Create as partial (prefixed with _)
- `--form` - Create form partial with form builder
- `--collection` - Create collection partial

### layout
Create a new layout file.

```
/rails-views layout name
```

### helper
Create view helper module.

```
/rails-views helper resource
```

## View Patterns

### Index View with Collection

```erb
<%# app/views/posts/index.html.erb %>
<div class="container mx-auto px-4 py-8">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold text-slate-900">Posts</h1>
    <%= link_to "New Post", new_post_path, class: "btn-primary" %>
  </div>

  <% if @posts.any? %>
    <div id="posts" class="space-y-4">
      <%= render @posts %>
    </div>

    <div class="mt-6">
      <%== pagy_nav(@pagy) if @pagy.pages > 1 %>
    </div>
  <% else %>
    <%= render "shared/empty_state",
        icon: "document",
        title: "No posts yet",
        description: "Get started by creating your first post.",
        action_text: "Create Post",
        action_path: new_post_path %>
  <% end %>
</div>
```

### Show View

```erb
<%# app/views/posts/show.html.erb %>
<%= turbo_frame_tag @post do %>
  <article class="max-w-3xl mx-auto px-4 py-8">
    <header class="mb-8">
      <div class="flex items-center gap-2 text-sm text-slate-500 mb-2">
        <%= link_to @post.category.name, category_path(@post.category), class: "hover:text-primary-600" if @post.category %>
        <span>&middot;</span>
        <time datetime="<%= @post.published_at&.iso8601 %>">
          <%= @post.published_at&.strftime("%B %d, %Y") || "Draft" %>
        </time>
      </div>

      <h1 class="text-3xl font-bold text-slate-900 mb-4"><%= @post.title %></h1>

      <div class="flex items-center gap-3">
        <%= image_tag @post.user.avatar_url, class: "w-10 h-10 rounded-full", alt: @post.user.name %>
        <div>
          <div class="font-medium text-slate-900"><%= @post.user.name %></div>
          <div class="text-sm text-slate-500"><%= @post.user.title %></div>
        </div>
      </div>
    </header>

    <div class="prose prose-slate max-w-none">
      <%= simple_format(@post.body) %>
    </div>

    <footer class="mt-8 pt-8 border-t border-slate-200">
      <div class="flex flex-wrap gap-2">
        <% @post.tags.each do |tag| %>
          <%= link_to tag.name, tag_path(tag), class: "px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-sm hover:bg-slate-200" %>
        <% end %>
      </div>

      <% if policy(@post).edit? %>
        <div class="mt-6 flex gap-3">
          <%= link_to "Edit", edit_post_path(@post), class: "btn-secondary" %>
          <%= button_to "Delete", @post, method: :delete, class: "btn-danger",
              data: { turbo_confirm: "Are you sure you want to delete this post?" } %>
        </div>
      <% end %>
    </footer>
  </article>
<% end %>

<section class="max-w-3xl mx-auto px-4 py-8">
  <h2 class="text-xl font-bold text-slate-900 mb-6">
    Comments (<span id="comments_count"><%= @post.comments.count %></span>)
  </h2>

  <%= turbo_stream_from @post, :comments %>

  <div id="comments" class="space-y-6">
    <%= render @post.comments.includes(:user).order(created_at: :desc) %>
  </div>

  <div id="new_comment" class="mt-8">
    <%= render "comments/form", comment: Comment.new(post: @post) %>
  </div>
</section>
```

### Form Partial

```erb
<%# app/views/posts/_form.html.erb %>
<%= form_with model: post, class: "space-y-6", data: { controller: "form-validation" } do |f| %>
  <% if post.errors.any? %>
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <h3 class="text-red-800 font-medium mb-2">
        <%= pluralize(post.errors.count, "error") %> prevented this post from being saved:
      </h3>
      <ul class="list-disc list-inside text-red-700 text-sm">
        <% post.errors.full_messages.each do |message| %>
          <li><%= message %></li>
        <% end %>
      </ul>
    </div>
  <% end %>

  <div class="form-group">
    <%= f.label :title, class: "form-label" %>
    <%= f.text_field :title, class: "form-input", required: true,
        data: { form_validation_target: "field", action: "blur->form-validation#validate" } %>
  </div>

  <div class="form-group">
    <%= f.label :category_id, class: "form-label" %>
    <%= f.collection_select :category_id, Category.ordered, :id, :name,
        { prompt: "Select a category" },
        { class: "form-select" } %>
  </div>

  <div class="form-group">
    <%= f.label :body, class: "form-label" %>
    <%= f.text_area :body, class: "form-textarea", rows: 10, required: true %>
  </div>

  <div class="form-group">
    <%= f.label :tags, class: "form-label" %>
    <%= f.collection_check_boxes :tag_ids, Tag.alphabetical, :id, :name do |b| %>
      <label class="inline-flex items-center mr-4 mb-2">
        <%= b.check_box class: "form-input-checkbox" %>
        <span class="ml-2 text-sm text-slate-700"><%= b.text %></span>
      </label>
    <% end %>
  </div>

  <div class="form-group">
    <%= f.label :status, class: "form-label" %>
    <div class="flex gap-4">
      <% Post.statuses.keys.each do |status| %>
        <label class="inline-flex items-center">
          <%= f.radio_button :status, status, class: "form-input-radio" %>
          <span class="ml-2 text-sm text-slate-700"><%= status.titleize %></span>
        </label>
      <% end %>
    </div>
  </div>

  <div class="flex justify-end gap-3 pt-4 border-t border-slate-200">
    <%= link_to "Cancel", posts_path, class: "btn-secondary" %>
    <%= f.submit class: "btn-primary", data: { form_validation_target: "submit" } %>
  </div>
<% end %>
```

### Collection Partial

```erb
<%# app/views/posts/_post.html.erb %>
<%= turbo_frame_tag post do %>
  <article
    class="bg-white rounded-lg border border-slate-200 p-6 hover:border-slate-300 transition-colors"
    data-controller="post-card"
  >
    <div class="flex justify-between items-start">
      <div class="flex-1">
        <div class="flex items-center gap-2 text-sm text-slate-500 mb-2">
          <% if post.category %>
            <span class="text-primary-600"><%= post.category.name %></span>
            <span>&middot;</span>
          <% end %>
          <time datetime="<%= post.created_at.iso8601 %>">
            <%= time_ago_in_words(post.created_at) %> ago
          </time>
        </div>

        <%= link_to post_path(post), class: "block group" do %>
          <h2 class="text-lg font-semibold text-slate-900 group-hover:text-primary-600 mb-2">
            <%= post.title %>
          </h2>
        <% end %>

        <p class="text-slate-600 line-clamp-2 mb-4">
          <%= truncate(post.body, length: 160) %>
        </p>

        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <%= image_tag post.user.avatar_url, class: "w-6 h-6 rounded-full", alt: "" %>
            <span class="text-sm text-slate-700"><%= post.user.name %></span>
          </div>

          <% if post.tags.any? %>
            <div class="flex gap-1">
              <% post.tags.limit(3).each do |tag| %>
                <span class="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">
                  <%= tag.name %>
                </span>
              <% end %>
            </div>
          <% end %>
        </div>
      </div>

      <% if policy(post).edit? %>
        <div class="relative" data-controller="dropdown">
          <button
            type="button"
            class="p-2 hover:bg-slate-100 rounded-lg"
            data-action="click->dropdown#toggle"
          >
            <svg class="w-5 h-5 text-slate-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
            </svg>
          </button>

          <div
            data-dropdown-target="menu"
            class="hidden absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-10"
          >
            <%= link_to "Edit", edit_post_path(post), class: "block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50" %>
            <%= button_to "Delete", post, method: :delete, class: "block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50",
                data: { turbo_confirm: "Delete this post?" } %>
          </div>
        </div>
      <% end %>
    </div>
  </article>
<% end %>
```

### Empty State Partial

```erb
<%# app/views/shared/_empty_state.html.erb %>
<%# locals: (icon:, title:, description:, action_text: nil, action_path: nil) %>
<div class="text-center py-12">
  <div class="mx-auto w-12 h-12 text-slate-400 mb-4">
    <%= render "shared/icons/#{icon}" %>
  </div>
  <h3 class="text-lg font-medium text-slate-900 mb-2"><%= title %></h3>
  <p class="text-slate-500 mb-6 max-w-sm mx-auto"><%= description %></p>
  <% if action_text && action_path %>
    <%= link_to action_text, action_path, class: "btn-primary" %>
  <% end %>
</div>
```

### Layout

```erb
<%# app/views/layouts/application.html.erb %>
<!DOCTYPE html>
<html lang="<%= I18n.locale %>" class="h-full">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="csrf-token" content="<%= csrf_meta_tags %>">

    <title><%= content_for(:title) || "App Name" %></title>

    <%= csp_meta_tag %>
    <%= stylesheet_link_tag "application", data: { turbo_track: "reload" } %>
    <%= javascript_include_tag "application", "data-turbo-track": "reload", type: "module" %>
  </head>

  <body class="h-full bg-slate-50">
    <%= render "shared/navbar" %>

    <main class="min-h-screen">
      <div id="flash" class="container mx-auto px-4 pt-4">
        <%= render "shared/flash" %>
      </div>

      <%= yield %>
    </main>

    <%= render "shared/footer" %>
  </body>
</html>
```

### Flash Messages Partial

```erb
<%# app/views/shared/_flash.html.erb %>
<% flash.each do |type, message| %>
  <% alert_class = case type.to_sym
     when :notice, :success then "bg-green-50 border-green-200 text-green-800"
     when :alert, :error then "bg-red-50 border-red-200 text-red-800"
     else "bg-blue-50 border-blue-200 text-blue-800"
     end %>

  <div
    class="<%= alert_class %> border rounded-lg p-4 mb-4 flex justify-between items-center"
    data-controller="alert"
    data-alert-dismiss-after-value="5000"
  >
    <p><%= message %></p>
    <button
      type="button"
      class="ml-4 hover:opacity-75"
      data-action="click->alert#dismiss"
    >
      <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
    </button>
  </div>
<% end %>
```

## View Helpers

```ruby
# app/helpers/posts_helper.rb
module PostsHelper
  def post_status_badge(post)
    classes = case post.status
              when "published" then "bg-green-100 text-green-800"
              when "draft" then "bg-yellow-100 text-yellow-800"
              when "archived" then "bg-slate-100 text-slate-800"
              end

    content_tag :span, post.status.titleize,
      class: "px-2 py-1 text-xs font-medium rounded-full #{classes}"
  end

  def reading_time(text)
    words_per_minute = 200
    words = text.to_s.split.size
    minutes = (words / words_per_minute.to_f).ceil

    "#{minutes} min read"
  end
end
```

## Safety Rules

1. **Escape Output** - Use `<%=` (escaped) not `<%==` (unescaped) unless intentional
2. **No Logic** - Keep business logic in models/services
3. **Partials** - Extract reusable components
4. **Accessibility** - Include ARIA labels, semantic HTML
5. **Performance** - Use collection rendering, fragment caching
