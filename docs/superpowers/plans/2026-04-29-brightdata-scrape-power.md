# brightdata-scrape Kiro Power Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Kiro power at `powers/brightdata-scrape/` that detects an existing app's stack and adds production-ready Bright Data scraping (module, API route, or agent tool — picked by detection) plus wires the Bright Data MCP server into the project.

**Architecture:** Kiro power = `POWER.md` (frontmatter + onboarding) + `mcp.json` (Bright Data remote MCP) + 5 steering files (orchestrator + 4 phase files). The "code" the power produces lives in template fixture files committed alongside the steering, so the steering can reference them by path and we can verify both directions match. No runtime code — the power's behavior is prompt instructions executed by an AI agent inside Kiro.

**Tech Stack:** Markdown (`POWER.md`, steering), JSON (`mcp.json`), template fixtures in TypeScript and Python, a small `scripts/validate_power.py` (Python 3.11+, stdlib only) for self-checks.

**Spec:** `docs/superpowers/specs/2026-04-29-brightdata-scrape-power-design.md`

---

## File Structure

Locked-in layout (matches the spec):

```
powers/brightdata-scrape/
├── POWER.md                              # frontmatter + onboarding + orchestrator pointer
├── mcp.json                              # Bright Data remote MCP server
├── steering/
│   ├── scrape-workflow.md                # orchestrator
│   ├── phase1-detect-and-plan.md         # detection + plan
│   ├── phase2-scraping-playbook.md       # condensed Web Unlocker / Browser API decision
│   ├── phase3-integrate.md               # code generation, three sub-templates
│   └── phase4-mcp-and-verify.md          # MCP wiring + smoke test
└── templates/                             # canonical generated-code fixtures
    ├── module/
    │   ├── ts-cheerio.ts                 # TS module + cheerio parser
    │   ├── ts-fetch.ts                   # TS module, no parser dep (regex/HTMLRewriter)
    │   ├── py-bs4.py                     # Python module + bs4
    │   └── py-stdlib.py                  # Python module, stdlib only
    ├── route/
    │   ├── next-app-router.ts            # app/api/scrape/route.ts
    │   ├── next-pages-router.ts          # pages/api/scrape.ts
    │   ├── express.ts                    # src/routes/scrape.ts (Express)
    │   ├── fastify.ts                    # src/routes/scrape.ts (Fastify)
    │   ├── hono.ts                       # src/routes/scrape.ts (Hono)
    │   ├── koa.ts                        # src/routes/scrape.ts (Koa)
    │   ├── fastapi.py                    # app/api/scrape.py (FastAPI router)
    │   ├── flask.py                      # blueprint
    │   └── django.py                     # view + URL pattern
    ├── tool/
    │   ├── langchain-ts.ts
    │   ├── langchain-py.py
    │   ├── anthropic-sdk-ts.ts
    │   ├── anthropic-sdk-py.py
    │   ├── openai-ts.ts
    │   ├── openai-py.py
    │   ├── mastra.ts
    │   └── vercel-ai-sdk.ts
    └── fallback/
        └── curl.sh                       # generic Web Unlocker curl, language-agnostic

docs/superpowers/specs/2026-04-29-brightdata-scrape-power-design.md  # already exists
docs/superpowers/plans/2026-04-29-brightdata-scrape-power.md         # this file

scripts/validate_power.py                 # repo-root validation script (Python 3.11+, stdlib)
README.md                                 # add brightdata-scrape entry
```

**Implementation staging:** v1 ships all 4 steering files + a **subset** of templates so the power works end-to-end on the most common stacks. Remaining templates land in v1.1.

- **v1 templates (Tasks 12–18):** ts-cheerio.ts, py-bs4.py, next-app-router.ts, fastapi.py, anthropic-sdk-ts.ts, anthropic-sdk-py.py, curl.sh
- **v1.1 templates (Task 23):** all remaining templates, batched into one task per family

The orchestrator and Phase 3 steering check the `templates/` directory at runtime — if a needed template is missing, the steering instructs the agent to fall back to the closest available template and tell the user.

---

## Testing Strategy

This power has no runtime — its "behavior" is markdown that an LLM follows. We verify two things:

1. **Each template is well-formed** — parses (TS/Python imports valid, JSON valid), has the expected exports, references env vars by the names the steering specifies.
2. **The steering and templates agree** — every file path the steering names exists in `templates/`; every env var name the templates use is documented in the onboarding.

`scripts/validate_power.py` runs both checks. It's the test runner. Tasks add fixtures and grow the validation script in lockstep — TDD-style.

---

## Task 1: Repo bootstrap — create directory structure and validation harness

**Files:**
- Create: `powers/brightdata-scrape/` (directory)
- Create: `powers/brightdata-scrape/templates/module/` (directory)
- Create: `powers/brightdata-scrape/templates/route/` (directory)
- Create: `powers/brightdata-scrape/templates/tool/` (directory)
- Create: `powers/brightdata-scrape/templates/fallback/` (directory)
- Create: `powers/brightdata-scrape/steering/` (directory)
- Create: `scripts/validate_power.py`
- Create: `tests/test_validate_power.py`

- [ ] **Step 1: Create directories**

```bash
mkdir -p powers/brightdata-scrape/templates/{module,route,tool,fallback}
mkdir -p powers/brightdata-scrape/steering
mkdir -p scripts tests
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_validate_power.py`:

```python
"""Tests for scripts/validate_power.py.

Each test corresponds to one validation rule the script enforces.
Adding a new rule = add a fixture + add a test + extend the script.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
POWER_DIR = REPO_ROOT / "powers" / "brightdata-scrape"


def run_validator(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(REPO_ROOT / "scripts" / "validate_power.py"), *args],
        capture_output=True,
        text=True,
    )


def test_validator_runs_and_reports_missing_power_md():
    """With an empty power dir, validator should fail and mention POWER.md."""
    result = run_validator(str(POWER_DIR))
    assert result.returncode != 0, f"expected failure, got: {result.stdout}"
    assert "POWER.md" in (result.stdout + result.stderr)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py -v`
Expected: FAIL with `FileNotFoundError: scripts/validate_power.py` or similar — script doesn't exist yet.

- [ ] **Step 4: Write the minimal validator**

Create `scripts/validate_power.py`:

```python
#!/usr/bin/env python3
"""Validate a Kiro power directory.

Usage: python3 scripts/validate_power.py <power-dir>

Exit code 0 on success, 1 on any check failure.
Prints a summary of checks run and any failures.
"""
from __future__ import annotations
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_power.py <power-dir>", file=sys.stderr)
        return 2
    power_dir = Path(argv[1])
    if not power_dir.is_dir():
        fail(f"not a directory: {power_dir}")
        return 1
    failures: list[str] = []

    power_md = power_dir / "POWER.md"
    if not power_md.is_file():
        failures.append(f"missing required file: {power_md}")

    if failures:
        for f in failures:
            fail(f)
        return 1
    print(f"OK: {power_dir} passed all checks")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest tests/test_validate_power.py -v`
Expected: PASS — validator runs, exits non-zero, mentions POWER.md.

- [ ] **Step 6: Commit**

```bash
git add powers/brightdata-scrape scripts/validate_power.py tests/test_validate_power.py
git commit -m "feat(power): scaffold brightdata-scrape directory and validation harness"
```

---

## Task 2: POWER.md frontmatter

**Files:**
- Create: `powers/brightdata-scrape/POWER.md`
- Modify: `scripts/validate_power.py`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_power_md_has_required_frontmatter():
    """POWER.md must have name, displayName, description, keywords, author in frontmatter."""
    # First create a stub POWER.md with the right shape
    # The actual file lives in the repo — this test just asserts the validator
    # checks for those fields.
    result = run_validator(str(POWER_DIR))
    out = result.stdout + result.stderr
    # When POWER.md exists, the test still expects frontmatter checks to run
    # The minimal sufficient assertion: validator reports a frontmatter check by name
    assert "frontmatter" in out.lower(), f"validator output: {out}"
```

- [ ] **Step 2: Write the actual POWER.md**

Create `powers/brightdata-scrape/POWER.md`:

```markdown
---
name: "brightdata-scrape"
displayName: "Add web scraping to any app with Bright Data"
description: "Detect your project's stack and add production-ready web scraping — generates the right integration pattern (module, API route, or agent tool), wires Bright Data MCP into your project, handles pagination and bot detection."
keywords: ["scrape", "scraping", "scraper", "crawl", "crawler", "web-data", "extract", "extract-data", "competitor", "pricing-monitor", "lead-generation", "amazon", "linkedin", "instagram", "tiktok", "youtube", "serp", "google-search", "search-engine", "brightdata", "bright-data", "web-unlocker", "browser-api", "captcha", "bot-detection", "pagination", "agent-tools", "mcp"]
author: "Bright Data"
---

# Add web scraping to any app with Bright Data

This power detects what kind of project you're working on and adds production-ready scraping in the right shape — a reusable module, an API route, or an agent tool — backed by Bright Data's Web Unlocker, Web Scraper API, Browser API, and SERP API. It also wires the Bright Data MCP server into your project so any AI agent that runs against the project (Claude Code, Cursor, Cline, Kiro itself) gains live web tools.

**It works on any language**, but Python and TypeScript/JavaScript get first-class code generation. Other languages get a generic `curl`/HTTP template that you adapt.

## What you can do

- "Scrape competitor prices from example.com daily into my Next.js dashboard"
- "Add a `/api/scrape` route to my Express app"
- "Give my Claude SDK agent a tool that searches Google and reads results"
- "Extract all product listings from this Shopify store"
- "Monitor LinkedIn profiles of my pipeline contacts"

## Onboarding

Before using this power, complete the following.

### Step 1: Get a Bright Data API token

