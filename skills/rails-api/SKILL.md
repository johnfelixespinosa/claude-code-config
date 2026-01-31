---
name: rails-api
description: Create API controllers, serializers, and endpoints with versioning, authentication, and proper error handling
user_invocable: true
arguments: "action resource [options]"
---

# Rails API Skill

Generate API endpoints with proper versioning, authentication, serialization, and error handling patterns.

## Usage

```
/rails-api create posts
/rails-api create users --auth
/rails-api serializer Post
/rails-api base-controller
/rails-api version v2
```

## Supported Actions

### create
Create API controller with standard CRUD actions.

```
/rails-api create resource [options]
```

**Options:**
- `--auth` - Require authentication
- `--version=v1` - API version (default: v1)
- `--actions=index,show` - Limit actions

### serializer
Create a serializer for a model.

```
/rails-api serializer ModelName
```

### base-controller
Create/update API base controller.

### version
Create new API version namespace.

## API Patterns

### Base Controller

```ruby
# app/controllers/api/base_controller.rb
module Api
  class BaseController < ActionController::API
    include ActionController::HttpAuthentication::Token::ControllerMethods

    before_action :authenticate_request!
    before_action :set_default_format

    rescue_from ActiveRecord::RecordNotFound, with: :not_found
    rescue_from ActiveRecord::RecordInvalid, with: :unprocessable_entity
    rescue_from ActionController::ParameterMissing, with: :bad_request
    rescue_from Api::AuthenticationError, with: :unauthorized
    rescue_from Api::AuthorizationError, with: :forbidden

    private

    def authenticate_request!
      authenticate_or_request_with_http_token do |token, _options|
        @current_user = User.find_by(api_token: token)
        raise Api::AuthenticationError unless @current_user
        @current_user
      end
    end

    attr_reader :current_user

    def set_default_format
      request.format = :json
    end

    # Error responses
    def not_found(exception = nil)
      render json: {
        error: "Not Found",
        message: exception&.message || "Resource not found"
      }, status: :not_found
    end

    def unauthorized(exception = nil)
      render json: {
        error: "Unauthorized",
        message: exception&.message || "Authentication required"
      }, status: :unauthorized
    end

    def forbidden(exception = nil)
      render json: {
        error: "Forbidden",
        message: exception&.message || "Access denied"
      }, status: :forbidden
    end

    def unprocessable_entity(exception)
      render json: {
        error: "Unprocessable Entity",
        message: "Validation failed",
        details: exception.record.errors.as_json
      }, status: :unprocessable_entity
    end

    def bad_request(exception)
      render json: {
        error: "Bad Request",
        message: exception.message
      }, status: :bad_request
    end

    # Pagination helpers
    def pagination_meta(collection)
      {
        current_page: collection.current_page,
        next_page: collection.next_page,
        prev_page: collection.prev_page,
        total_pages: collection.total_pages,
        total_count: collection.total_count
      }
    end

    def paginate(collection)
      collection.page(params[:page]).per(params[:per_page] || 25)
    end
  end

  class AuthenticationError < StandardError; end
  class AuthorizationError < StandardError; end
end
```

### Resource Controller

```ruby
# app/controllers/api/v1/posts_controller.rb
module Api
  module V1
    class PostsController < Api::BaseController
      before_action :set_post, only: [:show, :update, :destroy]
      before_action :authorize_post!, only: [:update, :destroy]

      # GET /api/v1/posts
      def index
        @posts = Post.published
                     .includes(:user, :category, :tags)
                     .order(published_at: :desc)

        @posts = @posts.where(category_id: params[:category_id]) if params[:category_id]
        @posts = @posts.tagged_with(params[:tag]) if params[:tag]
        @posts = paginate(@posts)

        render json: {
          data: @posts.map { |post| PostSerializer.new(post).as_json },
          meta: pagination_meta(@posts)
        }
      end

      # GET /api/v1/posts/:id
      def show
        render json: {
          data: PostSerializer.new(@post, include_details: true).as_json
        }
      end

      # POST /api/v1/posts
      def create
        @post = current_user.posts.build(post_params)

        if @post.save
          render json: {
            data: PostSerializer.new(@post).as_json
          }, status: :created, location: api_v1_post_url(@post)
        else
          render json: {
            error: "Unprocessable Entity",
            details: @post.errors.as_json
          }, status: :unprocessable_entity
        end
      end

      # PATCH/PUT /api/v1/posts/:id
      def update
        if @post.update(post_params)
          render json: {
            data: PostSerializer.new(@post).as_json
          }
        else
          render json: {
            error: "Unprocessable Entity",
            details: @post.errors.as_json
          }, status: :unprocessable_entity
        end
      end

      # DELETE /api/v1/posts/:id
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

      def authorize_post!
        raise Api::AuthorizationError unless @post.user == current_user
      end
    end
  end
end
```

### Serializer

