---
name: rails-jobs
description: Create background jobs with Solid Queue, proper error handling, idempotency, and retry strategies
user_invocable: true
arguments: "action JobName [options]"
---

# Rails Jobs Skill

Generate background jobs following best practices for idempotency, error handling, and retry strategies using Solid Queue (Rails 8 default).

## Usage

```
/rails-jobs create SendWelcomeEmailJob
/rails-jobs create ProcessOrderJob --queue=critical
/rails-jobs create GenerateReportJob --scheduled
/rails-jobs create SyncInventoryJob --idempotent
/rails-jobs create BatchImportJob --batch
```

## Supported Actions

### create
Create a new background job.

```
/rails-jobs create JobName [options]
```

**Options:**
- `--queue=name` - Specify queue (default, critical, low)
- `--idempotent` - Add idempotency pattern with locking
- `--scheduled` - Add scheduling pattern for recurring jobs
- `--batch` - Add batch processing pattern
- `--retries=5` - Custom retry count

## Instructions

### Step 1: Determine Job Type

| Type | Use Case | Pattern |
|------|----------|---------|
| Standard | One-off async task | Basic job |
| Idempotent | May be retried/duplicated | Lock + check |
| Scheduled | Recurring task | Cron-like |
| Batch | Large dataset processing | Chunked |

### Step 2: Create Job File

Location: `app/jobs/[namespace/]job_name.rb`

## Job Patterns

### Standard Job

```ruby
# app/jobs/send_welcome_email_job.rb
class SendWelcomeEmailJob < ApplicationJob
  queue_as :default

  retry_on Net::SMTPServerBusy, wait: 5.minutes, attempts: 3
  discard_on ActiveJob::DeserializationError

  def perform(user_id)
    user = User.find(user_id)
    UserMailer.welcome(user).deliver_now
  end
end

# Usage
SendWelcomeEmailJob.perform_later(user.id)
```

### Idempotent Job (Recommended)

```ruby
# app/jobs/process_order_job.rb
class ProcessOrderJob < ApplicationJob
  queue_as :critical

  retry_on StandardError, wait: :polynomially_longer, attempts: 5
  discard_on ActiveJob::DeserializationError

  def perform(order_id)
    order = Order.find(order_id)

    # Idempotency check - skip if already processed
    return if order.processed?

    # Acquire lock to prevent concurrent processing
    order.with_lock do
      # Double-check after acquiring lock
      return if order.processed?

      ActiveRecord::Base.transaction do
        process_order(order)
        order.update!(processed_at: Time.current, status: :processed)
      end
    end
  end

  private

  def process_order(order)
    # Business logic here
    ChargePayment.call(order: order)
    UpdateInventory.call(order: order)
    SendConfirmation.call(order: order)
  end
end
```

### Idempotent Job with Advisory Lock (PostgreSQL)

```ruby
# app/jobs/sync_external_data_job.rb
class SyncExternalDataJob < ApplicationJob
  queue_as :default

  retry_on StandardError, wait: 1.minute, attempts: 3

  def perform(resource_id)
    # Use PostgreSQL advisory lock for cross-process safety
    lock_key = "sync_#{resource_id}".hash

    ActiveRecord::Base.connection.execute("SELECT pg_advisory_lock(#{lock_key})")

    begin
      resource = Resource.find(resource_id)
      return if resource.synced_at && resource.synced_at > 1.hour.ago

      ExternalApi.sync(resource)
      resource.update!(synced_at: Time.current)
    ensure
      ActiveRecord::Base.connection.execute("SELECT pg_advisory_unlock(#{lock_key})")
    end
  end
end
```

### Scheduled/Recurring Job

```ruby
# app/jobs/cleanup_expired_sessions_job.rb
class CleanupExpiredSessionsJob < ApplicationJob
  queue_as :low

  def perform
    # Prevent duplicate runs
    return if recently_ran?

    deleted_count = Session.expired.delete_all

    Rails.logger.info "Cleaned up #{deleted_count} expired sessions"

    # Record completion
    Rails.cache.write(cache_key, Time.current, expires_in: 50.minutes)
  end

  private

  def recently_ran?
    Rails.cache.exist?(cache_key)
  end

  def cache_key
    "#{self.class.name}:last_run"
  end
end

# Schedule in config/recurring.yml (Solid Queue)
# cleanup_sessions:
#   class: CleanupExpiredSessionsJob
#   schedule: every hour
```

### Batch Processing Job

```ruby
# app/jobs/batch_import_job.rb
class BatchImportJob < ApplicationJob
  queue_as :default

  BATCH_SIZE = 100

  retry_on StandardError, wait: 5.minutes, attempts: 3

  def perform(import_id, offset: 0)
    import = Import.find(import_id)
    return if import.completed? || import.failed?

    records = import.pending_records.offset(offset).limit(BATCH_SIZE)

    if records.empty?
      import.update!(status: :completed, completed_at: Time.current)
      return
    end

    ActiveRecord::Base.transaction do
      records.each do |record|
        ImportRecord.call(record: record, import: import)
      end

      import.update!(processed_count: import.processed_count + records.size)
    end

    # Queue next batch
    self.class.perform_later(import_id, offset: offset + BATCH_SIZE)
  rescue => e
    import.update!(status: :failed, error_message: e.message)
    raise
  end
end
```

