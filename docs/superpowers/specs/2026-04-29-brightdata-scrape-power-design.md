# brightdata-scrape Kiro Power — Design Spec

**Date:** 2026-04-29
**Author:** Bright Data
**Status:** Approved design, pending implementation plan

---

## Goal

Ship a Kiro power that lets a user, working in any existing application, say "add scraping" (or describe a scraping need) and get back:

1. **Production-ready scraper code** integrated into their existing project, in the right shape for their stack (module, API route, or agent tool — picked by detection, not asked).
2. **The Bright Data MCP server wired into the project**, so any AI agent the user runs against the project (Claude Code, Cursor, Cline, Kiro itself) gains live web tools.

The power must work on greenfield workspaces too, but is optimized for the "I have an existing app, add this capability to it" case.

## Non-goals

- Scheduling, cron jobs, GitHub Actions, queue workers — deferred to a future power.
- Database writes, ETL pipelines, dashboards, UI components.
- Proxy zone management (the `brightdata-cli` skill covers that).
- Multi-site / multi-target orchestration in one pass.
- First-class language support beyond Python and TypeScript/JavaScript. Other languages get a generic Web Unlocker `curl`/HTTP template with a note that the user adapts it.

## Architecture

```
powers/brightdata-scrape/
├── POWER.md                          # frontmatter + onboarding + orchestrator pointer
├── mcp.json                          # Bright Data remote MCP server
└── steering/
    ├── scrape-workflow.md            # orchestrator (always loaded for any task)
    ├── phase1-detect-and-plan.md     # repo detection → pattern decision → confirm
    ├── phase2-scraping-playbook.md   # condensed Web Unlocker / Browser API / pre-built decision
    ├── phase3-integrate.md           # generate the right code (module / route / agent tool)
    └── phase4-mcp-and-verify.md      # wire MCP, run a smoke test, write README snippet
```

Mirrors the `aws-amplify` power's phased orchestration model. The orchestrator (`scrape-workflow.md`) reads each phase steering file one at a time via Kiro's `readSteering` action, and never reads ahead. Unlike aws-amplify, all four phases are **mandatory** for every invocation — the orchestrator does not skip phases. Confirmation gates between phases let the user abort, but the sequence is fixed.

## POWER.md frontmatter

```yaml
---
name: "brightdata-scrape"
displayName: "Add web scraping to any app with Bright Data"
description: "Detect your project's stack and add production-ready web scraping — generates the right integration pattern (module, API route, or agent tool), wires Bright Data MCP into your project, handles pagination and bot detection."
keywords: ["scrape", "scraping", "scraper", "crawl", "crawler", "web-data", "extract", "extract-data", "competitor", "pricing-monitor", "lead-generation", "amazon", "linkedin", "instagram", "tiktok", "youtube", "serp", "google-search", "search-engine", "brightdata", "bright-data", "web-unlocker", "browser-api", "captcha", "bot-detection", "pagination", "agent-tools", "mcp"]
author: "Bright Data"
---
```

Keyword strategy: verb forms (`scrape`, `extract`), use cases (`competitor`, `pricing-monitor`, `lead-generation`), platforms (`amazon`, `linkedin`, `instagram`, `tiktok`, `youtube`), tech terms (`web-unlocker`, `browser-api`, `captcha`). Wide enough to catch indirect requests like "I want competitor prices from this site" without requiring the literal word "scrape."

## mcp.json

```json
{
  "mcpServers": {
    "brightdata": {
      "url": "https://mcp.brightdata.com/mcp?token=${BRIGHTDATA_API_KEY}",
      "disabled": false
    }
  }
}
```

Single remote SSE-style server with the token interpolated from env. The Phase 4 steering shows how to append `&pro=1` or `&groups=social,ecommerce` for users who need the 60+ Pro tools.

## POWER.md body

### Onboarding (three steps)

1. **Get a Bright Data API token.** Link to `https://brightdata.com/cp/setting/users`. Explain free 5,000 requests/month allowance.
2. **Configure the token.** Two options, user picks one:
   - **Env var:** `export BRIGHTDATA_API_KEY=<token>` in their shell or `.env`.
   - **User-level Kiro config:** add the `brightdata` server to `~/.kiro/settings/mcp.json` with the token hardcoded so it's available in every Kiro project.
3. **(Optional) Set up an Unlocker zone.** Most users can use the default zone; link to `https://brightdata.com/cp/zones` for users who hit "no zone" errors.

Then a one-liner: *"Once configured, describe what you want to scrape — the power detects your project and adds the right integration."*

### Pointer to orchestrator