```ruby
# app/serializers/post_serializer.rb
class PostSerializer
  def initialize(post, include_details: false)
    @post = post
    @include_details = include_details
  end

  def as_json
    data = {
      id: post.id,
      type: "post",
      attributes: attributes,
      relationships: relationships,
      links: links
    }

    data[:included] = included if include_details
    data
  end

  private

  attr_reader :post, :include_details

  def attributes
    {
      title: post.title,
      slug: post.slug,
      excerpt: post.body&.truncate(200),
      status: post.status,
      published_at: post.published_at&.iso8601,
      created_at: post.created_at.iso8601,
      updated_at: post.updated_at.iso8601
    }.tap do |attrs|
      attrs[:body] = post.body if include_details
    end
  end

  def relationships
    {
      author: {
        data: { type: "user", id: post.user_id }
      },
      category: post.category ? {
        data: { type: "category", id: post.category_id }
      } : nil,
      tags: {
        data: post.tags.map { |tag| { type: "tag", id: tag.id } }
      }
    }.compact
  end

  def links
    {
      self: "/api/v1/posts/#{post.id}"
    }
  end

  def included
    [
      UserSerializer.new(post.user).as_json,
      post.category ? CategorySerializer.new(post.category).as_json : nil,
      *post.tags.map { |tag| TagSerializer.new(tag).as_json }
    ].compact
  end
end
```

### JWT Authentication

```ruby
# app/controllers/api/v1/auth_controller.rb
module Api
  module V1
    class AuthController < Api::BaseController
      skip_before_action :authenticate_request!, only: [:login, :register]

      # POST /api/v1/auth/login
      def login
        user = User.find_by(email: params[:email])

        if user&.authenticate(params[:password])
          token = generate_jwt(user)
          render json: {
            data: {
              token: token,
              user: UserSerializer.new(user).as_json
            }
          }
        else
          render json: {
            error: "Unauthorized",
            message: "Invalid email or password"
          }, status: :unauthorized
        end
      end

      # POST /api/v1/auth/register
      def register
        user = User.new(user_params)

        if user.save
          token = generate_jwt(user)
          render json: {
            data: {
              token: token,
              user: UserSerializer.new(user).as_json
            }
          }, status: :created
        else
          render json: {
            error: "Unprocessable Entity",
            details: user.errors.as_json
          }, status: :unprocessable_entity
        end
      end

      # POST /api/v1/auth/refresh
      def refresh
        token = generate_jwt(current_user)
        render json: { data: { token: token } }
      end

      # DELETE /api/v1/auth/logout
      def logout
        # Invalidate token if using token blacklist
        head :no_content
      end

      private

      def user_params
        params.permit(:name, :email, :password, :password_confirmation)
      end

      def generate_jwt(user)
        payload = {
          user_id: user.id,
          exp: 24.hours.from_now.to_i
        }
        JWT.encode(payload, Rails.application.credentials.secret_key_base)
      end
    end
  end
end

# For JWT auth, update base controller:
# def authenticate_request!
#   token = request.headers["Authorization"]&.split(" ")&.last
#   payload = JWT.decode(token, Rails.application.credentials.secret_key_base).first
#   @current_user = User.find(payload["user_id"])
# rescue JWT::DecodeError, ActiveRecord::RecordNotFound
#   raise Api::AuthenticationError
# end
```

### Routes

```ruby
# config/routes.rb
namespace :api do
  namespace :v1 do
    # Auth
    post "auth/login", to: "auth#login"
    post "auth/register", to: "auth#register"
    post "auth/refresh", to: "auth#refresh"
    delete "auth/logout", to: "auth#logout"

    # Resources
    resources :posts do
      resources :comments, only: [:index, :create, :destroy]
    end
    resources :categories, only: [:index, :show]
    resources :tags, only: [:index, :show]
    resources :users, only: [:show, :update] do
      collection do
        get :me
      end
    end
  end

  # Version 2 (example)
  namespace :v2 do
    resources :posts
  end
end
```

### Error Response Format

```json
{
  "error": "Unprocessable Entity",
  "message": "Validation failed",
  "details": {
    "title": ["can't be blank"],
    "email": ["has already been taken", "is invalid"]
  }
}
```

### Success Response Format

```json
{
  "data": {
    "id": "uuid",
    "type": "post",
    "attributes": {
      "title": "Post Title",
      "body": "Content..."
    },
    "relationships": {
      "author": { "data": { "type": "user", "id": "uuid" } }
    },
    "links": {
      "self": "/api/v1/posts/uuid"
    }
  },
  "meta": {
    "current_page": 1,
    "total_pages": 10,
    "total_count": 100
  }
}
```

## Rate Limiting

```ruby
# app/controllers/api/base_controller.rb
class Api::BaseController < ActionController::API
  before_action :check_rate_limit

  private

  def check_rate_limit
    key = "rate_limit:#{current_user&.id || request.remote_ip}"
    count = Rails.cache.increment(key, 1, expires_in: 1.minute, initial: 0)

    if count > 100 # 100 requests per minute
      render json: {
        error: "Too Many Requests",
        message: "Rate limit exceeded. Please wait before making more requests."
      }, status: :too_many_requests
    end
  end
end
```

## Safety Rules

1. **Always authenticate** - Protect endpoints appropriately
2. **Validate input** - Use strong parameters
3. **Consistent errors** - Standard error format
4. **Version your API** - Use namespaces (v1, v2)
5. **Rate limit** - Prevent abuse
6. **No sensitive data** - Filter passwords, tokens from logs
