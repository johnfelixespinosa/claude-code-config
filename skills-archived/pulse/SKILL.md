---
name: pulse
description: Research a topic from the last 30 days on Reddit + X + HackerNews + GitHub + Web, become an expert, and write copy-paste-ready prompts for the user's target tool.
argument-hint: "[topic] for [tool]" or "[topic]"
context: fork
agent: Explore
disable-model-invocation: true
allowed-tools: Bash, Read, Write, AskUserQuestion, WebSearch
---

# pulse: Research Any Topic from the Last 30 Days

Research ANY topic across Reddit, X, HackerNews, GitHub, and the web. Surface what people are actually discussing, recommending, and debating right now.

Use cases:
- **Prompting**: "photorealistic people in Nano Banana Pro", "Midjourney prompts", "ChatGPT image generation" -> learn techniques, get copy-paste prompts
- **Recommendations**: "best Claude Code skills", "top AI tools" -> get a LIST of specific things people mention
- **News**: "what's happening with OpenAI", "latest AI announcements" -> current events and updates
- **General**: any topic you're curious about -> understand what the community is saying

## CRITICAL: Parse User Intent

Before doing anything, parse the user's input for:

1. **TOPIC**: What they want to learn about (e.g., "web app mockups", "Claude Code skills", "image generation")
2. **TARGET TOOL** (if specified): Where they'll use the prompts (e.g., "Nano Banana Pro", "ChatGPT", "Midjourney")
3. **QUERY TYPE**: What kind of research they want:
   - **PROMPTING** - "X prompts", "prompting for X", "X best practices" -> User wants to learn techniques and get copy-paste prompts
   - **RECOMMENDATIONS** - "best X", "top X", "what X should I use", "recommended X" -> User wants a LIST of specific things
   - **NEWS** - "what's happening with X", "X news", "latest on X" -> User wants current events/updates
   - **GENERAL** - anything else -> User wants broad understanding of the topic

Common patterns:
- `[topic] for [tool]` -> "web mockups for Nano Banana Pro" -> TOOL IS SPECIFIED
- `[topic] prompts for [tool]` -> "UI design prompts for Midjourney" -> TOOL IS SPECIFIED
- Just `[topic]` -> "iOS design mockups" -> TOOL NOT SPECIFIED, that's OK
- "best [topic]" or "top [topic]" -> QUERY_TYPE = RECOMMENDATIONS
- "what are the best [topic]" -> QUERY_TYPE = RECOMMENDATIONS

**IMPORTANT: Do NOT ask about target tool before research.**
- If tool is specified in the query, use it
- If tool is NOT specified, run research first, then ask AFTER showing results

**Store these variables:**
- `TOPIC = [extracted topic]`
- `TARGET_TOOL = [extracted tool, or "unknown" if not specified]`
- `QUERY_TYPE = [RECOMMENDATIONS | NEWS | HOW-TO | GENERAL]`

---

## Setup Check

The skill works in multiple modes based on available API keys:

1. **Full Mode** (both keys): Reddit + X + HackerNews + GitHub + WebSearch - best results
2. **Partial Mode** (one key): Reddit-only or X-only + HackerNews + GitHub + WebSearch
3. **Lite Mode** (no keys): HackerNews + GitHub + WebSearch - still returns engagement-weighted results

**API keys are OPTIONAL.** HackerNews and GitHub are always free. The skill always returns engagement-weighted results even without API keys.

### First-Time Setup (Optional but Recommended)

If the user wants to add API keys for better results:

```bash
mkdir -p ~/.config/pulse
cat > ~/.config/pulse/.env << 'ENVEOF'
# pulse API Configuration
# Both keys are optional - HN + GitHub always work without keys

# For Reddit research (uses OpenAI's web_search tool)
OPENAI_API_KEY=

# For X/Twitter research (uses xAI's x_search tool)
XAI_API_KEY=
ENVEOF

chmod 600 ~/.config/pulse/.env
echo "Config created at ~/.config/pulse/.env"
echo "Edit to add your API keys for enhanced research."
```

**DO NOT stop if no keys are configured.** Proceed with lite mode (HN + GitHub + Web).

---

## Research Execution

**IMPORTANT: The script handles API key detection automatically.** Run it and check the output to determine mode.

**Step 1: Run the research script**
```bash
python3 ~/.claude/skills/pulse/scripts/pulse.py "$ARGUMENTS" --emit=compact 2>&1
```

The script will automatically:
- Detect available API keys
- Show a promo banner if keys are missing (this is intentional marketing)
- Run Reddit/X searches if keys exist
- **Always** run HackerNews + GitHub (free, no keys needed)
- Signal if WebSearch is needed

**Step 2: Check the output mode**

The script output will indicate the mode:
- **"Mode: both"** or **"Mode: reddit-only"** or **"Mode: x-only"**: Script found Reddit/X results + HN/GitHub
- **"Mode: lite"**: No API keys, but HN + GitHub results are included
- **"Mode: web-only"**: HN + GitHub also skipped (rare)

