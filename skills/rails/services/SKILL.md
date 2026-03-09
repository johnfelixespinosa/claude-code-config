---
name: rails-services
description: Create service objects for complex business logic with proper patterns, error handling, and result objects
user_invocable: true
arguments: "action ServiceName [options]"
---

# Rails Services Skill

Generate service objects that encapsulate business logic, following single responsibility principle with proper error handling and result objects.

## Usage

```
/rails-services create ProcessPayment
/rails-services create Users::Registration
/rails-services create Orders::Checkout --with-result
/rails-services create SendWelcomeEmail --async
```

## Supported Actions

### create
Create a new service object.

```
/rails-services create ServiceName [options]
```

**Options:**
- `--with-result` - Include Result object pattern
- `--async` - Create as a service that queues a job
- `--transaction` - Wrap in database transaction
- `--namespace=Orders` - Create in namespace

## Instructions

### Step 1: Analyze the Service Need

Determine what type of service is needed:
- **Command Service**: Performs an action (CreateOrder, SendEmail)
- **Query Service**: Retrieves data (SearchProducts, FilterUsers)
- **Form Object**: Handles multi-model forms
- **Policy Object**: Authorization logic

### Step 2: Create Service File

Location: `app/services/[namespace/]service_name.rb`

### Step 3: Apply Appropriate Pattern

## Service Patterns

### Basic Service Pattern

```ruby
# app/services/create_order.rb
class CreateOrder
  def self.call(...)
    new(...).call
  end

  def initialize(user:, cart:, payment_method:)
    @user = user
    @cart = cart
    @payment_method = payment_method
  end

  def call
    ActiveRecord::Base.transaction do
      order = create_order
      process_payment(order)
      send_confirmation(order)
      order
    end
  end

  private

  attr_reader :user, :cart, :payment_method

  def create_order
    Order.create!(
      user: user,
      total_cents: cart.total_cents,
      status: :pending
    )
  end

  def process_payment(order)
    PaymentGateway.charge(
      amount: order.total_cents,
      method: payment_method
    )
    order.update!(status: :paid)
  end

  def send_confirmation(order)
    OrderMailer.confirmation(order).deliver_later
  end
end

# Usage
order = CreateOrder.call(user: current_user, cart: @cart, payment_method: params[:payment_method])
```

### Result Object Pattern

```ruby
# app/services/users/registration.rb
module Users
  class Registration
    Result = Struct.new(:success?, :user, :errors, keyword_init: true)

    def self.call(...)
      new(...).call
    end

    def initialize(params:, invitation_token: nil)
      @params = params
      @invitation_token = invitation_token
    end

    def call
      user = build_user

      ActiveRecord::Base.transaction do
        if user.save
          process_invitation(user) if invitation_token
          send_welcome_email(user)
          Result.new(success?: true, user: user, errors: [])
        else
          Result.new(success?: false, user: user, errors: user.errors.full_messages)
        end
      end
    rescue StandardError => e
      Rails.logger.error("Registration failed: #{e.message}")
      Result.new(success?: false, user: nil, errors: [e.message])
    end

    private

    attr_reader :params, :invitation_token

    def build_user
      User.new(params)
    end

    def process_invitation(user)
      invitation = Invitation.find_by!(token: invitation_token)
      invitation.accept!(user)
    end

    def send_welcome_email(user)
      UserMailer.welcome(user).deliver_later
    end
  end
end

# Usage in controller
result = Users::Registration.call(params: user_params)

if result.success?
  redirect_to dashboard_path, notice: "Welcome!"
else
  @user = result.user
  flash.now[:alert] = result.errors.join(", ")
  render :new, status: :unprocessable_entity
end
```

### Service with Dependency Injection

```ruby
# app/services/process_payment.rb
class ProcessPayment
  def self.call(...)
    new(...).call
  end

  def initialize(order:, payment_gateway: PaymentGateway, mailer: OrderMailer)
    @order = order
    @payment_gateway = payment_gateway
    @mailer = mailer
  end

  def call
    charge = payment_gateway.charge(
      amount: order.total_cents,
      customer_id: order.user.stripe_customer_id
    )

    order.update!(
      status: :paid,
      payment_id: charge.id
    )

    mailer.receipt(order).deliver_later

    charge
  rescue PaymentGateway::CardDeclined => e
    order.update!(status: :payment_failed)
    raise PaymentFailedError, e.message
  end

  private

  attr_reader :order, :payment_gateway, :mailer

  class PaymentFailedError < StandardError; end
end

# Easy to test with mocks
result = ProcessPayment.call(
  order: order,
  payment_gateway: MockPaymentGateway,
  mailer: MockMailer
)
```

### Form Object Pattern