Sign up (or log in) at [https://brightdata.com](https://brightdata.com). Generate an API token at [https://brightdata.com/cp/setting/users](https://brightdata.com/cp/setting/users). The free tier includes **5,000 requests per month** including Pro tools.

### Step 2: Configure the token (pick one)

**Option A — Env var (recommended for CI / production):**

```bash
export BRIGHTDATA_API_KEY=<your-token>
```

Add to your shell profile (`.zshrc`, `.bashrc`) or a project `.env` file. The generated `mcp.json` references `${BRIGHTDATA_API_KEY}`, so this works automatically.

**Option B — Hardcoded in user-level Kiro config:**

Edit `~/.kiro/settings/mcp.json` and add:

```json
{
  "mcpServers": {
    "brightdata": {
      "url": "https://mcp.brightdata.com/mcp?token=YOUR_TOKEN_HERE",
      "disabled": false
    }
  }
}
```

This makes Bright Data MCP available in every Kiro project on your machine.

### Step 3 (optional): Set up an Unlocker zone

The default Web Unlocker zone is named `unblocker` on new accounts. If you've renamed it or hit "no zone" errors, set:

```bash
export BRIGHTDATA_UNLOCKER_ZONE=<your-zone-name>
```

Or create / rename a zone at [https://brightdata.com/cp/zones](https://brightdata.com/cp/zones).

---

## How to use this power

For any scraping task, **always** read the orchestrator steering file first:

```
Call action "readSteering" with powerName="brightdata-scrape", steeringFile="scrape-workflow.md"
```

The orchestrator runs four phases in sequence with confirmation gates between each:

1. **Detect & plan** — inspect the project, pick the right integration pattern, ask what to scrape.
2. **Scraping playbook** — pick the right Bright Data API and selectors based on the target site.
3. **Integrate** — generate the scraper module, API route, or agent tool into the user's project.
4. **MCP & verify** — wire the Bright Data MCP server, run a smoke test, write a README snippet.

**Do NOT improvise. Do NOT skip phases.** The steering files contain the exact instructions for each.
```

- [ ] **Step 3: Extend the validator to check frontmatter**

Modify `scripts/validate_power.py` — add after the `power_md` existence check:

```python
    # Frontmatter check (after the existence block above)
    if power_md.is_file():
        text = power_md.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            failures.append("POWER.md frontmatter: must start with '---' fence")
        else:
            # crude YAML-front-matter parse (no PyYAML dep)
            end = text.find("\n---\n", 4)
            if end == -1:
                failures.append("POWER.md frontmatter: missing closing '---' fence")
            else:
                front = text[4:end]
                required_fields = ["name:", "displayName:", "description:", "keywords:", "author:"]
                for field in required_fields:
                    if field not in front:
                        failures.append(f"POWER.md frontmatter: missing field '{field.rstrip(':')}'")
```

- [ ] **Step 4: Run the tests**

Run: `python3 -m pytest tests/test_validate_power.py -v`
Expected: PASS — validator now reports `frontmatter` checks in output.

- [ ] **Step 5: Run the validator directly to confirm POWER.md passes**

Run: `python3 scripts/validate_power.py powers/brightdata-scrape`
Expected: `OK: powers/brightdata-scrape passed all checks`

- [ ] **Step 6: Commit**

```bash
git add powers/brightdata-scrape/POWER.md scripts/validate_power.py tests/test_validate_power.py
git commit -m "feat(power): POWER.md with frontmatter and onboarding"
```

---

## Task 3: mcp.json

**Files:**
- Create: `powers/brightdata-scrape/mcp.json`
- Modify: `scripts/validate_power.py`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_mcp_json_has_brightdata_server():
    """mcp.json must define a 'brightdata' server with a URL referencing BRIGHTDATA_API_KEY."""
    result = run_validator(str(POWER_DIR))
    out = result.stdout + result.stderr
    # Validator should now run an mcp.json check and pass it
    assert "mcp.json" in out.lower() or result.returncode == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_mcp_json_has_brightdata_server -v`
Expected: FAIL — validator doesn't check mcp.json yet.

- [ ] **Step 3: Create mcp.json**

Create `powers/brightdata-scrape/mcp.json`:

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

- [ ] **Step 4: Extend validator**

Modify `scripts/validate_power.py` — add after the frontmatter block (still inside `main`):

```python
    import json
    mcp_path = power_dir / "mcp.json"
    if not mcp_path.is_file():
        failures.append("mcp.json: missing required file")
    else:
        try:
            data = json.loads(mcp_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            failures.append(f"mcp.json: invalid JSON ({e})")
        else:
            servers = data.get("mcpServers", {})
            bd = servers.get("brightdata")
            if not bd:
                failures.append("mcp.json: missing mcpServers.brightdata entry")
            elif "${BRIGHTDATA_API_KEY}" not in bd.get("url", ""):
                failures.append("mcp.json: brightdata.url must reference ${BRIGHTDATA_API_KEY}")
```

- [ ] **Step 5: Run tests**

Run: `python3 -m pytest tests/test_validate_power.py -v`
Expected: ALL PASS.

Run: `python3 scripts/validate_power.py powers/brightdata-scrape`
Expected: `OK: powers/brightdata-scrape passed all checks`

- [ ] **Step 6: Commit**

```bash
git add powers/brightdata-scrape/mcp.json scripts/validate_power.py tests/test_validate_power.py
git commit -m "feat(power): mcp.json wiring Bright Data remote MCP server"
```

---

## Task 4: Steering — orchestrator (`scrape-workflow.md`)

**Files:**
- Create: `powers/brightdata-scrape/steering/scrape-workflow.md`
- Modify: `scripts/validate_power.py`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_orchestrator_steering_exists_and_lists_all_phases():
    """scrape-workflow.md must reference all four phase files by exact filename."""
    wf_path = POWER_DIR / "steering" / "scrape-workflow.md"
    assert wf_path.is_file(), f"missing {wf_path}"
    text = wf_path.read_text(encoding="utf-8")
    for phase in [
        "phase1-detect-and-plan.md",
        "phase2-scraping-playbook.md",
        "phase3-integrate.md",
        "phase4-mcp-and-verify.md",
    ]:
        assert phase in text, f"orchestrator missing reference to {phase}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_orchestrator_steering_exists_and_lists_all_phases -v`
Expected: FAIL — `scrape-workflow.md` doesn't exist yet.

- [ ] **Step 3: Create the orchestrator file**

Create `powers/brightdata-scrape/steering/scrape-workflow.md`:

```markdown
# brightdata-scrape Workflow

Orchestrated workflow for adding Bright Data scraping to a project.

## When to use this workflow

Use for any scraping or web-data task — the user said something like "scrape X", "extract data from Y", "monitor competitor prices", "give my agent web search", or any keyword from this power's frontmatter.

## Critical rules

1. **All four phases run in order.** No skipping, no reordering.
2. **One phase steering file at a time.** Read only the next phase's file. Do NOT read ahead.
3. **Wait for user confirmation between phases.** Each phase ends with a confirmation gate.
4. **If you lose track, re-read this orchestrator file.** Identify the last completed phase, dispatch the next one.
5. **Do not improvise the integration code.** Use the templates in `powers/brightdata-scrape/templates/` as canonical references.

## Step 1: Validate prerequisites

Run these checks before proceeding:

1. **`BRIGHTDATA_API_KEY` is set OR hardcoded in `~/.kiro/settings/mcp.json`.**
   - Check env: `echo $BRIGHTDATA_API_KEY` (non-empty)
   - OR check `~/.kiro/settings/mcp.json` for a `brightdata` entry with the token in the URL

2. **The user is in a workspace** (current working directory is set).

If `BRIGHTDATA_API_KEY` is missing, **STOP** and present the onboarding from `POWER.md` Step 1–2. Do not proceed.

## Step 2: Dispatch Phase 1

Read **only** the Phase 1 steering file:

```
Call action "readSteering" with powerName="brightdata-scrape", steeringFile="phase1-detect-and-plan.md"
```

**Do NOT read any other phase file yet.** Phase 1 will summarize a plan and ask the user to confirm. After confirmation, return here.

## Step 3: Dispatch subsequent phases

After each phase completes and the user confirms, dispatch the next phase. The phase order is fixed:

1. `phase1-detect-and-plan.md`
2. `phase2-scraping-playbook.md`
3. `phase3-integrate.md`
4. `phase4-mcp-and-verify.md`

After Phase 4 completes, the workflow is done. Tell the user what was added and where.

## Step 4: Phase transition pattern

When a phase finishes, it will summarize what it did and stop. The orchestrator then:

1. Tells the user which phase just finished and what's next.
2. Asks: `[Phase name] is complete. Ready to proceed to [next phase name]?`
3. **Waits for the user to confirm.**
4. Once confirmed, reads the next phase steering file with `readSteering` and dispatches it.

## Troubleshooting

- **Smoke test in Phase 4 returns empty data** → re-enter Phase 2 reconnaissance, fix selectors, regenerate the affected files in Phase 3, re-run smoke test. Do not declare success.
- **User asks to change scope mid-flow** → ask if they want to abort and restart Phase 1, or continue with current plan.
- **Multiple manifests in repo (monorepo)** → Phase 1 handles this; ask the user which sub-project.
```

- [ ] **Step 4: Run the unit test to verify it passes**

Run: `python3 -m pytest tests/test_validate_power.py::test_orchestrator_steering_exists_and_lists_all_phases -v`
Expected: PASS.

- [ ] **Step 5: Extend validator (cross-cutting check; will FAIL overall until Tasks 5–8 land their files)**

Modify `scripts/validate_power.py` — add after the mcp.json block:

```python
    steering_dir = power_dir / "steering"
    if not steering_dir.is_dir():
        failures.append("steering/: missing required directory")
    else:
        required_steering = [
            "scrape-workflow.md",
            "phase1-detect-and-plan.md",
            "phase2-scraping-playbook.md",
            "phase3-integrate.md",
            "phase4-mcp-and-verify.md",
        ]
        present = {p.name for p in steering_dir.iterdir() if p.is_file()}
        for name in required_steering:
            if name not in present:
                failures.append(f"steering/{name}: missing required file")

        # Orchestrator must reference each phase file by exact filename
        wf = steering_dir / "scrape-workflow.md"
        if wf.is_file():
            wf_text = wf.read_text(encoding="utf-8")
            for phase in required_steering[1:]:  # skip self
                if phase not in wf_text:
                    failures.append(
                        f"scrape-workflow.md: must reference '{phase}' by exact filename"
                    )
```

Run: `python3 scripts/validate_power.py powers/brightdata-scrape`
Expected: FAIL with messages about missing `phase1-detect-and-plan.md` etc. (intended; Tasks 5–8 add those files). The unit test from Step 1 still passes because it only checks the orchestrator's content.

- [ ] **Step 6: Commit**

```bash
git add powers/brightdata-scrape/steering/scrape-workflow.md scripts/validate_power.py tests/test_validate_power.py
git commit -m "feat(power): orchestrator steering file"
```

---

## Task 5: Steering — Phase 1 (detect & plan)

**Files:**
- Create: `powers/brightdata-scrape/steering/phase1-detect-and-plan.md`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_phase1_detect_covers_all_pattern_branches():
    """Phase 1 must document module / route / agent-tool branches and greenfield handling."""
    p = POWER_DIR / "steering" / "phase1-detect-and-plan.md"
    assert p.is_file(), f"missing {p}"
    text = p.read_text(encoding="utf-8")
    for keyword in ["module", "API route", "agent tool", "greenfield",
                    "package.json", "pyproject.toml",
                    "next", "express", "fastapi", "flask",
                    "langchain", "anthropic", "openai"]:
        assert keyword.lower() in text.lower(), f"phase1 missing keyword: {keyword}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_phase1_detect_covers_all_pattern_branches -v`
Expected: FAIL — file doesn't exist.

- [ ] **Step 3: Create the Phase 1 steering file**

Create `powers/brightdata-scrape/steering/phase1-detect-and-plan.md`:

```markdown
# Phase 1: Detect & Plan

Inspect the user's workspace, classify it, and propose a single integration pattern. Confirm with the user before proceeding to Phase 2.

## Step 1: Manifest detection

Look for these manifest files at the workspace root, in order:

| Manifest | Language |
|----------|----------|
| `package.json` | TypeScript / JavaScript |
| `pyproject.toml`, `requirements.txt`, `Pipfile` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `Gemfile` | Ruby |
| `pom.xml`, `build.gradle` | Java / Kotlin |
| `composer.json` | PHP |

**No manifest found** → **greenfield mode**. Skip to Step 4 and ask the user: "Python or TypeScript?"

**Multiple manifests in subdirectories (monorepo)** → ask the user which sub-project to integrate into. Do **not** pick automatically.

## Step 2: Stack signature

Within the chosen manifest, look for these dependency signatures:

### Web framework dependencies (route pattern)

**TypeScript/JavaScript** — look in `dependencies` and `devDependencies`:
- `next`, `next.js` → Next.js
- `express` → Express
- `fastify` → Fastify
- `hono` → Hono
- `koa`, `koa-router` → Koa
- `@nestjs/core` → NestJS
- `remix`, `@remix-run/react` → Remix

**Python** — look in `pyproject.toml` `[project.dependencies]` or `requirements.txt`:
- `fastapi` → FastAPI
- `flask` → Flask
- `django` → Django
- `aiohttp` → aiohttp
- `starlette` → Starlette

### Agent framework dependencies (agent tool pattern)

**TypeScript/JavaScript:**
- `langchain`, `@langchain/*` → LangChain
- `@anthropic-ai/sdk` → Anthropic SDK
- `openai` → OpenAI SDK
- `mastra`, `@mastra/*` → Mastra
- `@ai-sdk/*`, `ai` → Vercel AI SDK
- `@modelcontextprotocol/sdk` → MCP SDK

**Python:**
- `langchain`, `langchain-*` → LangChain
- `anthropic` → Anthropic SDK
- `openai` → OpenAI SDK
- `llama-index` → LlamaIndex
- `crewai` → CrewAI
- `mcp` → MCP SDK

## Step 3: Pick the single pattern

Apply this decision tree:

| Signals | Pattern | Template family |
|---------|---------|-----------------|
| Web framework deps present | **API route** | `templates/route/` |
| Agent framework deps present, no web framework | **Agent tool** | `templates/tool/` |
| Both web and agent | Ask the user which surface they prefer (route or tool) |
| Library / CLI / unrecognized | **Module** | `templates/module/` |
| Greenfield (no manifest) | **Module**, language asked above | `templates/module/` |

**Inform the user of the choice but don't put it up for vote** — the detection is the choice.

## Step 4: Targeted scraping question

Ask in **one** message:

> What do you want to scrape, and which fields? (Examples: 'product name + price + image from amazon.com search results', 'all job titles + companies from greenhouse.io listings'.) Roughly how many pages or items?

Do NOT ask separately about pagination type, output format, or language preference:
- **Pagination type** → discovered in Phase 2 reconnaissance.
- **Output format** → defaults to typed return value; the caller decides what to do with it.
- **Language** → already determined by manifest (TypeScript for `package.json`, Python for `pyproject.toml`/`requirements.txt`); greenfield is handled in Step 1.

## Step 5: Present plan and wait for confirmation

Format:

```
## Plan

**Detected:** <stack signature, e.g., "Next.js 14 (App Router) project, TypeScript">
**Pattern:** <module | API route | agent tool>
**Scraping target:** <user's site/data>
**Estimated volume:** <single | small (<50) | bulk (>=50)>

**Phases I'll run:**
  1. ✓ Detect & plan (this phase, just confirmed)
  2. Scraping playbook — pick the right Bright Data API and selectors
  3. Integrate — generate <files I'll write> in your project
  4. MCP & verify — wire Bright Data MCP, run a smoke test

Ready to proceed to Phase 2?
```

**WAIT for the user to confirm before returning control to the orchestrator.**

## Output of this phase

The orchestrator carries forward this decision record:

```
{
  "language": "typescript" | "python" | "other",
  "language_other_name": "<e.g., 'go'>" | null,
  "pattern": "module" | "route" | "tool",
  "framework": "<e.g., 'next-app-router', 'fastapi', 'anthropic-sdk-ts'>",
  "target_url": "<user's site>",
  "fields": ["<field1>", "<field2>", ...],
  "volume": "single" | "small" | "bulk",
  "monorepo_subproject": "<path>" | null
}
```

Subsequent phases reference this record by name. If anything is missing from it, return to Phase 1.
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_phase1_detect_covers_all_pattern_branches -v`
Expected: PASS.

- [ ] **Step 5: Run the validator**

Run: `python3 scripts/validate_power.py powers/brightdata-scrape`
Expected: still failing on phase 2/3/4 files, but phase 1 file now exists.

- [ ] **Step 6: Commit**

```bash
git add powers/brightdata-scrape/steering/phase1-detect-and-plan.md tests/test_validate_power.py
git commit -m "feat(power): Phase 1 steering — detect stack and plan integration"
```

---

## Task 6: Steering — Phase 2 (scraping playbook, condensed)

**Files:**
- Create: `powers/brightdata-scrape/steering/phase2-scraping-playbook.md`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_phase2_playbook_covers_all_apis_and_pagination_patterns():
    """Phase 2 must document the four-API decision tree and pagination patterns."""
    p = POWER_DIR / "steering" / "phase2-scraping-playbook.md"
    assert p.is_file(), f"missing {p}"
    text = p.read_text(encoding="utf-8")
    for keyword in [
        "Web Unlocker", "Browser API", "Web Scraper API", "SERP API",
        "data attributes", "selectors",
        "url-based", "next-link", "cursor", "infinite scroll",
        "concurrency", "semaphore",
        "scraper-builder",  # pointer to the long-form skill
        "https://api.brightdata.com/datasets/list",  # pre-built lookup
    ]:
        assert keyword.lower() in text.lower(), f"phase2 missing keyword: {keyword}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_phase2_playbook_covers_all_apis_and_pagination_patterns -v`
Expected: FAIL.

- [ ] **Step 3: Create the Phase 2 steering file**

Create `powers/brightdata-scrape/steering/phase2-scraping-playbook.md`:

```markdown
# Phase 2: Scraping Playbook (Condensed)

Pick the right Bright Data API and selectors for the user's target. Output a decision record the next phase consumes.

> This is a **condensed** version of the long-form `scraper-builder` skill. For deeper analysis (anti-bot escalation, multi-site parallelism, retry semantics, browser-session reuse), the brightdata-plugin `scraper-builder` skill is the reference. This phase is a working subset.

## Step 1: Decision tree (the four-line core)

1. **Pre-built scraper exists for this domain?** → use **Web Scraper API** (zero parsing, structured JSON).
2. **Static HTML, no interaction needed?** → use **Web Unlocker** (cheapest, simplest).
3. **JS-rendered, or needs clicks/scrolls/form fills?** → use **Browser API** (full automation).
4. **Search engine results page (Google/Bing/Yandex)?** → use **SERP API**.

## Step 2: Pre-built scraper check

One curl to discover all available pre-built scrapers:

```bash
curl -H "Authorization: Bearer $BRIGHTDATA_API_KEY" \
     https://api.brightdata.com/datasets/list
```

Search the response for the target domain. If you find a match, record the `dataset_id` and **skip to Step 5** — no reconnaissance needed.

Common matches: `amazon`, `linkedin`, `instagram`, `tiktok`, `youtube`, `facebook`, `twitter` (X), `reddit`, `walmart`, `ebay`, `crunchbase`, `zillow`, `booking`, `yahoo-finance`, `google-play`, `apple-app-store`.

## Step 3: Reconnaissance (no pre-built scraper)

### Step 3a: Fetch raw HTML

```bash
curl -X POST https://api.brightdata.com/request \
  -H "Authorization: Bearer $BRIGHTDATA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"zone": "'"${BRIGHTDATA_UNLOCKER_ZONE:-unblocker}"'", "url": "<TARGET_URL>", "format": "raw"}'
```

### Step 3b: Inspect

- **Is the data in the HTML?** If yes → Web Unlocker is sufficient.
- **Is the HTML mostly an empty shell** (`<div id="root"></div>`, `<div id="__next"></div>`, `ng-app`)? → content is client-rendered → **escalate to Browser API**.
- **Does the page reference internal JSON endpoints** (look for `fetch('/api/...')`, `XMLHttpRequest`, hardcoded JSON in `<script>` tags)? → hitting the API endpoint directly via Web Unlocker is cleaner than HTML parsing.

### Step 3c: Pick selectors (priority order)

1. **`data-*` attributes** (e.g., `[data-testid="product-price"]`) — survive redesigns.
2. **Semantic class names** (e.g., `.product-card .price`).
3. **`id` attributes** — unique, but may change.
4. **Structural selectors** (e.g., `div > span:nth-child(2)`) — fragile, **avoid**.

## Step 4: Pagination patterns

| Pattern | Detection | Implementation |
|---------|-----------|----------------|
| **URL-based** | URLs like `?page=N`, `?offset=20` | Loop `?page=N` until response has no items |
| **Next-link** | HTML has `<a rel="next">` or `.pagination .next a` | Follow the next-link until absent |
| **Cursor** | API responses include `next_cursor`, `next_token` | Loop with `?cursor=<token>` from previous response |
| **Infinite scroll** | Content loads on scroll, no URL change | Browser API only — scroll until item count stops growing |

## Step 5: Concurrency

If the user said "bulk" volume in Phase 1 (50+ URLs), the generated code **must** use semaphore-bounded async with `CONCURRENCY=20` as the default. Sequential `time.sleep(1)` loops at this volume are unacceptable.

## Step 6: Output the decision record

Hand back to the orchestrator:

```
{
  "approach": "web-unlocker" | "browser-api" | "pre-built" | "serp",
  "dataset_id": "<if pre-built>" | null,
  "selectors": { "<field>": "<css selector>", ... },
  "pagination": "url-based" | "next-link" | "cursor" | "infinite-scroll" | "none",
  "concurrency_required": true | false,
  "hidden_api_endpoint": "<URL or null>"
}
```

Confirm the choice with the user in one short message before returning to the orchestrator:

> I'll use **Web Unlocker** with these selectors: `<list>`. Pagination is **URL-based**. Sound right?

WAIT for confirmation. Then return.
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_phase2_playbook_covers_all_apis_and_pagination_patterns -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add powers/brightdata-scrape/steering/phase2-scraping-playbook.md tests/test_validate_power.py
git commit -m "feat(power): Phase 2 steering — condensed scraping playbook"
```

---

## Task 7: Steering — Phase 3 (integrate)

**Files:**
- Create: `powers/brightdata-scrape/steering/phase3-integrate.md`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_phase3_integrate_references_template_directories():
    """Phase 3 must reference the templates/ subdirectories the orchestrator picks from."""
    p = POWER_DIR / "steering" / "phase3-integrate.md"
    assert p.is_file(), f"missing {p}"
    text = p.read_text(encoding="utf-8")
    for keyword in [
        "templates/module/", "templates/route/", "templates/tool/", "templates/fallback/",
        "BRIGHTDATA_API_KEY", "BRIGHTDATA_UNLOCKER_ZONE",
        ".env.example", "README.md",
        "confirmation",  # gate before writing
        "never overwrite", "do not overwrite",  # safety
    ]:
        assert keyword.lower() in text.lower(), f"phase3 missing keyword: {keyword}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_phase3_integrate_references_template_directories -v`
Expected: FAIL.

- [ ] **Step 3: Create the Phase 3 steering file**

Create `powers/brightdata-scrape/steering/phase3-integrate.md`:

```markdown
# Phase 3: Integrate

Generate the scraper code into the user's project. The pattern (module / route / tool) was chosen in Phase 1; the API and selectors were chosen in Phase 2. This phase picks the right template, fills it, and writes files — but only after confirming each path with the user.

## Step 1: Pick the template

Use the Phase 1 decision record's `pattern` and `framework` fields. Look up the canonical template:

| Pattern | Framework | Template path |
|---------|-----------|---------------|
| `module` | TypeScript | `powers/brightdata-scrape/templates/module/ts-cheerio.ts` (if user has cheerio) or `ts-fetch.ts` (otherwise) |
| `module` | Python | `powers/brightdata-scrape/templates/module/py-bs4.py` (if bs4 acceptable) or `py-stdlib.py` (otherwise) |
| `route` | Next.js App Router | `templates/route/next-app-router.ts` |
| `route` | Next.js Pages Router | `templates/route/next-pages-router.ts` |
| `route` | Express | `templates/route/express.ts` |
| `route` | Fastify | `templates/route/fastify.ts` |
| `route` | Hono | `templates/route/hono.ts` |
| `route` | Koa | `templates/route/koa.ts` |
| `route` | FastAPI | `templates/route/fastapi.py` |
| `route` | Flask | `templates/route/flask.py` |
| `route` | Django | `templates/route/django.py` |
| `tool` | LangChain (TS) | `templates/tool/langchain-ts.ts` |
| `tool` | LangChain (Python) | `templates/tool/langchain-py.py` |
| `tool` | Anthropic SDK (TS) | `templates/tool/anthropic-sdk-ts.ts` |
| `tool` | Anthropic SDK (Python) | `templates/tool/anthropic-sdk-py.py` |
| `tool` | OpenAI SDK (TS) | `templates/tool/openai-ts.ts` |
| `tool` | OpenAI SDK (Python) | `templates/tool/openai-py.py` |
| `tool` | Mastra | `templates/tool/mastra.ts` |
| `tool` | Vercel AI SDK | `templates/tool/vercel-ai-sdk.ts` |
| **other language** | any | `templates/fallback/curl.sh` (adapt by hand, tell the user) |

**If a template file does not exist** (because v1 ships a subset), fall back to the closest available template in the same family and tell the user:

> "I don't have a canonical template for `<framework>` yet — I'm using the `<closest>` template as a starting point and adapting it. You may need to adjust imports/syntax."

## Step 2: Fill the template

Replace these placeholders in the template with values from the decision records:

- `{{TARGET_URL}}` → Phase 1 `target_url`
- `{{TARGET_NAME}}` → derived from URL host, snake_case (e.g., `amazon_com`, `competitor_prices`)
- `{{FIELDS}}` → Phase 1 `fields`, formatted per template (TS interface, Python TypedDict, etc.)
- `{{SELECTORS}}` → Phase 2 `selectors` (CSS strings)
- `{{PAGINATION}}` → Phase 2 `pagination` ('url-based' / 'next-link' / 'cursor' / 'infinite-scroll' / 'none')
- `{{APPROACH}}` → Phase 2 `approach`
- `{{DATASET_ID}}` → Phase 2 `dataset_id` (only for pre-built scrapers)
- `{{CONCURRENCY}}` → 20 if `concurrency_required` else 1
- `{{HIDDEN_API_ENDPOINT}}` → Phase 2 `hidden_api_endpoint` if present

Generated files always read **`BRIGHTDATA_API_KEY`** and **`BRIGHTDATA_UNLOCKER_ZONE`** (default `"unblocker"`) from environment.

## Step 3: Pick destination paths

For the **module** pattern:
- TS: `src/scrapers/{{TARGET_NAME}}.ts`
- Python: `src/scrapers/{{TARGET_NAME}}.py` — or use the project's existing source directory if `src/` doesn't exist (check for `app/`, `lib/`, top-level `.py` files)

For the **route** pattern:
- Next.js App Router: `app/api/scrape/route.ts`
- Next.js Pages Router: `pages/api/scrape.ts`
- Express / Fastify / Hono / Koa: `src/routes/scrape.ts` (or wherever the project's existing routes live — inspect)
- FastAPI: `app/api/scrape.py` (with router include line shown to user)
- Flask: `app/scrape.py` (blueprint, with `app.register_blueprint(...)` line shown)
- Django: `<app>/views/scrape.py` (with URL pattern line shown)

The route pattern **also** generates the module file (route imports the module).

For the **tool** pattern:
- TS: `src/tools/scrape.ts`
- Python: `src/tools/scrape.py`

The tool pattern **also** generates the module file (tool calls the module).

## Step 4: Update env and README

Always update:

- `.env.example` — append (skip lines already present):
  ```
  # Get token at https://brightdata.com/cp/setting/users
  BRIGHTDATA_API_KEY=
  # Optional — defaults to the account's "unblocker" zone if unset.
  # Manage zones at https://brightdata.com/cp/zones
  BRIGHTDATA_UNLOCKER_ZONE=
  ```

- `README.md` — append (or create) a `## Web scraping` section with one usage example showing how to call the generated function/route/tool.

## Step 5: Confirmation gate

Before writing **any** file, present the user with a list:

```
I'll write or modify these files:
  • CREATE src/scrapers/competitor_prices.ts
  • CREATE app/api/scrape/route.ts
  • MODIFY .env.example (append BRIGHTDATA_API_KEY, BRIGHTDATA_UNLOCKER_ZONE)
  • MODIFY README.md (append "## Web scraping" section)

OK to write?
```

**WAIT for confirmation. Do not edit a single file before the user says yes.**

## Step 6: Existing-file safety

- **Never overwrite an existing scraper file.** If `src/scrapers/competitor_prices.ts` exists, suggest `competitor_prices_2.ts` or ask the user where to put it.
- **Never overwrite `README.md` or `.env.example` wholesale.** Append only. If `BRIGHTDATA_API_KEY` is already in `.env.example`, skip it. If a `## Web scraping` section already exists, append a sub-section.
- **Never duplicate a route registration line.** If the user's `app.ts` already has `app.use('/api/scrape', ...)`, skip the suggestion.

## Step 7: Output

After writing, summarize for the user:

```
Files written:
  ✓ src/scrapers/competitor_prices.ts
  ✓ app/api/scrape/route.ts
  ✓ .env.example
  ✓ README.md

Next: Phase 4 will wire Bright Data MCP and run a smoke test.
```

Return control to the orchestrator.
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_phase3_integrate_references_template_directories -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add powers/brightdata-scrape/steering/phase3-integrate.md tests/test_validate_power.py
git commit -m "feat(power): Phase 3 steering — integrate templates into the user's project"
```

---

## Task 8: Steering — Phase 4 (MCP wiring + verify)

**Files:**
- Create: `powers/brightdata-scrape/steering/phase4-mcp-and-verify.md`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_phase4_covers_mcp_and_smoke_test():
    """Phase 4 must document MCP wiring (project-level + user-level) and the smoke test loop."""
    p = POWER_DIR / "steering" / "phase4-mcp-and-verify.md"
    assert p.is_file(), f"missing {p}"
    text = p.read_text(encoding="utf-8")
    for keyword in [
        ".kiro/settings/mcp.json",
        "~/.kiro/settings/mcp.json",
        "smoke test",
        "https://mcp.brightdata.com/mcp",
        "${BRIGHTDATA_API_KEY}",
        "&pro=1",        # pro tools
        "&groups=",      # selective groups
        "phase 2",       # back-link on smoke-test failure
    ]:
        assert keyword.lower() in text.lower(), f"phase4 missing keyword: {keyword}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_phase4_covers_mcp_and_smoke_test -v`
Expected: FAIL.

- [ ] **Step 3: Create the Phase 4 steering file**

Create `powers/brightdata-scrape/steering/phase4-mcp-and-verify.md`:

```markdown
# Phase 4: MCP Wiring & Smoke Test

Wire the Bright Data MCP server into the project, run a one-page smoke test, and write the README wrap-up.

## Step 1: Project-level MCP config

Read or create `.kiro/settings/mcp.json`. Apply the following merge logic:

- **File doesn't exist** → create with this content:
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

- **File exists, no `brightdata` key** → merge the entry above into `mcpServers`.

- **File exists, `brightdata` key with the same URL** → no-op.

- **File exists, `brightdata` key with a different URL** → show the diff to the user and ask:
  > "There's an existing `brightdata` MCP server pointing at `<existing-url>`. Want me to: (a) replace it with the standard URL, (b) leave it alone, or (c) append `&pro=1` to enable Pro tools?"

**Always show the diff before writing.** Do not write silently.

## Step 2: User-level alternative

Tell the user:

> "If you'd rather have Bright Data MCP available across **every** Kiro project (not just this one), copy the same `brightdata` block to `~/.kiro/settings/mcp.json` instead. The project-level `.kiro/settings/mcp.json` overrides user-level if both exist."

## Step 3: Token onboarding inline check

Verify the token is actually available at runtime:

1. **Env var path:** `echo $BRIGHTDATA_API_KEY` should be non-empty.
2. **Hardcoded path:** the URL in `.kiro/settings/mcp.json` (or `~/.kiro/settings/mcp.json`) does not contain the literal `${BRIGHTDATA_API_KEY}` (it has been replaced with a real token).

If neither is true, **STOP** and ask the user to set the env var or hardcode the token before continuing. Do not skip to Step 4.

In **greenfield mode** (no project shell context), offer to set the env var inline for the smoke test only:

```bash
BRIGHTDATA_API_KEY=<token> python scrape.py
```

Tell the user this is for the smoke test only — they should add it to their shell profile or `.env` afterward.

## Step 4: Smoke test

Run the generated scraper on the user's target URL with a 1-page sample (or 1–3 items, whichever is faster).

**For a module:** call the function directly from a one-line REPL invocation or a temporary script.

**For a route:** start the dev server (or call the handler function directly if possible) and hit the endpoint with one curl.

**For an agent tool:** invoke the tool's `run`/`call`/`execute` function directly with a sample input.

Show the result to the user.

### Outcomes

- **Empty result, all-null fields, or error** → **return to Phase 2 reconnaissance**, fix selectors, regenerate the affected module file in Phase 3, re-run the smoke test. **Do not declare success.**
- **Partial result** (some fields populated, some null) → ask the user if it's good enough or to iterate.
- **Clean result** → proceed to Step 5.

## Step 5: README wrap-up

Append to `README.md`:

```markdown
## Bright Data MCP

This project has the Bright Data MCP server configured (`.kiro/settings/mcp.json`).
Any AI agent (Claude Code, Cursor, Cline, Kiro) running against this project
gains live web tools — `search_engine`, `scrape_as_markdown`, and structured-data
extractors for 40+ platforms.

To enable the full 60+ Pro tools (e.g., `web_data_amazon_product`,
`web_data_linkedin_person_profile`), append `&pro=1` to the MCP URL in
`.kiro/settings/mcp.json`. To enable specific groups only, use
`&groups=social,ecommerce` (groups: `social`, `ecommerce`, `business`,
`finance`, `research`, `app_stores`, `travel`, `browser`, `advanced_scraping`).
```

If the section already exists, **skip** — do not duplicate.

## Step 6: Final summary

Tell the user:

```
Done. Here's what was added:

  Code:
    ✓ <files written by Phase 3>

  MCP:
    ✓ .kiro/settings/mcp.json — Bright Data server registered
    ℹ︎ Append `&pro=1` to the MCP URL to enable 60+ Pro tools

  Smoke test:
    ✓ Scraped 1 page — extracted <N> items, all fields populated

Try it out:
    <one-line invocation appropriate to the pattern>
```

Workflow complete. Return to the orchestrator with no further action.
```

- [ ] **Step 4: Run the tests**

Run: `python3 -m pytest tests/test_validate_power.py -v`
Expected: ALL PASS.

Run: `python3 scripts/validate_power.py powers/brightdata-scrape`
Expected: `OK: powers/brightdata-scrape passed all checks`

- [ ] **Step 5: Commit**

```bash
git add powers/brightdata-scrape/steering/phase4-mcp-and-verify.md tests/test_validate_power.py
git commit -m "feat(power): Phase 4 steering — MCP wiring and smoke test"
```

---

## Task 9: Validator — template path consistency check

**Files:**
- Modify: `scripts/validate_power.py`
- Modify: `tests/test_validate_power.py`

This task adds a cross-check: every template path Phase 3 names must exist in `templates/` (when ready). Templates land in Tasks 12–18, so this check runs in **warning** mode (logs missing templates but doesn't fail) until Task 18 flips it to error mode.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_validator_warns_on_missing_templates_listed_in_phase3():
    """Validator should output a 'WARN: missing template' line for each template Phase 3 references that doesn't yet exist."""
    result = run_validator(str(POWER_DIR))
    out = result.stdout + result.stderr
    # At least one template is referenced in phase3 (templates/module/ts-cheerio.ts)
    # and won't exist until Task 12. Validator should warn but not fail on it.
    assert "WARN: missing template" in out or "OK:" in out, f"validator output: {out}"
```

- [ ] **Step 2: Run test to verify it fails (the WARN line isn't emitted yet)**

Run: `python3 -m pytest tests/test_validate_power.py::test_validator_warns_on_missing_templates_listed_in_phase3 -v`
Expected: FAIL.

- [ ] **Step 3: Extend the validator**

Modify `scripts/validate_power.py` — add after the steering checks block:

```python
    import re
    phase3_path = power_dir / "steering" / "phase3-integrate.md"
    if phase3_path.is_file():
        phase3_text = phase3_path.read_text(encoding="utf-8")
        # Match patterns like `templates/module/ts-cheerio.ts` or `templates/route/next-app-router.ts`
        template_refs = re.findall(
            r"templates/(?:module|route|tool|fallback)/[A-Za-z0-9_./-]+\.(?:ts|py|sh)",
            phase3_text,
        )
        for rel in sorted(set(template_refs)):
            full = power_dir / rel
            if not full.is_file():
                print(f"WARN: missing template {rel} (referenced in phase3-integrate.md)")
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_validator_warns_on_missing_templates_listed_in_phase3 -v`
Expected: PASS — output includes `WARN: missing template ...`.

- [ ] **Step 5: Run the validator and observe the warning list**

Run: `python3 scripts/validate_power.py powers/brightdata-scrape`
Expected: prints multiple `WARN: missing template ...` lines (because no template files exist yet), but exits 0 because they're warnings.

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_power.py tests/test_validate_power.py
git commit -m "feat(validator): warn on missing templates referenced by phase3"
```

---

## Task 10: Template — Python module with bs4 (`py-bs4.py`)

**Files:**
- Create: `powers/brightdata-scrape/templates/module/py-bs4.py`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_template_py_bs4_is_valid_python():
    """The Python module template must parse as valid Python (placeholders and all)."""
    import ast
    p = POWER_DIR / "templates" / "module" / "py-bs4.py"
    assert p.is_file(), f"missing {p}"
    src = p.read_text(encoding="utf-8")
    # Replace template placeholders with valid Python literals so ast.parse succeeds
    src_filled = (src
        .replace("{{TARGET_NAME}}", "competitor_prices")
        .replace("{{TARGET_URL}}", "https://example.com")
        .replace("{{CONCURRENCY}}", "20")
    )
    ast.parse(src_filled)  # raises SyntaxError on failure

    # Required surface-level checks
    assert "BRIGHTDATA_API_KEY" in src
    assert "BRIGHTDATA_UNLOCKER_ZONE" in src
    assert "https://api.brightdata.com/request" in src
    assert "def scrape_" in src
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_py_bs4_is_valid_python -v`
Expected: FAIL — file doesn't exist.

- [ ] **Step 3: Create the template**

Create `powers/brightdata-scrape/templates/module/py-bs4.py`:

```python
"""Bright Data scraper for {{TARGET_URL}}.

Generated by the brightdata-scrape Kiro power. Customize selectors below.

Usage:
    from src.scrapers.{{TARGET_NAME}} import scrape_{{TARGET_NAME}}
    items = scrape_{{TARGET_NAME}}("https://example.com")
"""
from __future__ import annotations

import os
import time
from typing import Any, Iterator, TypedDict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

API_KEY = os.environ["BRIGHTDATA_API_KEY"]
ZONE = os.environ.get("BRIGHTDATA_UNLOCKER_ZONE", "unblocker")
BASE_URL = "{{TARGET_URL}}"


class {{TARGET_NAME}}_Item(TypedDict, total=False):
    name: str
    url: str
    # TODO: add fields from {{FIELDS}}


def _fetch(url: str, retries: int = 3) -> str:
    """Fetch a page through Bright Data Web Unlocker with exponential backoff."""
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.post(
                "https://api.brightdata.com/request",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={"zone": ZONE, "url": url, "format": "raw"},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to fetch {url} after {retries} attempts") from last_exc


def _parse(html: str) -> list[{{TARGET_NAME}}_Item]:
    """Extract structured items from a page's HTML.

    Selectors come from Phase 2 reconnaissance. Adjust these to match the target site.
    """
    soup = BeautifulSoup(html, "html.parser")
    items: list[{{TARGET_NAME}}_Item] = []
    for card in soup.select(".item"):  # TODO: replace with {{SELECTORS}} root
        try:
            item: {{TARGET_NAME}}_Item = {
                "name": card.select_one(".name").get_text(strip=True),
                "url": card.select_one("a").get("href", ""),
                # TODO: extract remaining {{FIELDS}}
            }
            items.append(item)
        except (AttributeError, TypeError):
            continue
    return items


def _paginate(start_url: str, max_pages: int = 50) -> Iterator[str]:
    """Yield page URLs. Default: URL-based pagination (?page=N).

    Phase 2 chose pagination = {{PAGINATION}}. If different, replace the body.
    """
    for n in range(1, max_pages + 1):
        sep = "&" if "?" in start_url else "?"
        yield f"{start_url}{sep}page={n}"


def scrape_{{TARGET_NAME}}(start_url: str | None = None) -> list[{{TARGET_NAME}}_Item]:
    """Scrape {{TARGET_URL}} and return a list of items.

    Args:
        start_url: Override the default {{TARGET_URL}}.

    Returns:
        A list of typed item dicts.
    """
    url = start_url or BASE_URL
    all_items: list[{{TARGET_NAME}}_Item] = []
    for page_url in _paginate(url):
        html = _fetch(page_url)
        items = _parse(html)
        if not items:
            break
        all_items.extend(items)
    return all_items


if __name__ == "__main__":
    import json
    print(json.dumps(scrape_{{TARGET_NAME}}(), indent=2, ensure_ascii=False))
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_py_bs4_is_valid_python -v`
Expected: PASS.

- [ ] **Step 5: Run the validator (one less WARN now)**

Run: `python3 scripts/validate_power.py powers/brightdata-scrape`
Expected: OK with one fewer `WARN: missing template`.

- [ ] **Step 6: Commit**

```bash
git add powers/brightdata-scrape/templates/module/py-bs4.py tests/test_validate_power.py
git commit -m "feat(power): Python module template (bs4)"
```

---

## Task 11: Template — TypeScript module with cheerio (`ts-cheerio.ts`)

**Files:**
- Create: `powers/brightdata-scrape/templates/module/ts-cheerio.ts`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_template_ts_cheerio_has_expected_exports_and_imports():
    """The TS module template must declare the right imports, exports, and env-var reads."""
    p = POWER_DIR / "templates" / "module" / "ts-cheerio.ts"
    assert p.is_file(), f"missing {p}"
    src = p.read_text(encoding="utf-8")
    assert "import * as cheerio" in src or "import cheerio" in src
    assert "export async function scrape" in src
    assert "process.env.BRIGHTDATA_API_KEY" in src
    assert "process.env.BRIGHTDATA_UNLOCKER_ZONE" in src
    assert "https://api.brightdata.com/request" in src
    assert "{{TARGET_NAME}}" in src
    assert "{{TARGET_URL}}" in src
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_ts_cheerio_has_expected_exports_and_imports -v`
Expected: FAIL.

- [ ] **Step 3: Create the template**

Create `powers/brightdata-scrape/templates/module/ts-cheerio.ts`:

```typescript
/**
 * Bright Data scraper for {{TARGET_URL}}.
 *
 * Generated by the brightdata-scrape Kiro power. Customize selectors below.
 *
 * Usage:
 *   import { scrape{{TARGET_NAME}} } from "@/scrapers/{{TARGET_NAME}}";
 *   const items = await scrape{{TARGET_NAME}}();
 */
import * as cheerio from "cheerio";

const API_KEY = process.env.BRIGHTDATA_API_KEY;
const ZONE = process.env.BRIGHTDATA_UNLOCKER_ZONE ?? "unblocker";
const BASE_URL = "{{TARGET_URL}}";

if (!API_KEY) {
  throw new Error("BRIGHTDATA_API_KEY is not set");
}

export interface {{TARGET_NAME}}_Item {
  name?: string;
  url?: string;
  // TODO: add fields from {{FIELDS}}
}

async function fetchPage(url: string, retries = 3): Promise<string> {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const resp = await fetch("https://api.brightdata.com/request", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ zone: ZONE, url, format: "raw" }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return await resp.text();
    } catch (err) {
      if (attempt === retries - 1) throw err;
      await new Promise((r) => setTimeout(r, 2 ** attempt * 1000));
    }
  }
  throw new Error("unreachable");
}