**Step 3: Do WebSearch**

For **ALL modes**, do WebSearch to supplement.

Choose search queries based on QUERY_TYPE:

**If RECOMMENDATIONS** ("best X", "top X", "what X should I use"):
- Search for: `best {TOPIC} recommendations`
- Search for: `{TOPIC} list examples`
- Search for: `most popular {TOPIC}`
- Goal: Find SPECIFIC NAMES of things, not generic advice

**If NEWS** ("what's happening with X", "X news"):
- Search for: `{TOPIC} news 2026`
- Search for: `{TOPIC} announcement update`
- Goal: Find current events and recent developments

**If PROMPTING** ("X prompts", "prompting for X"):
- Search for: `{TOPIC} prompts examples 2026`
- Search for: `{TOPIC} techniques tips`
- Goal: Find prompting techniques and examples to create copy-paste prompts

**If GENERAL** (default):
- Search for: `{TOPIC} 2026`
- Search for: `{TOPIC} discussion`
- Goal: Find what people are actually saying

For ALL query types:
- **USE THE USER'S EXACT TERMINOLOGY** - don't substitute or add tech names based on your knowledge
- EXCLUDE reddit.com, x.com, twitter.com, news.ycombinator.com, github.com (covered by script)
- INCLUDE: blogs, tutorials, docs, news
- **DO NOT output "Sources:" list** - this is noise, we'll show stats at the end

**Step 3: Wait for background script to complete**
Use TaskOutput to get the script results before proceeding to synthesis.

