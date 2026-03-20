---
name: real-world-rails
description: Research how production Rails apps solve architectural problems using the Real World Rails repository (200+ open-source apps). Use this skill whenever the user asks how other Rails apps handle something, wants to compare implementation patterns, needs evidence for an architectural decision, or mentions "rails patterns", "how do other apps do X", "real world rails", "production examples", "what's the common approach for". Also trigger when the user is debating between two Rails patterns and could benefit from seeing how real codebases chose — even if they don't explicitly ask for research.
---

# Rails Pattern Research

## The Repository

The **Real World Rails** repository is a curated collection of 200+ production
Rails application source code. It's a goldmine for answering "how do real apps
actually do this?" instead of relying on blog posts and toy examples.

- **Repository**: https://github.com/eliotsykes/real-world-rails
- **Structure**: `apps/` contains full app source (models, migrations, schema,
  controllers, views, concerns, Gemfiles). `engines/` contains Rails engines.

## Locating the Repository

Check these locations in order:

1. `~/src/real-world-rails`
2. `~/real-world-rails`
3. Current working directory or any parent with `real-world-rails/apps/`

If found locally, use the local copy — it's faster and allows deep code reading.

If **not found locally**, use the GitHub API to search the repository remotely:
```bash
# Search for patterns across the repo
gh api search/code -X GET -f q='<search-term> repo:eliotsykes/real-world-rails' -f per_page=20

# Browse specific app directories
gh api repos/eliotsykes/real-world-rails/contents/apps

# Read a specific file from an app
gh api repos/eliotsykes/real-world-rails/contents/apps/<app-name>/app/models/<file>.rb
```

If `gh` is not available, fall back to raw GitHub URLs:
```
https://api.github.com/search/code?q=<term>+repo:eliotsykes/real-world-rails
```

Tell the user which access method you're using (local or remote) so they know
they can clone the repo locally for faster, deeper research.

## Research Workflow

### 1. Decompose the Question

Break the user's topic into searchable patterns. For "how do apps handle
soft deletes?" that becomes:

- Gem usage: `paranoia`, `discard`, `acts_as_paranoid` in Gemfiles
- Schema patterns: `deleted_at` columns in `schema.rb` / migrations
- Model patterns: `acts_as_paranoid`, `include Discard::Model`, custom concerns
- Query patterns: default scopes, explicit `.kept` / `.with_discarded`

### 2. Search in Parallel

Spin up parallel agents — one per search angle. Each agent should:

- **Search broadly first** — grep across all apps for the pattern
- **Read deeply second** — once hits are found, read the surrounding code
  (the full model, the migration, the schema) to understand context
- **Note the app name** — every finding must be attributed to a specific app

Reading actual code is the whole point. File name matches alone are worthless.

### 3. Build a Comparative Evidence Table

This is the core output. Don't just narrate what you found — structure it:

| App | Approach | Gem/Method | Notable Detail |
|-----|----------|------------|----------------|
| diaspora | paranoia | `acts_as_paranoid` | Applies to 12 models, uses default scope |
| gitlabhq | custom | `deleted_at` column | Hand-rolled concern, no gem dependency |
| discourse | discard | `include Discard::Model` | Only on 3 models, prefers hard delete |

Include as many apps as you find (aim for 5-15 examples). This table is what
makes the research actionable — the user can see the distribution of approaches
at a glance.

### 4. Synthesize Patterns

After the table, provide analysis:

- **Dominant pattern**: What do most apps do? (e.g., "7 of 12 apps use paranoia")
- **Minority patterns**: What do the outliers do, and why might they have chosen differently?
- **Complexity correlation**: Do larger/more complex apps tend toward one approach?
- **Gem ecosystem health**: Are the gems actively maintained? Any migrations happening (e.g., paranoia → discard)?
- **Your recommendation**: Given what the evidence shows, what would you suggest for the user's project?

## Adversarial Mode

When the user's wording suggests they want help *choosing* between approaches
(phrases like "compare for us", "which fits best", "debate", "adversarial",
"evaluate for our project", "pros and cons"), go deeper:

1. Run the standard research workflow above
2. Then spin up **advocate agents** — one per major pattern found — each tasked
   with making the strongest possible case for their pattern *in the context of
   the user's current project*
3. Each advocate should reference:
   - Evidence from the real-world-rails apps
   - How the pattern fits (or conflicts with) the user's existing architecture
   - Maintenance burden and long-term implications
   - Migration path if they later change their mind
4. Present the advocates' arguments side by side, then give your own verdict

## Tips for Effective Searching

**Local repo searches** — cast a wide net:
```bash
# Search across all apps for a pattern
grep -r "acts_as_paranoid\|include Discard" apps/ --include="*.rb" -l

# Check Gemfiles for gem usage
grep -r "gem.*paranoia\|gem.*discard" apps/ --include="Gemfile"

# Search schema files for column patterns
grep -r "deleted_at" apps/ --include="schema.rb"
```

**Remote searches** — be strategic with API calls:
- GitHub code search has rate limits; use specific terms
- Search for gem names in Gemfiles first, then drill into specific apps
- Use file path filters: `path:app/models` or `filename:schema.rb`

**What to read** when you find a hit:
- The model file (for concerns, validations, scopes, callbacks)
- The schema or migration (for column types, indexes, constraints)
- The Gemfile (for gem version and related dependencies)
- Tests if available (for intended behavior and edge cases)
