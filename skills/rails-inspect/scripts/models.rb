# Rails Models Inspector
# Usage: bin/rails runner ~/.claude/skills/rails-inspect/scripts/models.rb [model_names...]
#
# Outputs model information as JSON including:
# - Associations (has_many, belongs_to, has_one, has_and_belongs_to_many)
# - Validations with options
# - Scopes (named scopes)
# - Callbacks
# - Included concerns/modules
# - Enum definitions

require 'json'

class ModelsInspector
  def initialize(filter_models = [])
    @filter_models = filter_models.map(&:to_s).map(&:camelize)

    # Eager load all models
    Rails.application.eager_load! if Rails.env.development? || Rails.env.test?
  end

  def inspect
    {
      models: inspect_models,
      metadata: metadata
    }
  end

  private

  def all_models
    ApplicationRecord.descendants.sort_by(&:name)
  rescue NameError
    # Fallback for apps without ApplicationRecord
    ActiveRecord::Base.descendants
      .reject { |m| m.abstract_class? || m.name.nil? }
      .sort_by(&:name)
  end

  def inspect_models
    models = all_models

    # Filter if specific models requested
    if @filter_models.any?
      models = models.select do |m|
        @filter_models.any? { |f| m.name&.include?(f) }
      end
    end

    models.map { |model| inspect_model(model) }
  end

  def inspect_model(model)
    {
      name: model.name,
      table_name: safe_table_name(model),
      abstract: model.abstract_class?,
      associations: inspect_associations(model),
      validations: inspect_validations(model),
      scopes: inspect_scopes(model),
      callbacks: inspect_callbacks(model),
      enums: inspect_enums(model),
      concerns: inspect_concerns(model),
      class_methods: inspect_class_methods(model)
    }.compact
  end

  def safe_table_name(model)
    model.table_name
  rescue ActiveRecord::StatementInvalid
    nil
  end

  def inspect_associations(model)
    result = {}

    [:has_many, :has_one, :belongs_to, :has_and_belongs_to_many].each do |type|
      assocs = model.reflect_on_all_associations(type)
      next if assocs.empty?

      result[type] = assocs.map do |assoc|
        info = { name: assoc.name.to_s }

        # Add important options
        info[:class_name] = assoc.class_name if assoc.class_name != assoc.name.to_s.classify
        info[:foreign_key] = assoc.foreign_key if assoc.foreign_key != "#{assoc.name}_id"
        info[:dependent] = assoc.options[:dependent] if assoc.options[:dependent]
        info[:through] = assoc.options[:through].to_s if assoc.options[:through]
        info[:polymorphic] = true if assoc.options[:polymorphic]
        info[:optional] = assoc.options[:optional] if assoc.options.key?(:optional)
        info[:counter_cache] = assoc.options[:counter_cache] if assoc.options[:counter_cache]

        info.size == 1 ? assoc.name.to_s : info
      end
    end

    result.empty? ? nil : result
  end

  def inspect_validations(model)
    return nil if model.validators.empty?

    # Group validations by attribute
    grouped = model.validators.group_by { |v| v.attributes.first&.to_s || 'base' }

    grouped.transform_values do |validators|
      validators.map do |v|
        type = v.class.name.demodulize.underscore.sub(/_validator$/, '')
        options = v.options.except(:if, :unless, :on)

        if options.empty?
          type
        else
          { type: type, options: options }
        end
      end
    end
  end

  def inspect_scopes(model)
    # Get scope names (they're stored as singleton methods)
    scope_names = model.methods(false)
      .select { |m| model.respond_to?(m) }
      .select { |m|
        begin
          # Check if it returns an ActiveRecord::Relation
          model.send(m).is_a?(ActiveRecord::Relation) rescue false
        rescue ArgumentError
          # Scope requires arguments
          true
        end
      }

    # Also check for explicitly defined scopes
    if model.respond_to?(:_declared_scopes, true)
      scope_names += model._declared_scopes rescue []
    end

    scopes = scope_names.uniq.sort.map(&:to_s)
    scopes.empty? ? nil : scopes
  rescue
    nil
  end

  def inspect_callbacks(model)
    callback_types = [
      :before_validation, :after_validation,
      :before_save, :after_save, :around_save,
      :before_create, :after_create, :around_create,
      :before_update, :after_update, :around_update,
      :before_destroy, :after_destroy, :around_destroy,
      :after_commit, :after_rollback
    ]

    result = {}

    callback_types.each do |type|
      callbacks = model.send("_#{type}_callbacks") rescue nil
      next unless callbacks

      names = callbacks
        .map { |cb| cb.filter.to_s if cb.filter.is_a?(Symbol) }
        .compact
        .uniq

      result[type] = names if names.any?
    end

    result.empty? ? nil : result
  end

  def inspect_enums(model)
    return nil unless model.respond_to?(:defined_enums)

    enums = model.defined_enums
    return nil if enums.empty?

    enums.transform_values { |mapping| mapping.keys }
  end

  def inspect_concerns(model)
    # Get included modules that look like concerns
    concerns = model.included_modules
      .select { |m| m.name&.include?('::') || m.name =~ /able$|tion$|ment$/ }
      .reject { |m| m.name&.start_with?('ActiveRecord', 'ActiveModel', 'ActiveSupport') }
      .map(&:name)
      .compact
      .sort

    concerns.empty? ? nil : concerns
  end

  def inspect_class_methods(model)
    # Find notable class methods (not from ActiveRecord)
    ar_methods = ActiveRecord::Base.methods
    custom_methods = model.methods(false) - ar_methods

    # Filter to likely useful methods
    notable = custom_methods
      .select { |m| m.to_s =~ /^find_by_|^search|^filter|^for_|^with_|^by_/ }
      .map(&:to_s)
      .sort

    notable.empty? ? nil : notable
  end

  def metadata
    {
      total_models: all_models.count,
      rails_version: Rails.version,
      abstract_models: all_models.count(&:abstract_class?)
    }
  end
end

# Parse arguments (model names to filter)
filter_models = ARGV.dup

# Run inspection
inspector = ModelsInspector.new(filter_models)
result = inspector.inspect

# Output as formatted JSON
puts JSON.pretty_generate(result)