```
For any scraping task, ALWAYS read steering first:
  Call action "readSteering" with powerName="brightdata-scrape", steeringFile="scrape-workflow.md"

Do NOT improvise. Do NOT skip the phases.
```

## Phase 1 — Detect & Plan (`phase1-detect-and-plan.md`)

### Step 1: Manifest detection

Look for, in order:
- `package.json`
- `pyproject.toml` / `requirements.txt` / `Pipfile`
- `go.mod`
- `Cargo.toml`
- `Gemfile`
- `pom.xml` / `build.gradle`
- `composer.json`

If none found → **greenfield mode** (skip stack signature, default to module pattern, ask which language they want — Python or TypeScript).

If multiple manifests at root level (rare) or in subdirs (monorepo) → ask user which sub-project to integrate into. Do not pick.

### Step 2: Stack signature

Within the chosen manifest, look for these signals:

**Web framework dependencies (route pattern):**
- TS/JS: `next`, `express`, `fastify`, `hono`, `koa`, `@nestjs/core`, `remix`
- Python: `fastapi`, `flask`, `django`, `aiohttp`, `starlette`

**Agent framework dependencies (agent-tool pattern):**
- TS/JS: `langchain`, `@langchain/*`, `@anthropic-ai/sdk`, `openai`, `mastra`, `@ai-sdk/*`, `@modelcontextprotocol/sdk`
- Python: `langchain`, `anthropic`, `openai`, `llama-index`, `crewai`, `mcp`

### Step 3: Pick the single pattern (Q6=D, detection-driven)

| Signals | Pattern |
|---------|---------|
| Web framework deps present | **API route** |
| Agent framework deps present, no web framework | **Agent tool** |
| Both web + agent | Ask user which surface they want |
| Neither (library / CLI / unknown) | **Module** |
| Greenfield (no manifest) | **Module**, with language ask |

The chosen pattern is shown to the user but not put up for vote — Q6=D rejected the multiple-output flow.

### Step 4: Targeted scraping question

Ask, in one message:

> "What do you want to scrape, and which fields? (e.g., 'product name + price + image from amazon.com search results'.) And roughly how many pages/items?"

Don't ask about pagination type, output format, or language preference. Pagination type comes from Phase 2 reconnaissance. Output format defaults to a typed return value (no file write — the caller decides). Language is determined by the manifest signature: `package.json` → TypeScript; `pyproject.toml` / `requirements.txt` → Python; greenfield → ask the user once.

### Step 5: Present plan & wait for confirmation

```
## Plan

**Detected:** <stack signature>
**Pattern:** <module | API route | agent tool>
**Target:** <user's site/data>
**Phases:**
  1. ✓ Detect & plan (this phase, just confirmed)
  2. Pick the right Bright Data API and selectors
  3. Generate <files> in your project
  4. Wire Bright Data MCP and run a smoke test

Ready?
```

Wait for confirmation. After confirmation, the orchestrator advances to Phase 2.

## Phase 2 — Scraping playbook, condensed (`phase2-scraping-playbook.md`)

This is the ~30%-size condensed version of the brightdata-plugin `scraper-builder` skill. Contains:

### Decision tree (the 4-line core)

1. Pre-built scraper exists for this domain? → **Web Scraper API** (zero parsing, structured JSON).
2. Static HTML, no interaction needed? → **Web Unlocker** (cheapest, simplest).
3. JS-rendered or needs clicks/scrolls? → **Browser API** (full automation).
4. Search engine results? → **SERP API**.

### Pre-built check

One curl to discover:
```bash
curl -H "Authorization: Bearer $BRIGHTDATA_API_KEY" \
     https://api.brightdata.com/datasets/list
```
Search the response for the target domain. If matched, use the dataset's `id` with the Web Scraper API.

### Reconnaissance (when no pre-built)

1. Fetch raw HTML via Web Unlocker.
2. Inspect: is the data in the HTML, or behind a `<div id="root">` / `<div id="__next">` / `ng-app`?
3. Pick selectors with priority: `data-*` > semantic class > `id` > nth-child (avoid).
4. Spot hidden JSON APIs in the page source — hitting them directly via Web Unlocker is cleaner than parsing HTML.

### Pagination patterns (one-paragraph each)

- **URL-based:** loop `?page=N` until empty result.
- **Next-link:** follow `a[rel="next"]` until absent.
- **Cursor:** loop with `?cursor=<token>` from previous response.
- **Infinite scroll:** Browser API, scroll until item count stops growing.

### Concurrency rule

If the user has 50+ URLs, use semaphore-bounded async (default `CONCURRENCY=20`). Sequential `time.sleep(1)` loops are unacceptable at that volume.

### Pointer to the long-form skill