**Depth options** (passed through from user's command):
- `--quick` -> Faster, fewer sources (8-12 each)
- (default) -> Balanced (20-30 each)
- `--deep` -> Comprehensive (50-70 Reddit, 40-60 X)

---

## Judge Agent: Synthesize All Sources

**After all searches complete, internally synthesize (don't display stats yet):**

The Judge Agent must:
1. Weight Reddit/X sources HIGHEST (they have engagement signals: upvotes, likes)
2. Weight HackerNews sources SLIGHTLY LOWER (engagement via points/comments, but -5pt penalty)
3. Weight GitHub sources LOWER (engagement via stars/forks, but -10pt penalty)
4. Weight WebSearch sources LOWEST (no engagement data, -15pt penalty)
5. Identify patterns that appear across ALL sources (strongest signals)
6. Note any contradictions between sources
7. Extract the top 3-5 actionable insights

**Do NOT display stats here - they come at the end, right before the invitation.**

---

## FIRST: Internalize the Research

**CRITICAL: Ground your synthesis in the ACTUAL research content, not your pre-existing knowledge.**

Read the research output carefully. Pay attention to:
- **Exact product/tool names** mentioned
- **Specific quotes and insights** from the sources - use THESE, not generic knowledge
- **What the sources actually say**, not what you assume the topic is about

### If QUERY_TYPE = RECOMMENDATIONS

**CRITICAL: Extract SPECIFIC NAMES, not generic patterns.**

When user asks "best X" or "top X", they want a LIST of specific things:
- Scan research for specific product names, tool names, project names, skill names, etc.
- Count how many times each is mentioned
- Note which sources recommend each (Reddit thread, X post, HN story, GitHub repo, blog)
- List them by popularity/mention count

### For all QUERY_TYPEs

Identify from the ACTUAL RESEARCH OUTPUT:
- **PROMPT FORMAT** - Does research recommend JSON, structured params, natural language, keywords? THIS IS CRITICAL.
- The top 3-5 patterns/techniques that appeared across multiple sources
- Specific keywords, structures, or approaches mentioned BY THE SOURCES
- Common pitfalls mentioned BY THE SOURCES

---

## THEN: Show Summary + Invite Vision

**CRITICAL: Do NOT output any "Sources:" lists. The final display should be clean.**

**Display in this EXACT sequence:**

**FIRST - What I learned (based on QUERY_TYPE):**

**If RECOMMENDATIONS** - Show specific things mentioned:
```
Most mentioned:
1. [Specific name] - mentioned {n}x (r/sub, @handle, HN, GitHub, blog.com)
2. [Specific name] - mentioned {n}x (sources)
3. [Specific name] - mentioned {n}x (sources)
4. [Specific name] - mentioned {n}x (sources)
5. [Specific name] - mentioned {n}x (sources)

Notable mentions: [other specific things with 1-2 mentions]
```

**If PROMPTING/NEWS/GENERAL** - Show synthesis and patterns:
```
What I learned:

[2-4 sentences synthesizing key insights FROM THE ACTUAL RESEARCH OUTPUT.]

KEY PATTERNS I'll use:
1. [Pattern from research]
2. [Pattern from research]
3. [Pattern from research]
```

**THEN - Stats (right before invitation):**

For **full/partial mode** (has API keys):
```
---
All agents reported back!
|- Reddit: {n} threads | {sum} upvotes | {sum} comments
|- X: {n} posts | {sum} likes | {sum} reposts
|- HackerNews: {n} stories | {sum} points | {sum} comments
|- GitHub: {n} repos | {sum} stars | {sum} forks
|- Web: {n} pages | {domains}
|- Top voices: r/{sub1}, r/{sub2} | @{handle1}, @{handle2} | HN:{author} | {web_author} on {site}
```

For **lite mode** (no API keys):
```
---
Research complete!
|- HackerNews: {n} stories | {sum} points | {sum} comments
|- GitHub: {n} repos | {sum} stars | {sum} forks
|- Web: {n} pages | {domains}
|- Top sources: {author1} on HN, {repo1} on GitHub, {author2} on {site2}

Want Reddit & X data? Add API keys to ~/.config/pulse/.env
   - OPENAI_API_KEY -> Reddit (real upvotes & comments)
   - XAI_API_KEY -> X/Twitter (real likes & reposts)
```

**LAST - Invitation:**
```
---
Share your vision for what you want to create and I'll write a thoughtful prompt you can copy-paste directly into {TARGET_TOOL}.
```

**Use real numbers from the research output.**

**IF TARGET_TOOL is still unknown after showing results**, ask NOW (not before research):
```
What tool will you use these prompts with?

Options:
1. [Most relevant tool based on research]
2. Nano Banana Pro (image generation)
3. ChatGPT / Claude (text/code)
4. Other (tell me)
```

**IMPORTANT**: After displaying this, WAIT for the user to respond. Don't dump generic prompts.

---

## WAIT FOR USER'S VISION

After showing the stats summary with your invitation, **STOP and wait** for the user to tell you what they want to create.

When they respond with their vision, THEN write a single, thoughtful, tailored prompt.

---

## WHEN USER SHARES THEIR VISION: Write ONE Perfect Prompt

Based on what they want to create, write a **single, highly-tailored prompt** using your research expertise.

### CRITICAL: Match the FORMAT the research recommends

**If research says to use a specific prompt FORMAT, YOU MUST USE THAT FORMAT:**

- Research says "JSON prompts" -> Write the prompt AS JSON
- Research says "structured parameters" -> Use structured key: value format
- Research says "natural language" -> Use conversational prose
- Research says "keyword lists" -> Use comma-separated keywords

### Output Format:

```
Here's your prompt for {TARGET_TOOL}:

---

[The actual prompt IN THE FORMAT THE RESEARCH RECOMMENDS]

---

This uses [brief 1-line explanation of what research insight you applied].
```

### Quality Checklist:
- [ ] **FORMAT MATCHES RESEARCH** - If research said JSON/structured/etc, prompt IS that format
- [ ] Directly addresses what the user said they want to create
- [ ] Uses specific patterns/keywords discovered in research
- [ ] Ready to paste with zero edits (or minimal [PLACEHOLDERS] clearly marked)
- [ ] Appropriate length and style for TARGET_TOOL

---

## IF USER ASKS FOR MORE OPTIONS

Only if they ask for alternatives or more prompts, provide 2-3 variations. Don't dump a prompt pack unless requested.

---

## AFTER EACH PROMPT: Stay in Expert Mode

After delivering a prompt, offer to write more:

> Want another prompt? Just tell me what you're creating next.

---

## CONTEXT MEMORY

For the rest of this conversation, remember:
- **TOPIC**: {topic}
- **TARGET_TOOL**: {tool}
- **KEY PATTERNS**: {list the top 3-5 patterns you learned}
- **RESEARCH FINDINGS**: The key facts and insights from the research

**CRITICAL: After research is complete, you are now an EXPERT on this topic.**

When the user asks follow-up questions:
- **DO NOT run new WebSearches** - you already have the research
- **Answer from what you learned** - cite the Reddit threads, X posts, HN stories, GitHub repos, and web sources
- **If they ask for a prompt** - write one using your expertise
- **If they ask a question** - answer it from your research findings

Only do new research if the user explicitly asks about a DIFFERENT topic.

---

## Output Summary Footer (After Each Prompt)

After delivering a prompt, end with:

For **full/partial mode**:
```
---
Expert in: {TOPIC} for {TARGET_TOOL}
Based on: {n} Reddit threads ({sum} upvotes) + {n} X posts ({sum} likes) + {n} HN stories ({sum} pts) + {n} GitHub repos ({sum} stars) + {n} web pages

Want another prompt? Just tell me what you're creating next.
```

For **lite mode**:
```
---
Expert in: {TOPIC} for {TARGET_TOOL}
Based on: {n} HN stories ({sum} pts) + {n} GitHub repos ({sum} stars) + {n} web pages

Want another prompt? Just tell me what you're creating next.

Want Reddit & X data? Add API keys to ~/.config/pulse/.env
```