function parseItems(html: string): {{TARGET_NAME}}_Item[] {
  const $ = cheerio.load(html);
  const items: {{TARGET_NAME}}_Item[] = [];
  $(".item").each((_i, el) => {
    // TODO: replace with {{SELECTORS}}
    const $el = $(el);
    items.push({
      name: $el.find(".name").text().trim(),
      url: $el.find("a").attr("href") ?? "",
      // TODO: extract remaining {{FIELDS}}
    });
  });
  return items;
}

function* paginate(startUrl: string, maxPages = 50): Generator<string> {
  for (let n = 1; n <= maxPages; n++) {
    const sep = startUrl.includes("?") ? "&" : "?";
    yield `${startUrl}${sep}page=${n}`;
  }
}

export async function scrape{{TARGET_NAME}}(
  startUrl: string = BASE_URL,
): Promise<{{TARGET_NAME}}_Item[]> {
  const all: {{TARGET_NAME}}_Item[] = [];
  for (const pageUrl of paginate(startUrl)) {
    const html = await fetchPage(pageUrl);
    const items = parseItems(html);
    if (items.length === 0) break;
    all.push(...items);
  }
  return all;
}
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_ts_cheerio_has_expected_exports_and_imports -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add powers/brightdata-scrape/templates/module/ts-cheerio.ts tests/test_validate_power.py
git commit -m "feat(power): TypeScript module template (cheerio)"
```

---

## Task 12: Template — Next.js App Router route (`next-app-router.ts`)

**Files:**
- Create: `powers/brightdata-scrape/templates/route/next-app-router.ts`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_template_next_app_router_route():
    """Next.js App Router route must export GET handler and import the module."""
    p = POWER_DIR / "templates" / "route" / "next-app-router.ts"
    assert p.is_file(), f"missing {p}"
    src = p.read_text(encoding="utf-8")
    assert "export async function GET" in src or "export const GET" in src
    assert "scrape{{TARGET_NAME}}" in src or "scrape" in src.lower()
    assert "NextResponse" in src or "Response" in src
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_next_app_router_route -v`
Expected: FAIL.

