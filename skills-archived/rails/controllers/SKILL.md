---
name: rails-controllers
description: Create and modify Rails controllers with RESTful patterns, strong parameters, and proper error handling
user_invocable: true
arguments: "action name [options]"
---

# Rails Controllers Skill

Generate and modify Rails controllers following RESTful conventions, with proper strong parameters, error handling, and authentication patterns.

## Usage

```
/rails-controllers create Posts
/rails-controllers create Admin::Users --namespace=admin
/rails-controllers add_action Posts publish --member
/rails-controllers add_action Posts search --collection
/rails-controllers create Api::V1::Posts --api
```

## Supported Actions

### create
Create a new controller with standard RESTful actions.

```
/rails-controllers create ControllerName [options]
```

**Options:**
- `--namespace=admin` - Create in namespace (Admin::UsersController)
- `--api` - Create API controller (inherits from Api::BaseController)
- `--actions=index,show,create` - Only include specific actions
- `--skip-views` - Don't generate view templates
- `--parent=BaseController` - Custom parent class

### add_action
Add a custom action to existing controller.

```
/rails-controllers add_action ControllerName action_name [--member|--collection]
```

- `--member` - Action operates on single resource (requires ID)
- `--collection` - Action operates on collection

### add_filter
Add before/after/around action filters.

```
/rails-controllers add_filter ControllerName filter_name --before --only=create,update
```

## Instructions

When this skill is invoked, follow these steps:

### Step 1: Inspect Current State

```bash
# Check existing controllers and routes
bin/rails runner ~/.claude/skills/rails-inspect/scripts/routes.rb [controller_name]

# Check if model exists for resource
bin/rails runner ~/.claude/skills/rails-inspect/scripts/models.rb [ModelName]
```

### Step 2: Determine Controller Type

| Type | Parent Class | Use Case |
|------|--------------|----------|
| Standard | ApplicationController | HTML views with Turbo |
| API | Api::BaseController | JSON API endpoints |
| Admin | Admin::BaseController | Admin namespace |

### Step 3: Generate Controller

Use Rails generator for new controllers:
```bash
bin/rails generate controller ControllerName action1 action2 --no-test-framework
```

Then customize with proper patterns.

### Step 4: Apply Conventions

## Controller Patterns

### Standard RESTful Controller

```ruby
class PostsController < ApplicationController
  before_action :set_post, only: [:show, :edit, :update, :destroy]
  before_action :authenticate_user!, except: [:index, :show]
  before_action :authorize_post!, only: [:edit, :update, :destroy]

  def index
    @posts = Post.published.recent.page(params[:page])
  end

  def show
  end

  def new
    @post = current_user.posts.build
  end

  def create
    @post = current_user.posts.build(post_params)

    if @post.save
      redirect_to @post, notice: "Post was successfully created."
    else
      render :new, status: :unprocessable_entity
    end
  end

  def edit
  end

  def update
    if @post.update(post_params)
      redirect_to @post, notice: "Post was successfully updated."
    else
      render :edit, status: :unprocessable_entity
    end
  end

  def destroy
    @post.destroy
    redirect_to posts_url, notice: "Post was successfully deleted."
  end

  private

  def set_post
    @post = Post.find(params[:id])
  end

  def post_params
    params.expect(post: [:title, :body, :category_id, :status, tag_ids: []])
  end

  def authorize_post!
    redirect_to posts_url, alert: "Not authorized" unless @post.user == current_user
  end
end
```

### API Controller

