---
name: rails-tests
description: Create tests using Minitest or RSpec with proper patterns, factories, and coverage strategies
user_invocable: true
arguments: "action resource [options]"
---

# Rails Tests Skill

Generate tests following best practices with proper setup, assertions, and coverage for models, controllers, services, and system tests.

## Usage

```
/rails-tests model Post
/rails-tests controller Posts
/rails-tests service CreateOrder
/rails-tests system posts/create
/rails-tests request api/v1/posts
/rails-tests factory Post
```

## Supported Actions

### model
Create model tests.

```
/rails-tests model ModelName
```

### controller
Create controller tests.

```
/rails-tests controller ControllerName
```

### service
Create service object tests.

```
/rails-tests service ServiceName
```

### system
Create system/integration tests.

```
/rails-tests system feature_name
```

### request
Create API request tests.

```
/rails-tests request endpoint
```

### factory
Create FactoryBot factory.

```
/rails-tests factory ModelName
```

## Test Patterns (Minitest)

### Model Test

```ruby
# test/models/post_test.rb
require "test_helper"

class PostTest < ActiveSupport::TestCase
  # Associations
  test "belongs to user" do
    assoc = Post.reflect_on_association(:user)
    assert_equal :belongs_to, assoc.macro
  end

  test "belongs to category" do
    assoc = Post.reflect_on_association(:category)
    assert_equal :belongs_to, assoc.macro
    assert assoc.options[:optional]
  end

  test "has many tags through taggings" do
    post = posts(:published)
    assert_respond_to post, :tags
  end

  # Validations
  test "requires title" do
    post = Post.new(user: users(:john), body: "Content")
    assert_not post.valid?
    assert_includes post.errors[:title], "can't be blank"
  end

  test "requires unique slug" do
    existing = posts(:published)
    post = Post.new(
      user: users(:john),
      title: "Different Title",
      slug: existing.slug
    )
    assert_not post.valid?
    assert_includes post.errors[:slug], "has already been taken"
  end

  # Callbacks
  test "generates slug from title" do
    post = Post.new(user: users(:john), title: "My Great Post")
    post.valid?
    assert_equal "my-great-post", post.slug
  end

  test "sets published_at when publishing" do
    post = posts(:draft)
    assert_nil post.published_at

    post.published!
    assert_not_nil post.published_at
  end

  # Scopes
  test ".published returns only published posts" do
    assert_includes Post.published, posts(:published)
    assert_not_includes Post.published, posts(:draft)
  end

  test ".drafts returns only draft posts" do
    assert_includes Post.drafts, posts(:draft)
    assert_not_includes Post.drafts, posts(:published)
  end

  test ".recent orders by published_at desc" do
    posts = Post.published.recent
    assert_equal posts, posts.sort_by(&:published_at).reverse
  end

  # Enums
  test "status enum values" do
    assert_equal %w[draft published archived], Post.statuses.keys
  end

  # Instance methods
  test "#published? returns true for published posts" do
    assert posts(:published).published?
    assert_not posts(:draft).published?
  end
end
```

### Controller Test

```ruby
# test/controllers/posts_controller_test.rb
require "test_helper"

class PostsControllerTest < ActionDispatch::IntegrationTest
  setup do
    @user = users(:john)
    @post = posts(:published)
  end

  # Index
  test "should get index" do
    get posts_url
    assert_response :success
    assert_select "article", minimum: 1
  end

  test "index paginates results" do
    get posts_url, params: { page: 2 }
    assert_response :success
  end

  # Show
  test "should get show" do
    get post_url(@post)
    assert_response :success
    assert_select "h1", @post.title
  end

  test "show returns 404 for missing post" do
    get post_url(id: "nonexistent")
    assert_response :not_found
  end

  # New/Create (authenticated)
  test "should get new when authenticated" do
    sign_in @user
    get new_post_url
    assert_response :success
  end

  test "redirects new when not authenticated" do
    get new_post_url
    assert_redirected_to login_url
  end

  test "should create post" do
    sign_in @user

    assert_difference("Post.count") do
      post posts_url, params: {
        post: {
          title: "New Post",
          body: "Content here",
          status: "draft"
        }
      }
    end

    assert_redirected_to post_url(Post.last)
    assert_equal "New Post", Post.last.title
    assert_equal @user, Post.last.user
  end

  test "create with invalid params renders new" do
    sign_in @user

    assert_no_difference("Post.count") do
      post posts_url, params: { post: { title: "" } }
    end

    assert_response :unprocessable_entity
  end

  # Edit/Update
  test "should get edit for own post" do
    sign_in @user
    get edit_post_url(@post)
    assert_response :success
  end

  test "should update own post" do
    sign_in @user

    patch post_url(@post), params: {
      post: { title: "Updated Title" }
    }

    assert_redirected_to post_url(@post)
    @post.reload
    assert_equal "Updated Title", @post.title
  end

  # Destroy
  test "should destroy own post" do
    sign_in @user

    assert_difference("Post.count", -1) do
      delete post_url(@post)
    end

    assert_redirected_to posts_url
  end

  # Authorization
  test "cannot edit other user's post" do
    sign_in users(:jane)
    get edit_post_url(@post)
    assert_redirected_to posts_url
  end

  private

  def sign_in(user)
    post login_url, params: { email: user.email, password: "password" }
  end
end
```