```ruby
# app/services/checkout_form.rb
class CheckoutForm
  include ActiveModel::Model
  include ActiveModel::Attributes

  attribute :user_id, :string
  attribute :shipping_address_id, :string
  attribute :billing_address_id, :string
  attribute :payment_method, :string
  attribute :notes, :string

  validates :user_id, :shipping_address_id, :payment_method, presence: true

  def save
    return false unless valid?

    ActiveRecord::Base.transaction do
      order = create_order
      create_shipment(order)
      process_payment(order)
      order
    end
  rescue ActiveRecord::RecordInvalid => e
    errors.add(:base, e.message)
    false
  end

  private

  def user
    @user ||= User.find(user_id)
  end

  def create_order
    Order.create!(
      user: user,
      shipping_address_id: shipping_address_id,
      billing_address_id: billing_address_id || shipping_address_id,
      notes: notes
    )
  end

  def create_shipment(order)
    Shipment.create!(order: order, address_id: shipping_address_id)
  end

  def process_payment(order)
    ProcessPayment.call(order: order, method: payment_method)
  end
end

# Usage in controller
@checkout = CheckoutForm.new(checkout_params)
if @checkout.save
  redirect_to order_path(@checkout.order)
else
  render :new
end
```

### Query Object Pattern

```ruby
# app/services/search_posts.rb
class SearchPosts
  def self.call(...)
    new(...).call
  end

  def initialize(scope: Post.all, params: {})
    @scope = scope
    @params = params
  end

  def call
    scope
      .then { |s| filter_by_status(s) }
      .then { |s| filter_by_category(s) }
      .then { |s| filter_by_date_range(s) }
      .then { |s| search_content(s) }
      .then { |s| apply_sorting(s) }
  end

  private

  attr_reader :scope, :params

  def filter_by_status(scope)
    return scope if params[:status].blank?
    scope.where(status: params[:status])
  end

  def filter_by_category(scope)
    return scope if params[:category_id].blank?
    scope.where(category_id: params[:category_id])
  end

  def filter_by_date_range(scope)
    return scope if params[:start_date].blank? && params[:end_date].blank?

    scope = scope.where("published_at >= ?", params[:start_date]) if params[:start_date]
    scope = scope.where("published_at <= ?", params[:end_date]) if params[:end_date]
    scope
  end

  def search_content(scope)
    return scope if params[:q].blank?
    scope.where("title ILIKE :q OR body ILIKE :q", q: "%#{params[:q]}%")
  end

  def apply_sorting(scope)
    case params[:sort]
    when "oldest" then scope.order(created_at: :asc)
    when "title" then scope.order(title: :asc)
    else scope.order(created_at: :desc)
    end
  end
end

# Usage
@posts = SearchPosts.call(params: search_params).page(params[:page])
```

## Directory Structure

```
app/services/
├── application_service.rb      # Base class (optional)
├── create_order.rb
├── process_payment.rb
├── search_posts.rb
├── users/
│   ├── registration.rb
│   ├── password_reset.rb
│   └── profile_update.rb
├── orders/
│   ├── checkout.rb
│   ├── fulfillment.rb
│   └── refund.rb
└── external/
    ├── stripe_service.rb
    └── sendgrid_service.rb
```

## Base Service Class (Optional)

```ruby
# app/services/application_service.rb
class ApplicationService
  def self.call(...)
    new(...).call
  end

  private

  def transaction(&block)
    ActiveRecord::Base.transaction(&block)
  end

  def log_error(message, error = nil)
    Rails.logger.error("#{self.class.name}: #{message}")
    Rails.logger.error(error.backtrace.first(5).join("\n")) if error
  end
end
```

## Testing Services

```ruby
# test/services/create_order_test.rb
require "test_helper"

class CreateOrderTest < ActiveSupport::TestCase
  setup do
    @user = users(:john)
    @cart = Cart.new(items: [products(:widget)])
  end

  test "creates order successfully" do
    order = CreateOrder.call(user: @user, cart: @cart, payment_method: "card")

    assert order.persisted?
    assert_equal @user, order.user
    assert_equal "paid", order.status
  end

  test "rolls back on payment failure" do
    PaymentGateway.stub(:charge, ->(*) { raise PaymentGateway::CardDeclined }) do
      assert_raises(CreateOrder::PaymentFailedError) do
        CreateOrder.call(user: @user, cart: @cart, payment_method: "card")
      end
    end

    assert_equal 0, Order.count
  end
end
```

## Safety Rules

1. **Single Responsibility** - One service, one job
2. **Dependency Injection** - Accept collaborators as arguments for testability
3. **Transaction Safety** - Wrap multi-step operations in transactions
4. **Meaningful Errors** - Use custom exception classes
5. **No Side Effects** - Services should be predictable
