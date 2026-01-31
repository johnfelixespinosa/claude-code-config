# Rails Schema Inspector
# Usage: bin/rails runner ~/.claude/skills/rails-inspect/scripts/schema.rb [table_names...]
#
# Outputs database schema as JSON including:
# - Tables with columns, types, defaults, nullability
# - Indexes (unique, composite, partial)
# - Foreign keys with references
# - Primary key types (uuid vs integer)

require 'json'

class SchemaInspector
  def initialize(filter_tables = [])
    @filter_tables = filter_tables.map(&:to_s).map(&:downcase)
    @connection = ActiveRecord::Base.connection
  end

  def inspect
    {
      tables: inspect_tables,
      metadata: metadata
    }
  end

  private

  def inspect_tables
    table_names = @connection.tables.sort

    # Filter if specific tables requested
    if @filter_tables.any?
      table_names = table_names.select do |t|
        @filter_tables.any? { |f| t.downcase.include?(f.downcase) }
      end
    end

    # Exclude internal Rails tables
    table_names -= %w[ar_internal_metadata schema_migrations]

    table_names.map { |table| inspect_table(table) }
  end

  def inspect_table(table_name)
    columns = @connection.columns(table_name)
    pk = @connection.primary_key(table_name)

    {
      name: table_name,
      primary_key: pk,
      primary_key_type: pk ? columns.find { |c| c.name == pk }&.type&.to_s : nil,
      columns: columns.map { |col| inspect_column(col) },
      indexes: inspect_indexes(table_name),
      foreign_keys: inspect_foreign_keys(table_name)
    }
  end

  def inspect_column(column)
    result = {
      name: column.name,
      type: column.type.to_s,
      sql_type: column.sql_type,
      null: column.null,
      default: column.default
    }

    # Add array flag for PostgreSQL arrays
    if column.respond_to?(:array?) && column.array?
      result[:array] = true
    end

    # Add limit for string/text columns
    if column.limit && column.type.in?([:string, :binary])
      result[:limit] = column.limit
    end

    # Add precision/scale for decimals
    if column.type == :decimal
      result[:precision] = column.precision if column.precision
      result[:scale] = column.scale if column.scale
    end

    result
  end

  def inspect_indexes(table_name)
    @connection.indexes(table_name).map do |index|
      {
        name: index.name,
        columns: index.columns,
        unique: index.unique,
        where: index.where,
        using: index.using&.to_s
      }.compact
    end
  end

  def inspect_foreign_keys(table_name)
    return [] unless @connection.respond_to?(:foreign_keys)

    @connection.foreign_keys(table_name).map do |fk|
      {
        from_table: fk.from_table,
        to_table: fk.to_table,
        column: fk.column,
        primary_key: fk.primary_key,
        name: fk.name,
        on_delete: fk.on_delete,
        on_update: fk.on_update
      }.compact
    end
  end

  def metadata
    {
      total_tables: @connection.tables.count - 2, # Exclude internal tables
      rails_version: Rails.version,
      adapter: @connection.adapter_name,
      database: @connection.current_database,
      encoding: database_encoding
    }
  end

  def database_encoding
    case @connection.adapter_name
    when /postgresql/i
      @connection.select_value("SHOW server_encoding")
    when /mysql/i
      @connection.select_value("SELECT @@character_set_database")
    else
      nil
    end
  rescue
    nil
  end
end

# Parse arguments (table names to filter)
filter_tables = ARGV.dup

# Run inspection
inspector = SchemaInspector.new(filter_tables)
result = inspector.inspect

# Output as formatted JSON
puts JSON.pretty_generate(result)