> *For deeper analysis (anti-bot escalation, multi-site parallelism, retry semantics, browser-session reuse), the brightdata-plugin `scraper-builder` skill is the long-form reference. This phase is a working subset.*

### Output of Phase 2

A small decision record the orchestrator carries into Phase 3:

```
{
  "approach": "web-unlocker" | "browser-api" | "pre-built" | "serp",
  "dataset_id": "<if pre-built>",
  "selectors": { ... },
  "pagination": "url-based" | "next-link" | "cursor" | "infinite-scroll" | "none",
  "estimated_volume": "<single | small (<50) | bulk (>=50)>"
}
```

## Phase 3 — Integrate (`phase3-integrate.md`)

Code-generation phase. Picks the sub-template from Phase 1's pattern decision, fills it with Phase 2's decision record.

### Sub-template A — Module pattern

**TypeScript:** `src/scrapers/<target>.ts`
- Exports `async function scrape<Target>(input): Promise<<Target>Item[]>`.
- Uses `fetch` + Bright Data `https://api.brightdata.com/request` endpoint.
- Includes a `parseItems(html)` helper using a parser the project already has (cheerio if installed, otherwise a minimal regex/HTMLRewriter fallback).

**Python:** `src/scrapers/<target>.py`
- Exports `def scrape_<target>(input) -> list[<Target>Item]`.
- Uses `requests` if already in project, else `httpx` if already there, else `requests` (added to `requirements.txt`).
- Uses `beautifulsoup4` if already there, else added.

Both write to `.env.example`:
```
# Get token at https://brightdata.com/cp/setting/users
BRIGHTDATA_API_KEY=
# Optional — defaults to the account's default Web Unlocker zone if unset.
# Create or rename a zone at https://brightdata.com/cp/zones
BRIGHTDATA_UNLOCKER_ZONE=
```