```ruby
module Api
  module V1
    class PostsController < Api::BaseController
      before_action :set_post, only: [:show, :update, :destroy]

      def index
        @posts = Post.published.recent
        @posts = @posts.page(params[:page]).per(params[:per_page] || 25)

        render json: {
          posts: @posts.as_json(include: [:category, :tags]),
          meta: pagination_meta(@posts)
        }
      end

      def show
        render json: @post.as_json(include: [:category, :tags, :user])
      end

      def create
        @post = current_user.posts.build(post_params)

        if @post.save
          render json: @post, status: :created
        else
          render json: { errors: @post.errors }, status: :unprocessable_entity
        end
      end

      def update
        if @post.update(post_params)
          render json: @post
        else
          render json: { errors: @post.errors }, status: :unprocessable_entity
        end
      end

      def destroy
        @post.destroy
        head :no_content
      end

      private

      def set_post
        @post = Post.find(params[:id])
      end

      def post_params
        params.expect(post: [:title, :body, :category_id, :status, tag_ids: []])
      end

      def pagination_meta(collection)
        {
          current_page: collection.current_page,
          total_pages: collection.total_pages,
          total_count: collection.total_count
        }
      end
    end
  end
end
```

### Api::BaseController Pattern

```ruby
module Api
  class BaseController < ActionController::API
    include ActionController::HttpAuthentication::Token::ControllerMethods

    before_action :authenticate_token!

    rescue_from ActiveRecord::RecordNotFound, with: :not_found
    rescue_from ActiveRecord::RecordInvalid, with: :unprocessable_entity
    rescue_from ActionController::ParameterMissing, with: :bad_request

    private

    def authenticate_token!
      authenticate_or_request_with_http_token do |token, options|
        @current_user = User.find_by(api_token: token)
      end
    end

    def current_user
      @current_user
    end

    def not_found(exception)
      render json: { error: "Not found" }, status: :not_found
    end

    def unprocessable_entity(exception)
      render json: { errors: exception.record.errors }, status: :unprocessable_entity
    end

    def bad_request(exception)
      render json: { error: exception.message }, status: :bad_request
    end
  end
end
```

## Strong Parameters (Rails 8)

```ruby
# Rails 8 syntax with params.expect
def post_params
  params.expect(post: [:title, :body, :status, tag_ids: []])
end

# Nested attributes
def order_params
  params.expect(order: [:customer_id, line_items_attributes: [[:product_id, :quantity]]])
end
```

## Routes

```ruby
# config/routes.rb

# Standard resources
resources :posts do
  member do
    post :publish
    post :archive
  end
  collection do
    get :search
    get :drafts
  end
end

# Nested resources (max 1 level deep)
resources :posts do
  resources :comments, only: [:create, :destroy]
end

# Namespaced
namespace :admin do
  resources :users
  resources :posts
end

# API versioning
namespace :api do
  namespace :v1 do
    resources :posts
  end
end
```

## Error Handling

```ruby
class ApplicationController < ActionController::Base
  rescue_from ActiveRecord::RecordNotFound, with: :not_found
  rescue_from ActionPolicy::Unauthorized, with: :forbidden

  private

  def not_found
    respond_to do |format|
      format.html { render "errors/not_found", status: :not_found }
      format.json { render json: { error: "Not found" }, status: :not_found }
    end
  end

  def forbidden
    respond_to do |format|
      format.html { redirect_to root_path, alert: "Not authorized" }
      format.json { render json: { error: "Forbidden" }, status: :forbidden }
    end
  end
end
```

## Turbo/Hotwire Patterns

```ruby
def create
  @post = current_user.posts.build(post_params)

  respond_to do |format|
    if @post.save
      format.html { redirect_to @post, notice: "Post created." }
      format.turbo_stream # renders create.turbo_stream.erb
    else
      format.html { render :new, status: :unprocessable_entity }
      format.turbo_stream { render turbo_stream: turbo_stream.replace("post_form", partial: "form", locals: { post: @post }) }
    end
  end
end
```

## Safety Rules

1. **ALWAYS** use strong parameters - never trust user input
2. **ALWAYS** add authentication checks where needed
3. **ALWAYS** add authorization checks for resource ownership
4. **NEVER** expose sensitive data in JSON responses
5. **PREFER** thin controllers - delegate to services/models

## Files Created

| Action | Files |
|--------|-------|
| create Posts | `app/controllers/posts_controller.rb`, views, routes |
| create Api::V1::Posts | `app/controllers/api/v1/posts_controller.rb`, routes |
| create Admin::Users | `app/controllers/admin/users_controller.rb`, views, routes |
