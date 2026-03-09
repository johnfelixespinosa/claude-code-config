# Rails Environment Inspector
# Usage: bin/rails runner ~/.claude/skills/rails-inspect/scripts/environment.rb
#
# Outputs environment information as JSON including:
# - Rails version and environment
# - Ruby version
# - Database configuration
# - Key gem versions
# - Application configuration

require 'json'

class EnvironmentInspector
  def inspect
    {
      rails: rails_info,
      ruby: ruby_info,
      database: database_info,
      gems: gem_versions,
      application: application_info,
      features: detect_features
    }
  end

  private

  def rails_info
    {
      version: Rails.version,
      environment: Rails.env,
      root: Rails.root.to_s,
      eager_load: Rails.configuration.eager_load,
      cache_classes: Rails.configuration.cache_classes,
      zeitwerk: defined?(Zeitwerk) ? true : false
    }
  end

  def ruby_info
    {
      version: RUBY_VERSION,
      platform: RUBY_PLATFORM,
      patchlevel: RUBY_PATCHLEVEL
    }
  end

  def database_info
    config = ActiveRecord::Base.connection_db_config
    connection = ActiveRecord::Base.connection

    {
      adapter: config.adapter,
      database: config.database,
      host: config.host || 'localhost',
      pool_size: config.pool,
      current_connections: connection.pool.connections.size,
      schema_version: ActiveRecord::Migrator.current_version,
      pending_migrations: pending_migrations_count
    }
  rescue => e
    { error: e.message }
  end

  def pending_migrations_count
    context = ActiveRecord::MigrationContext.new(Rails.root.join('db/migrate'))
    context.pending_migration_versions.count
  rescue
    nil
  end

  def gem_versions
    gems = {}

    # Key gems to check
    gem_names = %w[
      rails
      pg mysql2 sqlite3
      puma unicorn
      devise rodauth
      sidekiq solid_queue good_job
      redis
      turbo-rails stimulus-rails hotwire-rails
      importmap-rails
      tailwindcss-rails
      rspec-rails minitest
      factory_bot_rails
      rubocop
      kamal capistrano
    ]

    gem_names.each do |name|
      spec = Gem.loaded_specs[name]
      gems[name] = spec.version.to_s if spec
    end

    gems.sort.to_h
  end

  def application_info
    {
      name: Rails.application.class.module_parent_name,
      time_zone: Rails.configuration.time_zone,
      default_locale: I18n.default_locale,
      available_locales: I18n.available_locales,
      asset_pipeline: detect_asset_pipeline,
      api_only: Rails.application.config.api_only
    }
  end

  def detect_asset_pipeline
    if defined?(Propshaft)
      'propshaft'
    elsif defined?(Sprockets)
      'sprockets'
    elsif defined?(Importmap)
      'importmap'
    elsif defined?(Webpacker)
      'webpacker'
    else
      'none'
    end
  end

  def detect_features
    features = []

    # Hotwire
    features << 'turbo' if defined?(Turbo)
    features << 'stimulus' if defined?(Stimulus)

    # Background Jobs
    features << 'solid_queue' if defined?(SolidQueue)
    features << 'sidekiq' if defined?(Sidekiq)
    features << 'good_job' if defined?(GoodJob)

    # Caching
    features << 'solid_cache' if defined?(SolidCache)
    features << 'redis_cache' if Rails.cache.class.name.include?('Redis')

    # Real-time
    features << 'action_cable' if defined?(ActionCable)
    features << 'solid_cable' if defined?(SolidCable)

    # Auth
    features << 'devise' if defined?(Devise)
    features << 'rodauth' if defined?(Rodauth)

    # API
    features << 'graphql' if defined?(GraphQL)
    features << 'jbuilder' if defined?(Jbuilder)

    # Storage
    features << 'active_storage' if defined?(ActiveStorage)

    # Testing
    features << 'rspec' if defined?(RSpec)
    features << 'factory_bot' if defined?(FactoryBot)

    features.sort
  end
end

# Run inspection
inspector = EnvironmentInspector.new
result = inspector.inspect

# Output as formatted JSON
puts JSON.pretty_generate(result)
