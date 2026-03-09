---
name: write-tests
description: This skill should be used when users mention writing tests, creating tests, adding test coverage, or testing code changes. It generates Minitest tests for Rails models, services, controllers, and jobs following project conventions and testing principles.
---

# Write Tests

## Overview

Generate Minitest tests for Rails applications following established project conventions. This skill analyzes existing code, identifies testable behavior, and creates comprehensive tests that verify functionality without testing implementation details.

## When to Use

- After implementing new features (models, services, controllers, jobs)
- When adding test coverage to existing code
- When the user mentions "write tests", "add tests", "test this", or similar
- After completing code changes that need verification

## Testing Principles

Follow these core principles when generating tests:

1. **Never test the type or shape of return values** - Tests verify behavior, not implementation details or data structures

2. **Test default behavior first** - Each public method should have a test for its default return value with no setup

3. **Establish meaningful setup** - When testing a method returns its default value, first establish setup that would make it return the opposite without intervention. Otherwise the test is meaningless.

4. **Keep variables close to usage** - Do not put variables in setup or as constants at the top of the test class. Declare them where they are used.

5. **Test behavior, not implementation** - Focus on what the code does, not how it does it

## Workflow

### Step 1: Identify Files to Test

Analyze recent changes or specified files to determine what needs tests:

```bash
# Check recent changes
git diff --name-only HEAD~1 | grep -E '\.(rb)$'

# Or use git status for uncommitted changes
git status --porcelain | grep -E '\.rb$'
```

### Step 2: Determine Test Type

Based on file location, determine test type:

| File Location | Test Type | Test Location |
|---------------|-----------|---------------|
| `app/models/` | Model test | `test/models/` |
| `app/services/` | Service test | `test/services/` |
| `app/controllers/` | Controller test | `test/controllers/` |
| `app/jobs/` | Job test | `test/jobs/` |

### Step 3: Read Existing Code

Before writing tests, always read:

1. The file being tested (to understand public interface)
2. Any existing tests for the file (to avoid duplication)
3. Related factories (to understand test data setup)

### Step 4: Generate Tests

Create tests following these patterns:

#### Model Test Pattern

```ruby
require "test_helper"

class ModelNameTest < ActiveSupport::TestCase
  # Test associations
  test "belongs to parent" do
    record = build(:model_name)
    assert record.respond_to?(:parent)
  end

  # Test validations - verify behavior, not presence
  test "requires field_name" do
    record = build(:model_name, field_name: nil)
    assert_not record.valid?
    assert_includes record.errors[:field_name], "can't be blank"
  end

  # Test scopes - verify they return expected records
  test "active scope returns only active records" do
    active = create(:model_name, status: "active")
    inactive = create(:model_name, status: "inactive")

    assert_includes ModelName.active, active
    assert_not_includes ModelName.active, inactive
  end

  # Test instance methods - focus on behavior
  test "method_name returns expected result" do
    record = create(:model_name)
    # Setup that would change the result
    create(:related_record, model_name: record)

    assert record.method_name
  end
end
```

#### Service Test Pattern

```ruby
require "test_helper"

class ServiceNameTest < ActiveSupport::TestCase
  test "successfully performs action" do
    record = build(:model_name)
    service = ServiceName.new(record)

    result = service.call

    assert result.success?
    assert record.persisted?
  end

  test "fails with invalid input" do
    record = build(:model_name, required_field: nil)
    service = ServiceName.new(record)

    result = service.call

    assert_not result.success?
    assert_not result.errors.empty?
  end

  test "result exposes the record" do
    record = build(:model_name)
    service = ServiceName.new(record)

    result = service.call

    assert_equal record, result.record
  end
end
```

#### Controller Test Pattern

```ruby
require "test_helper"

class ControllerNameTest < ActionDispatch::IntegrationTest
  test "index returns success" do
    get controller_path

    assert_response :success
  end

  test "create with valid params redirects" do
    assert_difference("ModelName.count") do
      post controller_path, params: { model_name: valid_attributes }
    end

    assert_redirected_to model_name_path(ModelName.last)
  end

  test "create with invalid params renders new" do
    assert_no_difference("ModelName.count") do
      post controller_path, params: { model_name: invalid_attributes }
    end

    assert_response :unprocessable_entity
  end

  private

  def valid_attributes
    { field: "value" }
  end

  def invalid_attributes
    { field: nil }
  end
end
```

#### Job Test Pattern

```ruby
require "test_helper"

class JobNameTest < ActiveSupport::TestCase
  test "performs expected action" do
    record = create(:model_name)

    JobName.perform_now(record.id)

    record.reload
    assert_equal "expected_status", record.status
  end

  test "handles missing record gracefully" do
    assert_nothing_raised do
      JobName.perform_now("nonexistent-uuid")
    end
  end

  test "is idempotent" do
    record = create(:model_name)

    2.times { JobName.perform_now(record.id) }

    record.reload
    # Assert expected state after multiple runs
  end
end
```

### Step 5: Run Tests

After generating tests, always run them to verify they pass:

```bash
# Run specific test file
bundle exec rails test test/path/to/test_file.rb

# Run specific test by line number
bundle exec rails test test/path/to/test_file.rb:42

# Run all tests in a directory
bundle exec rails test test/models/
```

## Test Utilities

### FactoryBot

Use FactoryBot for test data:

```ruby
# Build (in memory, not saved)
record = build(:model_name)

# Create (saved to database)
record = create(:model_name)

# Build with overrides
record = build(:model_name, field: "custom_value")

# Create list
records = create_list(:model_name, 3)
```

### Mocha for Mocking

Use Mocha when needed for external dependencies:

```ruby
# Stub a method
ModelName.any_instance.stubs(:external_call).returns("mocked")

# Expect a method call
ModelName.any_instance.expects(:method_name).once
```

### VCR for External APIs

Use VCR for HTTP interactions:

```ruby
test "fetches external data" do
  use_vcr_cassette do
    result = ExternalService.fetch_data
    assert result.present?
  end
end
```

## Anti-Patterns to Avoid

1. **Testing private methods** - Only test public interface
2. **Testing return types** - Don't assert `is_a?` or `kind_of?`
3. **Over-mocking** - Prefer real objects when possible
4. **Setup blocks with unrelated data** - Keep setup minimal and relevant
5. **Constants for test data** - Declare variables inline where used
6. **Testing Rails/framework behavior** - Focus on application logic
7. **Meaningless default tests** - Ensure setup would change the outcome

## Checklist Before Completing

- [ ] Read the source file being tested
- [ ] Check for existing tests to avoid duplication
- [ ] Tests verify behavior, not implementation
- [ ] Variables declared close to usage
- [ ] Default behavior tests have meaningful setup
- [ ] Tests run and pass
