---
name: rails-models
description: Create and modify ActiveRecord models with Rails conventions - migrations, associations, validations, and scopes
user_invocable: true
arguments: "action name [attributes/options]"
---

# Rails Models Skill

Generate and modify ActiveRecord models following Rails 8 conventions. Uses runtime introspection to understand existing schema before making changes.

## Usage

```
/rails-models create Order user:references total_cents:integer status:string
/rails-models add_column users phone:string
/rails-models add_association Post has_many:comments
/rails-models add_validation User presence:name uniqueness:email
/rails-models add_index users email --unique
/rails-models add_enum Order status:pending,processing,shipped,delivered
/rails-models add_scope User active "where(active: true)"
```

## Supported Actions

### create
Create a new model with migration.

```
/rails-models create ModelName attribute:type attribute:type...
```

**Attribute Types:**
- `string`, `text`, `integer`, `float`, `decimal`, `boolean`, `date`, `datetime`, `time`
- `references` or `belongs_to` - Creates foreign key
- `jsonb` or `json` - JSON column (prefer jsonb for PostgreSQL)
- `uuid` - UUID column

**Attribute Modifiers:**
- `:index` - Add index (e.g., `email:string:index`)
- `:unique` - Add unique index (e.g., `email:string:unique`)
- `:null` - Allow null (default is nullable)
- `:default=X` - Set default value (e.g., `status:integer:default=0`)

### add_column
Add column to existing table.

```
/rails-models add_column table_name column:type [modifiers]
```

### add_association
Add association to existing model.

```
/rails-models add_association ModelName association_type:target [options]
```

**Association Types:**
- `has_many:comments` - One-to-many
- `has_one:profile` - One-to-one
- `belongs_to:user` - Many-to-one (adds foreign key)
- `has_many:tags,through:taggings` - Many-to-many through

**Options:**
- `dependent:destroy` - Cascade delete
- `optional:true` - Allow nil (for belongs_to)
- `foreign_key:custom_id` - Custom foreign key
- `class_name:CustomModel` - Custom class name

### add_validation
Add validation to existing model.

```
/rails-models add_validation ModelName validation_type:attribute [options]
```

**Validation Types:**
- `presence:name` - Validates presence
- `uniqueness:email` - Validates uniqueness
- `length:name,minimum=2,maximum=100` - Length validation
- `format:email,with=/regex/` - Format validation
- `numericality:price,greater_than=0` - Numeric validation
- `inclusion:status,in=[active,inactive]` - Inclusion validation

### add_index
Add database index.

```
/rails-models add_index table_name column [--unique] [--where="condition"]
```

### add_enum
Add enum to model (Rails 8 syntax).

```
/rails-models add_enum ModelName attribute:value1,value2,value3
```

### add_scope
Add named scope to model.

```
/rails-models add_scope ModelName scope_name "query"
```

## Instructions

When this skill is invoked, follow these steps:

### Step 1: Parse the Action and Arguments

Extract:
- `action`: create, add_column, add_association, add_validation, add_index, add_enum, add_scope
- `target`: Model name or table name
- `specifications`: Attributes, types, options

### Step 2: Inspect Current State

**ALWAYS** run introspection first to understand existing schema:

```bash
# Check if model/table exists
bin/rails runner ~/.claude/skills/rails-inspect/scripts/schema.rb [table_name]

# Check model associations and validations
bin/rails runner ~/.claude/skills/rails-inspect/scripts/models.rb [ModelName]
```

Use this information to:
- Detect conflicts (duplicate columns, associations)
- Understand existing patterns (naming conventions, index styles)
- Validate foreign key targets exist

### Step 3: Generate Changes

#### For `create` action:
Use Rails generator when appropriate:

```bash
bin/rails generate model ModelName attribute:type attribute:type --no-test-framework
```

Then customize the generated files to add:
- UUID primary key if project uses UUIDs
- Additional validations
- Associations
- Scopes

#### For modification actions:
Create targeted migrations and edit model files directly.

### Step 4: Apply Project Conventions

**From CLAUDE.md - Always follow these:**

```ruby
# UUID primary keys (if project uses them)
create_table :table_name, id: :uuid do |t|
  t.references :other, type: :uuid, foreign_key: true
end

# Enum syntax (Rails 8)
enum :status, {
  pending: "pending",
  active: "active"
}

# String status fields for state machines
t.string :status, null: false, default: 'initial'

# JSONB for flexible metadata
t.jsonb :metadata, default: {}
```

### Step 5: Output Plan and Diff

Before making any changes, present:

1. **Summary**: What will be created/modified
2. **Files Affected**: List of files to create or edit
3. **Migration Preview**: The migration code
4. **Model Changes**: Additions to model file

Ask for confirmation before proceeding.

### Step 6: Execute Changes

After confirmation:
1. Create/edit migration file
2. Edit model file
3. Run `bin/rails db:migrate` (only in development)
4. Show final state

## Templates

### Migration Template (Create Table)
```ruby
class Create<%= table_name.camelize.pluralize %> < ActiveRecord::Migration[8.0]
  def change
    create_table :<%= table_name.pluralize %>, id: :uuid do |t|
      <%= columns.map { |c| "t.#{c[:type]} :#{c[:name]}#{c[:options]}" }.join("\n      ") %>

      t.timestamps
    end

    <%= indexes.map { |i| "add_index :#{table_name.pluralize}, :#{i[:column]}#{i[:options]}" }.join("\n    ") %>
  end
end
```

### Migration Template (Add Column)
```ruby
class Add<%= column_name.camelize %>To<%= table_name.camelize.pluralize %> < ActiveRecord::Migration[8.0]
  def change
    add_column :<%= table_name.pluralize %>, :<%= column_name %>, :<%= column_type %><%= options %>
    <%= "add_index :#{table_name.pluralize}, :#{column_name}#{index_options}" if add_index %>
  end
end
```

### Model Template
```ruby
class <%= model_name %> < ApplicationRecord
  # Associations
  <%= associations.join("\n  ") %>

  # Validations
  <%= validations.join("\n  ") %>

  # Enums
  <%= enums.join("\n  ") %>

  # Scopes
  <%= scopes.join("\n  ") %>
end
```

## Safety Rules

1. **NEVER** run migrations in production environment
2. **ALWAYS** show diff before applying changes
3. **NEVER** drop columns or tables without explicit user confirmation
4. **ALWAYS** create reversible migrations
5. **CHECK** for existing indexes before adding duplicates
6. **VALIDATE** foreign key targets exist before adding references

## Error Handling

- **Table already exists**: Suggest using add_column instead
- **Column already exists**: Show current column definition, ask to proceed
- **Model file not found**: Suggest creating model first
- **Invalid attribute type**: List valid types
- **Missing foreign key target**: Warn and ask for confirmation

## Examples

### Create a complete model
```
/rails-models create Product name:string:null=false price_cents:integer:null=false:default=0 description:text category:references status:string:default=draft
```

### Add association with dependent
```
/rails-models add_association User has_many:orders dependent:destroy
```

### Add enum with string backing
```
/rails-models add_enum Order status:pending,confirmed,shipped,delivered,cancelled
```

### Add composite index
```
/rails-models add_index orders user_id,created_at
```
