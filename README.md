# brightdata-powers

A Bright Data Kiro power for adding web scraping to any application.

## What's in this repo

- **[`brightdata-scrape/`](brightdata-scrape/)** — the Kiro power itself (`POWER.md`, `mcp.json`, steering files, code templates). Install as a Kiro power from this directory, or copy `brightdata-scrape/` into the upstream `kirodotdev/powers` collection to contribute.
- **`powers/`** — a clone of [`kirodotdev/powers`](https://github.com/kirodotdev/powers) used as inspiration. Not part of this repo's tree (gitignored).
- **[`scripts/validate_power.py`](scripts/validate_power.py)** — CLI to validate the power's structure.
- **[`tests/test_validate_power.py`](tests/test_validate_power.py)** — pytest suite for the validator.

## What `brightdata-scrape` does

It's a Kiro power that detects your project's stack and adds production-ready Bright Data scraping in the right shape — a reusable module, an API route, or an agent tool — backed by Bright Data's [Web Unlocker](https://brightdata.com/products/web-unlocker), [SERP API](https://brightdata.com/products/serp-api), [Web Data APIs](https://brightdata.com/products/web-scraper), and [Browser API](https://brightdata.com/products/scraping-browser). It also wires the [Bright Data MCP server](https://mcp.brightdata.com) into your project so any AI agent that runs against the project (Claude Code, Cursor, Cline, Kiro itself) gains live web tools.

## Quick start

1. Get a [Bright Data API token](https://brightdata.com/cp/setting/users) (free 5,000 requests/month).
2. Set it: `export BRIGHTDATA_API_KEY=<your-token>`.
3. Install the power in Kiro (see [Installing](#installing) below).
4. Tell Kiro: *"add a scraper for X"* / *"give my agent web search"* / *"extract product prices from amazon.com"*.

## Installing

Open the **Powers** panel in Kiro and pick one of:

- **Add power from local path** — point Kiro at the `brightdata-scrape/` directory in your local clone of this repo.
- **Add power from GitHub** — paste the repo URL plus the path to the power directory:
  ```
  https://github.com/brightdata/powers/tree/main/brightdata-scrape
  ```
  (The repo is a multi-power monorepo — `brightdata-scrape/` is the power. Pointing Kiro at the bare repo URL won't work because `POWER.md` lives inside the subdirectory.)

Once installed, Kiro activates the power on keywords like "scrape", "extract data", "competitor prices", "give my agent web search", etc. See [`brightdata-scrape/POWER.md`](brightdata-scrape/POWER.md) for the full keyword list and onboarding steps.

## Validating the power

```bash
python3 scripts/validate_power.py brightdata-scrape
python3 -m pytest tests/test_validate_power.py -v
```

## See also

- Bright Data docs: [docs.brightdata.com](https://docs.brightdata.com)