### Service Test

```ruby
# test/services/create_order_test.rb
require "test_helper"

class CreateOrderTest < ActiveSupport::TestCase
  setup do
    @user = users(:john)
    @product = products(:widget)
    @cart = Cart.new(user: @user, items: [@product])
  end

  test "creates order successfully" do
    result = CreateOrder.call(user: @user, cart: @cart, payment_method: "card")

    assert result.is_a?(Order)
    assert result.persisted?
    assert_equal @user, result.user
    assert_equal "paid", result.status
  end

  test "creates order items" do
    assert_difference("OrderItem.count", 1) do
      CreateOrder.call(user: @user, cart: @cart, payment_method: "card")
    end
  end

  test "processes payment" do
    PaymentGateway.expects(:charge).with(
      amount: @cart.total_cents,
      customer_id: @user.stripe_customer_id
    ).returns(OpenStruct.new(id: "ch_123"))

    CreateOrder.call(user: @user, cart: @cart, payment_method: "card")
  end

  test "sends confirmation email" do
    assert_enqueued_email_with OrderMailer, :confirmation do
      CreateOrder.call(user: @user, cart: @cart, payment_method: "card")
    end
  end

  test "rolls back on payment failure" do
    PaymentGateway.stubs(:charge).raises(PaymentGateway::CardDeclined)

    assert_no_difference("Order.count") do
      assert_raises(CreateOrder::PaymentFailedError) do
        CreateOrder.call(user: @user, cart: @cart, payment_method: "card")
      end
    end
  end

  test "handles empty cart" do
    empty_cart = Cart.new(user: @user, items: [])

    assert_raises(CreateOrder::EmptyCartError) do
      CreateOrder.call(user: @user, cart: empty_cart, payment_method: "card")
    end
  end
end
```

### System Test

```ruby
# test/system/posts_test.rb
require "application_system_test_case"

class PostsTest < ApplicationSystemTestCase
  setup do
    @user = users(:john)
    @post = posts(:published)
  end

  test "viewing posts index" do
    visit posts_url

    assert_selector "h1", text: "Posts"
    assert_selector "article", minimum: 1
    assert_text @post.title
  end

  test "viewing a post" do
    visit post_url(@post)

    assert_selector "h1", text: @post.title
    assert_text @post.body
    assert_text @post.user.name
  end

  test "creating a post" do
    sign_in @user

    visit new_post_url

    fill_in "Title", with: "My New Post"
    fill_in "Body", with: "This is the content of my post."
    select "Technology", from: "Category"
    choose "Draft"

    click_button "Create Post"

    assert_text "Post was successfully created"
    assert_text "My New Post"
  end

  test "creating a post with validation errors" do
    sign_in @user

    visit new_post_url
    click_button "Create Post"

    assert_text "can't be blank"
  end

  test "editing a post" do
    sign_in @user

    visit post_url(@post)
    click_link "Edit"

    fill_in "Title", with: "Updated Title"
    click_button "Update Post"

    assert_text "Post was successfully updated"
    assert_text "Updated Title"
  end

  test "deleting a post" do
    sign_in @user

    visit post_url(@post)

    accept_confirm do
      click_button "Delete"
    end

    assert_text "Post was successfully deleted"
    assert_no_text @post.title
  end

  test "searching posts" do
    visit posts_url

    fill_in "Search", with: @post.title
    # Auto-submit via Stimulus

    assert_selector "article", count: 1
    assert_text @post.title
  end

  private

  def sign_in(user)
    visit login_url
    fill_in "Email", with: user.email
    fill_in "Password", with: "password"
    click_button "Sign in"
    assert_text "Signed in successfully"
  end
end
```