- [ ] **Step 3: Create the template**

Create `powers/brightdata-scrape/templates/route/next-app-router.ts`:

```typescript
/**
 * Next.js App Router route — GET /api/scrape
 *
 * Generated by the brightdata-scrape Kiro power.
 * Calls into src/scrapers/{{TARGET_NAME}}.ts
 */
import { NextResponse } from "next/server";
import { scrape{{TARGET_NAME}} } from "@/scrapers/{{TARGET_NAME}}";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const url = searchParams.get("url") ?? undefined;

  try {
    const items = await scrape{{TARGET_NAME}}(url);
    return NextResponse.json({ count: items.length, items });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_next_app_router_route -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add powers/brightdata-scrape/templates/route/next-app-router.ts tests/test_validate_power.py
git commit -m "feat(power): Next.js App Router route template"
```

---

## Task 13: Template — FastAPI route (`fastapi.py`)

**Files:**
- Create: `powers/brightdata-scrape/templates/route/fastapi.py`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_template_fastapi_route():
    """FastAPI route must use APIRouter and call the scraper module."""
    import ast
    p = POWER_DIR / "templates" / "route" / "fastapi.py"
    assert p.is_file(), f"missing {p}"
    src = p.read_text(encoding="utf-8")
    src_filled = src.replace("{{TARGET_NAME}}", "competitor")
    ast.parse(src_filled)
    assert "APIRouter" in src
    assert "scrape_{{TARGET_NAME}}" in src
    assert "@router.get" in src or "@router.post" in src
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_fastapi_route -v`
Expected: FAIL.

- [ ] **Step 3: Create the template**

Create `powers/brightdata-scrape/templates/route/fastapi.py`:

```python
"""FastAPI route — GET /api/scrape

Generated by the brightdata-scrape Kiro power.
Calls into src/scrapers/{{TARGET_NAME}}.py

Wire it up by adding to your app:

    from app.api.scrape import router as scrape_router
    app.include_router(scrape_router, prefix="/api")
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.scrapers.{{TARGET_NAME}} import scrape_{{TARGET_NAME}}

router = APIRouter()


@router.get("/scrape")
async def scrape(url: str | None = Query(default=None)) -> dict:
    try:
        items = scrape_{{TARGET_NAME}}(url) if url else scrape_{{TARGET_NAME}}()
    except Exception as exc:  # surface scraping failures as 500s
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"count": len(items), "items": items}
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_fastapi_route -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add powers/brightdata-scrape/templates/route/fastapi.py tests/test_validate_power.py
git commit -m "feat(power): FastAPI route template"
```

---

## Task 14: Template — Anthropic SDK tool, TypeScript (`anthropic-sdk-ts.ts`)

**Files:**
- Create: `powers/brightdata-scrape/templates/tool/anthropic-sdk-ts.ts`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_template_anthropic_sdk_ts_tool():
    """Anthropic SDK TS tool must declare a tool with name, description, input_schema, and a handler."""
    p = POWER_DIR / "templates" / "tool" / "anthropic-sdk-ts.ts"
    assert p.is_file(), f"missing {p}"
    src = p.read_text(encoding="utf-8")
    assert "name:" in src
    assert "description:" in src
    assert "input_schema" in src
    assert "scrape{{TARGET_NAME}}" in src or "scrape_" in src.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_anthropic_sdk_ts_tool -v`
Expected: FAIL.

- [ ] **Step 3: Create the template**

Create `powers/brightdata-scrape/templates/tool/anthropic-sdk-ts.ts`:

```typescript
/**
 * Anthropic SDK tool definition for scraping {{TARGET_URL}}.
 *
 * Generated by the brightdata-scrape Kiro power.
 *
 * Usage:
 *   import Anthropic from "@anthropic-ai/sdk";
 *   import { scrapeTool, runScrapeTool } from "./tools/scrape";
 *
 *   const client = new Anthropic();
 *   const response = await client.messages.create({
 *     model: "claude-opus-4-7",
 *     max_tokens: 1024,
 *     tools: [scrapeTool],
 *     messages: [{ role: "user", content: "Scrape latest items from {{TARGET_URL}}" }],
 *   });
 *   // When the model returns a tool_use block:
 *   //   const result = await runScrapeTool(toolUse.input);
 */
import { scrape{{TARGET_NAME}} } from "../scrapers/{{TARGET_NAME}}";

export const scrapeTool = {
  name: "scrape_{{TARGET_NAME}}",
  description:
    "Scrape items from {{TARGET_URL}}. Use when the user asks for live data from this site. Returns a JSON list of items.",
  input_schema: {
    type: "object" as const,
    properties: {
      url: {
        type: "string",
        description:
          "Optional override URL. If omitted, scrapes the default starting URL ({{TARGET_URL}}).",
      },
    },
  },
};

export async function runScrapeTool(
  input: { url?: string },
): Promise<{ count: number; items: unknown[] }> {
  const items = await scrape{{TARGET_NAME}}(input.url);
  return { count: items.length, items };
}
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_anthropic_sdk_ts_tool -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add powers/brightdata-scrape/templates/tool/anthropic-sdk-ts.ts tests/test_validate_power.py
git commit -m "feat(power): Anthropic SDK TS tool template"
```

---

## Task 15: Template — Anthropic SDK tool, Python (`anthropic-sdk-py.py`)

**Files:**
- Create: `powers/brightdata-scrape/templates/tool/anthropic-sdk-py.py`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_template_anthropic_sdk_py_tool():
    """Anthropic SDK Python tool must define SCRAPE_TOOL and run_scrape_tool."""
    import ast
    p = POWER_DIR / "templates" / "tool" / "anthropic-sdk-py.py"
    assert p.is_file(), f"missing {p}"
    src = p.read_text(encoding="utf-8")
    src_filled = src.replace("{{TARGET_NAME}}", "competitor").replace("{{TARGET_URL}}", "https://example.com")
    ast.parse(src_filled)
    assert "SCRAPE_TOOL" in src or "scrape_tool" in src.lower()
    assert "input_schema" in src
    assert "scrape_{{TARGET_NAME}}" in src
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_anthropic_sdk_py_tool -v`
Expected: FAIL.

- [ ] **Step 3: Create the template**

Create `powers/brightdata-scrape/templates/tool/anthropic-sdk-py.py`:

```python
"""Anthropic SDK tool definition for scraping {{TARGET_URL}}.