The generated scraper module reads `BRIGHTDATA_UNLOCKER_ZONE` with a fallback to the literal string `"unblocker"` (Bright Data's default zone name for new accounts). Documented in code comments and README so the user knows when they need to set it.

Both append a `## Web scraping` section to `README.md` showing one usage example.

### Sub-template B — API route pattern

Builds on sub-template A (the route imports the module), then drops in a route file:

| Framework | Route file path |
|-----------|-----------------|
| Next.js App Router | `app/api/scrape/route.ts` |
| Next.js Pages Router | `pages/api/scrape.ts` |
| Express | `src/routes/scrape.ts` + show user the `app.use(...)` line |
| Fastify | `src/routes/scrape.ts` + show user the `fastify.register(...)` line |
| Hono | `src/routes/scrape.ts` + registration line |
| Koa | `src/routes/scrape.ts` + `router.get(...)` line |
| FastAPI | `app/api/scrape.py` + show user the `app.include_router(...)` line |
| Flask | `app/scrape.py` (blueprint) + `app.register_blueprint(...)` line |
| Django | `<app>/views/scrape.py` + URL pattern line |

Detection:
- Next.js: `app/` directory exists → App Router; `pages/api/` exists → Pages Router; both → ask.
- Others: pick by manifest dependency.

### Sub-template C — Agent tool pattern

Builds on sub-template A (the tool calls the module), then generates a tool definition:

| Framework | Output |
|-----------|--------|
| LangChain TS | `src/tools/scrape.ts` exporting a `Tool` instance |
| LangChain Python | `src/tools/scrape.py` exporting a `BaseTool` subclass |
| Anthropic SDK (TS) | `src/tools/scrape.ts` exporting `tools: [{ name, description, input_schema, run }]` |
| Anthropic SDK (Python) | `src/tools/scrape.py` exporting same shape |
| OpenAI SDK | `src/tools/scrape.{ts,py}` with function-calling schema + handler |
| Mastra | Mastra-idiomatic tool registration |
| Vercel AI SDK | `tool({ description, parameters, execute })` from `ai` package |

Tool definition always includes:
- `name`: `scrape_<target>`
- `description`: 2 sentences, what it does + when to use it
- `input_schema` / `parameters`: `{ url?: string, query?: string, ... }` matching the user's stated fields

### Confirmation gate before writing

Power lists every file it will write/modify and asks "OK to write?" Waits. No edits until confirmed.

### Existing-file safety

- If a target file already exists: never overwrite. Suggest `<name>2.ts` or ask user where to put it.
- If `.env.example` already has `BRIGHTDATA_API_KEY`: skip that line.
- If `README.md` already has a `## Web scraping` section: append a sub-section, don't replace.

## Phase 4 — MCP wiring + verify (`phase4-mcp-and-verify.md`)

### Step 1: Project-level MCP config

Write or merge `.kiro/settings/mcp.json` with:

```json
{
  "mcpServers": {
    "brightdata": {
      "url": "https://mcp.brightdata.com/mcp?token=${BRIGHTDATA_API_KEY}",
      "disabled": false
    }
  }
}
```

Behavior:
- File doesn't exist → create with just this entry.
- File exists, no `brightdata` key → merge in this entry.
- File exists, `brightdata` key already there with same URL → no-op.
- File exists, `brightdata` key with **different** URL → show diff, ask user: replace, append `&pro=1`, or skip.

Always show the diff before writing.

### Step 2: User-level alternative

Mention that the same block can go in `~/.kiro/settings/mcp.json` instead, for users who want it across every project.

### Step 3: Token onboarding inline check

If `BRIGHTDATA_API_KEY` is unset and the project-level `mcp.json` doesn't have a hardcoded token, instruct the user to set it before continuing. Do not skip to step 4.

In greenfield mode (no project shell context), the power offers to set the env var inline for the smoke test only (not persisted) — `BRIGHTDATA_API_KEY=<token> python scrape.py`. The user is told to add it to their shell profile or `.env` afterward.

### Step 4: Smoke test

Run the generated scraper on the user's target URL with a 1-page sample (or 1-3 items, whichever is faster). Show the result.

- Empty result or all-null fields → **return to Phase 2 reconnaissance**, fix selectors, regenerate the affected module, re-run smoke test. Do not declare done.
- Partial result → ask user if it's good enough or to iterate.
- Clean result → proceed to step 5.

### Step 5: README & wrap-up

Append a `## Bright Data MCP` section to `README.md`:

```markdown
## Bright Data MCP

This project has the Bright Data MCP server configured (`.kiro/settings/mcp.json`).
Any AI agent (Claude Code, Cursor, Cline, Kiro) running against this project
gains live web tools — `search_engine`, `scrape_as_markdown`, and structured-data
extractors for 40+ platforms.

To enable the full 60+ Pro tools (e.g., `web_data_amazon_product`,
`web_data_linkedin_person_profile`), append `&pro=1` to the MCP URL in
`.kiro/settings/mcp.json`. To enable specific groups only, use
`&groups=social,ecommerce`.
```

Then summarize to the user: what was added, where, how to call it, and the next-step suggestion (e.g., "want me to schedule this on a cron?" — sets up the v2 power).

## Error handling matrix

| Situation | Power's response |
|-----------|------------------|
| Multiple manifests in monorepo | Ask which sub-project; don't pick |
| Existing `.kiro/settings/mcp.json` with different `brightdata` block | Show diff, offer merge / replace / skip |
| Existing scraper file at target path | Suggest numbered alternative, never overwrite |
| Smoke test returns empty | Re-run Phase 2 reconnaissance, do not claim success |
| Site has a pre-built scraper but user asked for custom | Prefer pre-built, explain why (faster, cheaper, structured), offer override |
| `BRIGHTDATA_API_KEY` unset at smoke-test time | Stop, instruct user, do not skip the test |
| Web framework + agent framework both present | Ask user which surface |
| Language other than Python or TS | Generate Web Unlocker `curl`/HTTP example with note that user adapts it |
| User on greenfield workspace | Default to module pattern, ask Python or TS |

## File templates (canonical)

The implementation plan will produce concrete templates for each of these. They all share a `fetchPage(url)` core that uses the brightdata-plugin scraper-builder skill's pattern (POST to `https://api.brightdata.com/request`, `{zone, url, format: "raw"}`, retries with exponential backoff).

Templates needed:
- TS module + TS module-with-cheerio
- Python module + Python module-with-bs4
- Next.js App Router route
- Next.js Pages Router route
- Express route + Fastify route + Hono route + Koa route
- FastAPI router + Flask blueprint + Django view
- LangChain TS tool + LangChain Python tool
- Anthropic SDK tool (TS + Python)
- OpenAI SDK tool (TS + Python)
- Mastra tool
- Vercel AI SDK tool
- Generic `curl`/HTTP fallback for other languages

## Activation summary

User says any of:
- "scrape \<site\> for \<thing\>"
- "extract \<data\> from \<site\>"
- "add a competitor pricing monitor"
- "give my agent web search"
- "monitor LinkedIn profiles"

→ Kiro matches a keyword, loads the power, the orchestrator runs Phase 1 → 2 → 3 → 4 with confirmation gates between each, and the user ends up with code + MCP tools wired into their existing project.

## Out of scope (recap)

Scheduling, ETL/DB writes, UI components, proxy zone management, multi-site orchestration, languages beyond Python/TS as first-class. Each is deferred to a follow-up power or a different skill.
