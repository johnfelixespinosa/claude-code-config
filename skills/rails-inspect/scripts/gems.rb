# Rails Gems Inspector
# Usage: bin/rails runner ~/.claude/skills/rails-inspect/scripts/gems.rb
#
# Outputs key gem information as JSON including:
# - Categorized gems (database, auth, background jobs, etc.)
# - Version information
# - Notable configuration

require 'json'

class GemsInspector
  GEM_CATEGORIES = {
    framework: %w[rails railties activesupport activerecord actionpack actionview actionmailer activejob actioncable activestorage],
    database: %w[pg mysql2 sqlite3 trilogy],
    server: %w[puma unicorn thin falcon],
    authentication: %w[devise rodauth clearance authlogic sorcery omniauth],
    authorization: %w[pundit cancancan action_policy],
    background_jobs: %w[sidekiq solid_queue good_job delayed_job resque que],
    caching: %w[solid_cache redis redis-rails dalli],
    search: %w[ransack pg_search searchkick elasticsearch meilisearch],
    pagination: %w[pagy kaminari will_paginate],
    file_upload: %w[shrine carrierwave paperclip],
    api: %w[grape jsonapi-rails graphql graphql-ruby jbuilder fast_jsonapi alba],
    frontend: %w[turbo-rails stimulus-rails hotwire-rails importmap-rails tailwindcss-rails cssbundling-rails jsbundling-rails],
    testing: %w[rspec-rails minitest factory_bot_rails fabrication faker capybara selenium-webdriver],
    linting: %w[rubocop rubocop-rails rubocop-rspec standard],
    deployment: %w[kamal capistrano mina],
    monitoring: %w[honeybadger sentry-ruby rollbar newrelic_rpm scout_apm skylight],
    admin: %w[rails_admin activeadmin administrate avo],
    payments: %w[stripe pay solidus spree],
    mailer: %w[letter_opener mailcatcher postmark-rails sendgrid-ruby],
    utilities: %w[image_processing nokogiri httparty faraday rest-client aws-sdk-s3]
  }.freeze

  def inspect
    {
      installed: categorized_gems,
      gemfile_summary: gemfile_summary,
      metadata: metadata
    }
  end

  private

  def all_gems
    @all_gems ||= Gem.loaded_specs.transform_values(&:version)
  end

  def categorized_gems
    result = {}

    GEM_CATEGORIES.each do |category, gem_names|
      found = gem_names.select { |name| all_gems.key?(name) }
        .map { |name| { name: name, version: all_gems[name].to_s } }

      result[category] = found if found.any?
    end

    result
  end

  def gemfile_summary
    gemfile_path = Rails.root.join('Gemfile')
    return nil unless File.exist?(gemfile_path)

    content = File.read(gemfile_path)

    {
      ruby_version: extract_ruby_version(content),
      git_sources: content.scan(/git_source\(:\w+\)/).count,
      github_gems: content.scan(/github:/).count,
      git_gems: content.scan(/git:/).count,
      groups: extract_groups(content),
      total_gems: content.scan(/^\s*gem\s+['"]/).count
    }
  end

  def extract_ruby_version(content)
    match = content.match(/ruby\s+['"]([^'"]+)['"]/)
    match ? match[1] : nil
  end

  def extract_groups(content)
    content.scan(/group\s+:(\w+)/).flatten.uniq.sort
  end

  def metadata
    {
      total_loaded: all_gems.count,
      bundler_version: Bundler::VERSION,
      load_path_size: $LOAD_PATH.size
    }
  end
end

# Run inspection
inspector = GemsInspector.new
result = inspector.inspect

# Output as formatted JSON
puts JSON.pretty_generate(result)