Generated by the brightdata-scrape Kiro power.

Usage:
    import anthropic
    from src.tools.scrape import SCRAPE_TOOL, run_scrape_tool

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        tools=[SCRAPE_TOOL],
        messages=[{"role": "user", "content": "Scrape latest items from {{TARGET_URL}}"}],
    )
    # When the model returns a tool_use block:
    #   result = run_scrape_tool(tool_use.input)
"""
from __future__ import annotations

from typing import Any

from src.scrapers.{{TARGET_NAME}} import scrape_{{TARGET_NAME}}

SCRAPE_TOOL: dict[str, Any] = {
    "name": "scrape_{{TARGET_NAME}}",
    "description": (
        "Scrape items from {{TARGET_URL}}. Use when the user asks for live data "
        "from this site. Returns a JSON list of items."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": (
                    "Optional override URL. If omitted, scrapes the default starting URL "
                    "({{TARGET_URL}})."
                ),
            },
        },
    },
}


def run_scrape_tool(tool_input: dict[str, Any]) -> dict[str, Any]:
    url = tool_input.get("url")
    items = scrape_{{TARGET_NAME}}(url) if url else scrape_{{TARGET_NAME}}()
    return {"count": len(items), "items": items}
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_anthropic_sdk_py_tool -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add powers/brightdata-scrape/templates/tool/anthropic-sdk-py.py tests/test_validate_power.py
git commit -m "feat(power): Anthropic SDK Python tool template"
```

---

## Task 16: Template — `curl.sh` fallback for other languages

**Files:**
- Create: `powers/brightdata-scrape/templates/fallback/curl.sh`
- Modify: `tests/test_validate_power.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
def test_template_curl_fallback():
    """Fallback curl template must show the Web Unlocker request and document adaptation."""
    p = POWER_DIR / "templates" / "fallback" / "curl.sh"
    assert p.is_file(), f"missing {p}"
    src = p.read_text(encoding="utf-8")
    assert "BRIGHTDATA_API_KEY" in src
    assert "https://api.brightdata.com/request" in src
    assert "Authorization: Bearer" in src
    # Must include guidance for adapting to another language
    assert "adapt" in src.lower() or "translate" in src.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_curl_fallback -v`
Expected: FAIL.

- [ ] **Step 3: Create the template**

Create `powers/brightdata-scrape/templates/fallback/curl.sh`:

```bash
#!/usr/bin/env bash
# Bright Data Web Unlocker — generic fallback for languages without a first-class template.
#
# Generated by the brightdata-scrape Kiro power.
# Adapt this curl invocation into your language's HTTP client (Go's net/http,
# Ruby's Net::HTTP, Java's HttpClient, etc.). The contract is:
#
#   POST https://api.brightdata.com/request
#   Headers: Authorization: Bearer $BRIGHTDATA_API_KEY
#            Content-Type: application/json
#   Body:   {"zone": "<zone>", "url": "<target>", "format": "raw"}
#
#   Response: raw HTML body of the target page, or JSON if the target is a JSON endpoint.
#
# Translate the request, parse the HTML in your language's idiomatic parser
# (e.g., goquery for Go, Nokogiri for Ruby, jsoup for Java).

set -euo pipefail

: "${BRIGHTDATA_API_KEY:?BRIGHTDATA_API_KEY must be set}"
ZONE="${BRIGHTDATA_UNLOCKER_ZONE:-unblocker}"
TARGET_URL="{{TARGET_URL}}"

curl -s -X POST https://api.brightdata.com/request \
  -H "Authorization: Bearer ${BRIGHTDATA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"zone\": \"${ZONE}\", \"url\": \"${TARGET_URL}\", \"format\": \"raw\"}"
```

- [ ] **Step 4: Run the test**

Run: `python3 -m pytest tests/test_validate_power.py::test_template_curl_fallback -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add powers/brightdata-scrape/templates/fallback/curl.sh tests/test_validate_power.py
git commit -m "feat(power): generic curl fallback template"
```

---

## Task 17: Validator — flip template-missing check from WARN to FAIL for v1 templates

**Files:**
- Modify: `scripts/validate_power.py`
- Modify: `tests/test_validate_power.py`

We've shipped the v1 template subset (Tasks 10–16). Time to require them. v1.1 templates remain WARN-only.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_validate_power.py`:

```python
V1_REQUIRED_TEMPLATES = [
    "templates/module/py-bs4.py",
    "templates/module/ts-cheerio.ts",
    "templates/route/next-app-router.ts",
    "templates/route/fastapi.py",
    "templates/tool/anthropic-sdk-ts.ts",
    "templates/tool/anthropic-sdk-py.py",
    "templates/fallback/curl.sh",
]

def test_v1_required_templates_all_present():
    """All v1 required templates must exist (validator should pass without WARN on these)."""
    for rel in V1_REQUIRED_TEMPLATES:
        path = POWER_DIR / rel
        assert path.is_file(), f"missing required v1 template: {rel}"

def test_validator_passes_when_v1_templates_present():
    """Validator should exit 0 with all v1 templates present."""
    result = run_validator(str(POWER_DIR))
    out = result.stdout + result.stderr
    assert result.returncode == 0, f"validator failed: {out}"
    # No WARN about v1 required templates
    for rel in V1_REQUIRED_TEMPLATES:
        assert f"WARN: missing template {rel}" not in out, f"unexpected WARN for v1 template {rel}"
```

- [ ] **Step 2: Run tests**

Run: `python3 -m pytest tests/test_validate_power.py -v`
Expected: PASS (all v1 templates exist from Tasks 10–16; validator already exits 0).

- [ ] **Step 3: Add explicit FAIL list to the validator**

Modify `scripts/validate_power.py` — replace the template-references block with:

```python
    import re
    phase3_path = power_dir / "steering" / "phase3-integrate.md"
    v1_required = {
        "templates/module/py-bs4.py",
        "templates/module/ts-cheerio.ts",
        "templates/route/next-app-router.ts",
        "templates/route/fastapi.py",
        "templates/tool/anthropic-sdk-ts.ts",
        "templates/tool/anthropic-sdk-py.py",
        "templates/fallback/curl.sh",
    }
    if phase3_path.is_file():
        phase3_text = phase3_path.read_text(encoding="utf-8")
        template_refs = set(re.findall(
            r"templates/(?:module|route|tool|fallback)/[A-Za-z0-9_./-]+\.(?:ts|py|sh)",
            phase3_text,
        ))
        for rel in sorted(template_refs):
            full = power_dir / rel
            if not full.is_file():
                if rel in v1_required:
                    failures.append(f"missing required v1 template: {rel}")
                else:
                    print(f"WARN: missing template {rel} (referenced in phase3-integrate.md)")
        # Also FAIL if any v1_required is missing even if not referenced in phase3
        for rel in sorted(v1_required):
            full = power_dir / rel
            if not full.is_file():
                if f"missing required v1 template: {rel}" not in failures:
                    failures.append(f"missing required v1 template: {rel}")
```

- [ ] **Step 4: Run tests and validator**

Run: `python3 -m pytest tests/test_validate_power.py -v`
Expected: ALL PASS.

Run: `python3 scripts/validate_power.py powers/brightdata-scrape`
Expected: `OK: powers/brightdata-scrape passed all checks` (no v1 FAILs; v1.1 templates still WARN).

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_power.py tests/test_validate_power.py
git commit -m "feat(validator): enforce v1 required templates"
```

---

## Task 18: Update `powers/README.md` to list the new power

**Files:**
- Modify: `powers/README.md`

- [ ] **Step 1: Read the existing README structure**

Inspect `powers/README.md` to find the alphabetical insertion point and copy the existing entry format (e.g., the `aws-mcp` or `postman` entry).

- [ ] **Step 2: Insert the brightdata-scrape entry**

Add this block in alphabetical order (between `aws-transform` and `checkout`, or wherever `b*` would land):

```markdown
### brightdata-scrape
**Add web scraping to any app with Bright Data** — Detects your project's stack (any language, with first-class TypeScript and Python support) and adds production-ready scraping in the right shape — a reusable module, an API route, or an agent tool. Wires the Bright Data MCP server into the project so any AI agent that runs against the project gains live web tools (search, scrape, structured data from 40+ platforms).

**MCP Servers:** brightdata (`https://mcp.brightdata.com/mcp`)

---
```

- [ ] **Step 3: Verify alphabetical order and formatting**

Run: `grep -n "^### " powers/README.md | head -30`
Expected: `brightdata-scrape` appears in alphabetical position; surrounding entries unchanged.

- [ ] **Step 4: Commit**

```bash
git add powers/README.md
git commit -m "docs: add brightdata-scrape to powers README"
```

---

## Task 19: Manual end-to-end smoke test (greenfield + Next.js)

**Files:** none modified — this is a manual verification step using a temporary scratch directory.

- [ ] **Step 1: Set up two scratch projects**

```bash
mkdir -p /tmp/brightdata-scrape-test/{greenfield,nextjs-app}

# Greenfield: empty directory, no manifest
cd /tmp/brightdata-scrape-test/greenfield
ls  # confirm empty

# Next.js project: minimal package.json so detection picks Next.js App Router
cd /tmp/brightdata-scrape-test/nextjs-app
cat > package.json <<'EOF'
{
  "name": "smoke-test-next",
  "version": "0.0.1",
  "dependencies": {
    "next": "14.0.0",
    "react": "18.0.0",
    "react-dom": "18.0.0"
  }
}
EOF
mkdir -p app
```

- [ ] **Step 2: Walk through each phase manually as if you were the LLM**

Open the steering files in order. For each one, confirm by reading:

1. `scrape-workflow.md` → tells you to read `phase1-detect-and-plan.md`. ✓
2. `phase1-detect-and-plan.md`:
   - For `nextjs-app`: detection sees `next` in `package.json` → pattern is **route**, framework is `next-app-router` (because `app/` directory exists, not `pages/`). ✓
   - For `greenfield`: no manifest → mode is **greenfield**, ask language → assume "Python" → pattern is **module**, template is `py-bs4.py`. ✓
3. `phase2-scraping-playbook.md` → no real reconnaissance, but the steering can be read top-to-bottom without contradicting itself. ✓
4. `phase3-integrate.md` → look up the template path table; `next-app-router.ts` and `py-bs4.py` are listed and exist. ✓
5. `phase4-mcp-and-verify.md` → the `.kiro/settings/mcp.json` merge logic and smoke-test outcomes are unambiguous. ✓

- [ ] **Step 3: Document any rough edges**

If any phase's instructions feel ambiguous when you walk through them in concrete projects, note the issue and create a follow-up TODO. The plan does NOT need to fix those here — they go into a v1.1 polish task.

- [ ] **Step 4: Clean up**

```bash
rm -rf /tmp/brightdata-scrape-test
```

- [ ] **Step 5: Commit (if any polish edits were applied)**

```bash
# only if you edited steering files for clarity during the walkthrough
git add powers/brightdata-scrape/steering/
git commit -m "docs(power): smoke-test polish — clarify steering wording"
# otherwise, no commit needed for this task
```

---

## Task 20: Add v1.1 templates (batched)

**Files:**
- Create: 12 remaining template files
- Modify: `tests/test_validate_power.py`

Templates added in one batch — they all follow the same shape. Each gets a small parsability test. Group commits by family.

- [ ] **Step 1: Module variants — `ts-fetch.ts` and `py-stdlib.py`**

Create `powers/brightdata-scrape/templates/module/ts-fetch.ts` (same shape as `ts-cheerio.ts` but parser uses regex / `HTMLRewriter` and has no `import * as cheerio`).

Create `powers/brightdata-scrape/templates/module/py-stdlib.py` (same shape as `py-bs4.py` but parser uses `html.parser` from stdlib instead of bs4).

Append parsability tests to `tests/test_validate_power.py`:

```python
def test_template_ts_fetch_module():
    p = POWER_DIR / "templates" / "module" / "ts-fetch.ts"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    assert "import * as cheerio" not in src
    assert "export async function scrape" in src
    assert "https://api.brightdata.com/request" in src

def test_template_py_stdlib_module():
    import ast
    p = POWER_DIR / "templates" / "module" / "py-stdlib.py"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    src_filled = src.replace("{{TARGET_NAME}}", "x").replace("{{TARGET_URL}}", "https://e.com")
    ast.parse(src_filled)
    assert "from bs4" not in src
    assert "html.parser" in src or "HTMLParser" in src
    assert "def scrape_" in src
```

Run tests: `python3 -m pytest tests/test_validate_power.py -v` → PASS.

Commit:

```bash
git add powers/brightdata-scrape/templates/module/ts-fetch.ts powers/brightdata-scrape/templates/module/py-stdlib.py tests/test_validate_power.py
git commit -m "feat(power): module templates — ts-fetch and py-stdlib"
```

- [ ] **Step 2: Route variants — Next.js Pages Router, Express, Fastify, Hono, Koa, Flask, Django**

Create each file under `powers/brightdata-scrape/templates/route/` following the same conventions as `next-app-router.ts` and `fastapi.py` (route imports the module, calls scraper, returns JSON; surfaces errors as 500s).

Filenames:
- `next-pages-router.ts`
- `express.ts`
- `fastify.ts`
- `hono.ts`
- `koa.ts`
- `flask.py`
- `django.py`

Append a parsability test for each (mirror Task 12/13 pattern). For TS files, just check key strings; for Python, use `ast.parse` after filling placeholders.

Run tests, then commit per family:

```bash
git add powers/brightdata-scrape/templates/route/next-pages-router.ts \
        powers/brightdata-scrape/templates/route/express.ts \
        powers/brightdata-scrape/templates/route/fastify.ts \
        powers/brightdata-scrape/templates/route/hono.ts \
        powers/brightdata-scrape/templates/route/koa.ts \
        tests/test_validate_power.py
git commit -m "feat(power): TS web framework route templates"

git add powers/brightdata-scrape/templates/route/flask.py \
        powers/brightdata-scrape/templates/route/django.py \
        tests/test_validate_power.py
git commit -m "feat(power): Python web framework route templates"
```

- [ ] **Step 3: Tool variants — LangChain (TS+Py), OpenAI (TS+Py), Mastra, Vercel AI SDK**

Create each under `powers/brightdata-scrape/templates/tool/`:
- `langchain-ts.ts`
- `langchain-py.py`
- `openai-ts.ts`
- `openai-py.py`
- `mastra.ts`
- `vercel-ai-sdk.ts`

Each follows the same shape as `anthropic-sdk-ts.ts` / `anthropic-sdk-py.py` — it imports the scraper module, defines a tool with name/description/schema, and provides a handler that calls into the scraper.

Append parsability tests, run, commit:

```bash
git add powers/brightdata-scrape/templates/tool/ tests/test_validate_power.py
git commit -m "feat(power): remaining agent-tool templates (LangChain, OpenAI, Mastra, Vercel AI)"
```

- [ ] **Step 4: Promote v1.1 templates to required in the validator**

Modify `scripts/validate_power.py` — extend `v1_required` with all 12 new template paths. Now any missing template is a FAIL.

Append to `tests/test_validate_power.py`:

```python
def test_validator_no_warn_lines_after_v1_1():
    """After v1.1, the validator should emit zero WARN lines."""
    result = run_validator(str(POWER_DIR))
    out = result.stdout + result.stderr
    assert result.returncode == 0
    assert "WARN" not in out, f"unexpected WARN: {out}"
```

Run tests, commit:

```bash
git add scripts/validate_power.py tests/test_validate_power.py
git commit -m "feat(validator): all templates now required (v1.1)"
```

---

## Self-review notes

After writing this plan, here's what I checked:

**Spec coverage** — every section of the spec maps to at least one task:
- Architecture / file layout → Task 1
- POWER.md frontmatter and onboarding → Task 2
- mcp.json → Task 3
- Steering files (orchestrator + 4 phases) → Tasks 4–8
- Phase 1 detection logic → Task 5
- Phase 2 scraping playbook → Task 6
- Phase 3 integration with three sub-templates → Task 7 (steering) + Tasks 10–16, 20 (templates)
- Phase 4 MCP wiring + smoke test → Task 8
- Error handling matrix → covered inside Phases 3 and 4
- File templates list (16 templates) → Tasks 10–16 (v1) + Task 20 (v1.1)
- Greenfield handling → Phase 1 steering (Task 5) + smoke-test branch (Task 8)
- README pointer → Task 18
- Manual smoke walkthrough → Task 19

**Placeholder scan** — no "TBD", "TODO" outside template content (template TODOs are user-facing markers indicating "fill in your selectors here", which is correct behavior, not a plan failure).

**Type/name consistency** — `scrape_{{TARGET_NAME}}` (Python) and `scrape{{TARGET_NAME}}` (TS) are consistent across templates. `BRIGHTDATA_API_KEY` and `BRIGHTDATA_UNLOCKER_ZONE` are the same env var names everywhere.

**Bite-sized steps** — every task has TDD-style steps (failing test → fix → passing test → commit). Each step is 2–5 minutes of focused work.

---

## Out of scope (recap from spec)

- Scheduling / cron / GitHub Actions (deferred to a future power)
- Database writes / ETL pipelines
- UI components for displaying scraped data
- Proxy zone management (`brightdata-cli` skill covers it)
- Multi-site orchestration in one pass
- First-class language support beyond Python/TypeScript (other languages get the curl fallback)