### Job with Progress Tracking

```ruby
# app/jobs/generate_report_job.rb
class GenerateReportJob < ApplicationJob
  queue_as :default

  def perform(report_id)
    report = Report.find(report_id)
    report.update!(status: :processing, started_at: Time.current)

    begin
      total = report.data_scope.count
      processed = 0

      report.data_scope.find_each do |record|
        process_record(record, report)
        processed += 1

        # Update progress every 100 records
        if processed % 100 == 0
          report.update!(progress: (processed.to_f / total * 100).round)
        end
      end

      report.update!(
        status: :completed,
        completed_at: Time.current,
        progress: 100
      )
    rescue => e
      report.update!(status: :failed, error_message: e.message)
      raise
    end
  end

  private

  def process_record(record, report)
    # Processing logic
  end
end
```

### Pipeline/Orchestrator Job

```ruby
# app/jobs/pipeline/orchestrator_job.rb
module Pipeline
  class OrchestratorJob < ApplicationJob
    queue_as :default

    def perform(pipeline_id, completed_stage: nil)
      pipeline = Pipeline.find(pipeline_id)

      # Advisory lock for pipeline
      lock_key = "pipeline_#{pipeline_id}".hash

      ActiveRecord::Base.transaction do
        return unless acquire_advisory_lock(lock_key)

        # Record completed stage
        if completed_stage
          pipeline.mark_stage_complete(completed_stage)
        end

        # Determine next stage
        next_stage = determine_next_stage(pipeline)

        case next_stage
        when :analyze
          Pipeline::AnalyzeJob.perform_later(pipeline_id)
        when :process
          Pipeline::ProcessJob.perform_later(pipeline_id)
        when :finalize
          Pipeline::FinalizeJob.perform_later(pipeline_id)
        when :complete
          pipeline.update!(status: :completed)
        end
      end
    end

    private

    def acquire_advisory_lock(key)
      result = ActiveRecord::Base.connection.select_value(
        "SELECT pg_try_advisory_xact_lock(#{key})"
      )
      result == true || result == "t"
    end

    def determine_next_stage(pipeline)
      case pipeline.status
      when "pending" then :analyze
      when "analyzed" then :process
      when "processed" then :finalize
      else :complete
      end
    end
  end
end
```

## Solid Queue Configuration

```yaml
# config/recurring.yml
cleanup_sessions:
  class: CleanupExpiredSessionsJob
  schedule: every hour

daily_report:
  class: GenerateDailyReportJob
  schedule: every day at 6am

sync_inventory:
  class: SyncInventoryJob
  schedule: every 15 minutes
```

```yaml
# config/solid_queue.yml
default: &default
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    - queues: [default]
      threads: 5
      processes: 2
    - queues: [critical]
      threads: 3
      processes: 1
    - queues: [low]
      threads: 2
      processes: 1
```

## Error Handling Strategies

```ruby
class ApplicationJob < ActiveJob::Base
  # Retry with exponential backoff
  retry_on StandardError, wait: :polynomially_longer, attempts: 5

  # Don't retry on deserialization errors (record deleted)
  discard_on ActiveJob::DeserializationError

  # Custom error handling
  rescue_from CustomError do |exception|
    # Log, notify, etc.
    Honeybadger.notify(exception)
  end

  around_perform do |job, block|
    Rails.logger.info "Starting #{job.class.name} with args: #{job.arguments}"
    start_time = Time.current

    block.call

    duration = Time.current - start_time
    Rails.logger.info "Completed #{job.class.name} in #{duration.round(2)}s"
  end
end
```

## Testing Jobs

```ruby
# test/jobs/process_order_job_test.rb
require "test_helper"

class ProcessOrderJobTest < ActiveSupport::TestCase
  include ActiveJob::TestHelper

  test "processes order successfully" do
    order = orders(:pending)

    perform_enqueued_jobs do
      ProcessOrderJob.perform_later(order.id)
    end

    order.reload
    assert_equal "processed", order.status
    assert_not_nil order.processed_at
  end

  test "is idempotent" do
    order = orders(:already_processed)

    assert_no_changes -> { order.reload.updated_at } do
      ProcessOrderJob.perform_now(order.id)
    end
  end

  test "retries on transient failure" do
    order = orders(:pending)

    ExternalService.stub(:call, -> { raise Net::ReadTimeout }) do
      assert_enqueued_with(job: ProcessOrderJob, at: 5.minutes.from_now) do
        ProcessOrderJob.perform_now(order.id)
      end
    end
  end
end
```

## Safety Rules

1. **ALWAYS** make jobs idempotent - safe to run multiple times
2. **ALWAYS** pass IDs, not objects - avoid serialization issues
3. **ALWAYS** handle errors gracefully with proper retry strategies
4. **NEVER** rely on job order - jobs may run out of order
5. **ALWAYS** use transactions for multi-step operations
6. **CONSIDER** using advisory locks for critical sections
