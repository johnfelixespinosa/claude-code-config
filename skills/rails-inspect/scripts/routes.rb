# Rails Routes Inspector
# Usage: bin/rails runner ~/.claude/skills/rails-inspect/scripts/routes.rb [filter]
#
# Outputs routes as JSON including:
# - HTTP verb, path, controller#action
# - Route name (for path helpers)
# - Constraints and defaults
# - Namespace grouping

require 'json'

class RoutesInspector
  def initialize(filter = nil)
    @filter = filter&.downcase
    @routes = Rails.application.routes.routes
  end

  def inspect
    {
      routes: inspect_routes,
      metadata: metadata
    }
  end

  private

  def inspect_routes
    routes = @routes
      .map { |route| inspect_route(route) }
      .compact

    # Apply filter if provided
    if @filter
      routes = routes.select do |r|
        r[:path]&.downcase&.include?(@filter) ||
        r[:controller]&.downcase&.include?(@filter) ||
        r[:name]&.downcase&.include?(@filter)
      end
    end

    routes
  end

  def internal_route?(route)
    # Rails 8+ uses `internal` attribute, older versions use `internal?`
    if route.respond_to?(:internal?)
      route.internal?
    elsif route.respond_to?(:internal)
      route.internal
    else
      # Fallback: check if path starts with /rails/
      route.path.spec.to_s.start_with?('/rails/')
    end
  end

  def inspect_route(route)
    # Skip internal Rails routes
    return nil if internal_route?(route)

    # Get route requirements
    reqs = route.requirements
    controller = reqs[:controller]
    action = reqs[:action]

    # Skip if no controller (e.g., redirect routes)
    return nil unless controller

    path = route.path.spec.to_s
    # Clean up path format (remove (.:format) suffix)
    path = path.gsub('(.:format)', '').gsub(/\(\.:format\)/, '')

    verb = route.verb
    verb = verb.source if verb.respond_to?(:source)
    verb = verb.to_s.gsub(/[$^]/, '')
    verb = 'ANY' if verb.blank?

    result = {
      verb: verb,
      path: path,
      controller: controller,
      action: action
    }

    # Add route name if present
    if route.name.present?
      result[:name] = route.name
      result[:helper] = "#{route.name}_path"
    end

    # Add constraints if any
    constraints = extract_constraints(route)
    result[:constraints] = constraints if constraints.any?

    # Add defaults beyond controller/action
    defaults = reqs.except(:controller, :action)
    result[:defaults] = defaults if defaults.any?

    result
  end

  def extract_constraints(route)
    constraints = {}

    route.constraints.each do |key, value|
      next if key == :request_method

      constraints[key] = case value
      when Regexp then value.source
      when Proc then 'Proc'
      else value.to_s
      end
    end

    constraints
  end

  def metadata
    all_routes = @routes.reject { |r| internal_route?(r) }
    controllers = all_routes.map { |r| r.requirements[:controller] }.compact.uniq

    # Detect namespaces
    namespaces = controllers
      .select { |c| c.include?('/') }
      .map { |c| c.split('/')[0..-2].join('/') }
      .uniq
      .sort

    # Detect API versions
    api_versions = namespaces
      .select { |n| n =~ /api\/v\d+/ }
      .sort

    {
      total_routes: all_routes.count,
      controllers: controllers.count,
      namespaces: namespaces,
      api_versions: api_versions.any? ? api_versions : nil,
      mounted_engines: detect_mounted_engines
    }.compact
  end

  def detect_mounted_engines
    @routes
      .select { |r| r.app.is_a?(Class) || r.app.respond_to?(:app) }
      .map do |r|
        app = r.app
        app = app.app if app.respond_to?(:app)

        {
          path: r.path.spec.to_s.gsub('(.:format)', ''),
          engine: app.class.name
        }
      end
      .reject { |e| e[:engine].include?('ActionDispatch') }
      .presence
  rescue
    nil
  end
end

# Parse arguments (optional filter)
filter = ARGV.first

# Run inspection
inspector = RoutesInspector.new(filter)
result = inspector.inspect

# Output as formatted JSON
puts JSON.pretty_generate(result)