### Request Test (API)

```ruby
# test/requests/api/v1/posts_test.rb
require "test_helper"

class Api::V1::PostsTest < ActionDispatch::IntegrationTest
  setup do
    @user = users(:john)
    @post = posts(:published)
    @headers = {
      "Authorization" => "Bearer #{@user.api_token}",
      "Content-Type" => "application/json"
    }
  end

  # Index
  test "GET /api/v1/posts returns posts" do
    get api_v1_posts_url, headers: @headers

    assert_response :success
    json = JSON.parse(response.body)
    assert json["data"].is_a?(Array)
    assert json["meta"]["total_count"].positive?
  end

  test "GET /api/v1/posts paginates" do
    get api_v1_posts_url, params: { page: 1, per_page: 5 }, headers: @headers

    json = JSON.parse(response.body)
    assert_equal 1, json["meta"]["current_page"]
    assert json["data"].length <= 5
  end

  # Show
  test "GET /api/v1/posts/:id returns post" do
    get api_v1_post_url(@post), headers: @headers

    assert_response :success
    json = JSON.parse(response.body)
    assert_equal @post.id, json["data"]["id"]
    assert_equal @post.title, json["data"]["attributes"]["title"]
  end

  test "GET /api/v1/posts/:id returns 404 for missing" do
    get api_v1_post_url(id: "nonexistent"), headers: @headers

    assert_response :not_found
    json = JSON.parse(response.body)
    assert_equal "Not Found", json["error"]
  end

  # Create
  test "POST /api/v1/posts creates post" do
    assert_difference("Post.count") do
      post api_v1_posts_url,
        params: { post: { title: "API Post", body: "Content" } }.to_json,
        headers: @headers
    end

    assert_response :created
    json = JSON.parse(response.body)
    assert_equal "API Post", json["data"]["attributes"]["title"]
  end

  test "POST /api/v1/posts returns errors for invalid" do
    post api_v1_posts_url,
      params: { post: { title: "" } }.to_json,
      headers: @headers

    assert_response :unprocessable_entity
    json = JSON.parse(response.body)
    assert json["details"]["title"].present?
  end

  # Update
  test "PATCH /api/v1/posts/:id updates post" do
    patch api_v1_post_url(@post),
      params: { post: { title: "Updated" } }.to_json,
      headers: @headers

    assert_response :success
    @post.reload
    assert_equal "Updated", @post.title
  end

  # Delete
  test "DELETE /api/v1/posts/:id deletes post" do
    assert_difference("Post.count", -1) do
      delete api_v1_post_url(@post), headers: @headers
    end

    assert_response :no_content
  end

  # Authentication
  test "returns 401 without auth header" do
    get api_v1_posts_url

    assert_response :unauthorized
  end

  test "returns 401 with invalid token" do
    get api_v1_posts_url, headers: { "Authorization" => "Bearer invalid" }

    assert_response :unauthorized
  end
end
```

### Factory

```ruby
# test/factories/posts.rb
FactoryBot.define do
  factory :post do
    association :user
    association :category, optional: true

    title { Faker::Lorem.sentence }
    body { Faker::Lorem.paragraphs(number: 3).join("\n\n") }
    status { :draft }

    trait :published do
      status { :published }
      published_at { Time.current }
    end

    trait :archived do
      status { :archived }
    end

    trait :with_tags do
      transient do
        tags_count { 3 }
      end

      after(:create) do |post, evaluator|
        create_list(:tag, evaluator.tags_count).each do |tag|
          post.tags << tag
        end
      end
    end
  end
end
```

### Fixtures

```yaml
# test/fixtures/posts.yml
published:
  user: john
  category: technology
  title: Published Post
  slug: published-post
  body: This is a published post.
  status: published
  published_at: <%= 1.day.ago %>

draft:
  user: john
  title: Draft Post
  slug: draft-post
  body: This is a draft post.
  status: draft
```

## Safety Rules

1. **Arrange-Act-Assert** - Clear test structure
2. **Independence** - Tests should not depend on each other
3. **Fast** - Use mocks/stubs for external services
4. **Meaningful** - Test behavior, not implementation
5. **Coverage** - Focus on critical paths and edge cases
