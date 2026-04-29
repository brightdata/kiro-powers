"""Tests for scripts/validate_power.py.

Each test corresponds to one validation rule the script enforces.
Adding a new rule = add a fixture + add a test + extend the script.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
POWER_DIR = REPO_ROOT / "brightdata-scrape"

VALID_POWER_MD = (
    "---\n"
    "name: test-power\n"
    "displayName: Test Power\n"
    "description: A test power.\n"
    'keywords: ["test"]\n'
    "author: Test Author\n"
    "---\n"
    "\n"
    "# Test Power\n"
)

VALID_MCP_JSON = (
    '{\n'
    '  "mcpServers": {\n'
    '    "brightdata": {\n'
    '      "url": "https://mcp.brightdata.com/mcp?token=${BRIGHTDATA_API_KEY}",\n'
    '      "disabled": false\n'
    '    }\n'
    '  }\n'
    '}\n'
)

VALID_STEERING_WORKFLOW = (
    "# Workflow\n\nReads phase1-detect-and-plan.md, "
    "phase2-scraping-playbook.md, phase3-integrate.md, "
    "phase4-mcp-and-verify.md.\n"
)


def _add_valid_steering(base: "Path") -> None:
    """Create a minimal valid steering/ directory under *base*."""
    steering = base / "steering"
    steering.mkdir(exist_ok=True)
    (steering / "scrape-workflow.md").write_text(VALID_STEERING_WORKFLOW, encoding="utf-8")
    (steering / "phase1-detect-and-plan.md").write_text("# P1", encoding="utf-8")
    (steering / "phase2-scraping-playbook.md").write_text("# P2", encoding="utf-8")
    (steering / "phase3-integrate.md").write_text("# P3", encoding="utf-8")
    (steering / "phase4-mcp-and-verify.md").write_text("# P4", encoding="utf-8")


def run_validator(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(REPO_ROOT / "scripts" / "validate_power.py"), *args],
        capture_output=True,
        text=True,
    )


def _failure_lines(output: str) -> "list[str]":
    return [line for line in output.splitlines() if line.startswith("FAIL:")]


def test_validator_runs_and_reports_missing_power_md(tmp_path):
    """With a directory that has mcp.json but no POWER.md, the POWER.md-missing and steering-missing rules fire."""
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    fails = _failure_lines(output)
    assert len(fails) == 2, f"expected exactly two FAIL lines, got: {fails}"
    assert any("POWER.md" in f and "missing required file" in f for f in fails), f"validator output was: {output!r}"


def test_validator_fails_when_powermd_missing_frontmatter(tmp_path):
    """POWER.md exists but has no '---' fence — validator should fail with a frontmatter message."""
    power_md = tmp_path / "POWER.md"
    power_md.write_text("# My Power\n\nSome content without any frontmatter.\n", encoding="utf-8")
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    fails = _failure_lines(output)
    assert len(fails) == 1, f"expected exactly one FAIL line, got: {fails}"
    assert "POWER.md frontmatter" in fails[0], f"validator output was: {output!r}"


def test_validator_fails_when_frontmatter_missing_required_field(tmp_path):
    """POWER.md has frontmatter but is missing 'keywords:' — validator should fail naming that field."""
    power_md = tmp_path / "POWER.md"
    power_md.write_text(
        "---\n"
        "name: test-power\n"
        "displayName: Test Power\n"
        "description: A test power.\n"
        "author: Test Author\n"
        "---\n"
        "\n"
        "# Test Power\n",
        encoding="utf-8",
    )
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    fails = _failure_lines(output)
    assert len(fails) == 1, f"expected exactly one FAIL line, got: {fails}"
    assert "missing field 'keywords'" in fails[0], f"validator output was: {output!r}"


def test_validator_passes_with_complete_powermd(tmp_path):
    """POWER.md with all five required frontmatter fields — validator should return 0."""
    power_md = tmp_path / "POWER.md"
    power_md.write_text(
        "---\n"
        "name: test-power\n"
        "displayName: Test Power\n"
        "description: A test power.\n"
        'keywords: ["test", "power"]\n'
        "author: Test Author\n"
        "---\n"
        "\n"
        "# Test Power\n",
        encoding="utf-8",
    )
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"validator output was: {output!r}"
    assert "OK" in result.stdout, f"validator output was: {output!r}"


def test_validator_accepts_crlf_line_endings(tmp_path):
    """A POWER.md saved with CRLF line endings should still parse correctly."""
    power_md = tmp_path / "POWER.md"
    power_md.write_text(
        "---\r\n"
        "name: test-power\r\n"
        "displayName: Test Power\r\n"
        "description: A test power.\r\n"
        'keywords: ["test"]\r\n'
        "author: Test Author\r\n"
        "---\r\n"
        "\r\n"
        "# Test Power\r\n",
        encoding="utf-8",
    )
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    assert result.returncode == 0, f"unexpected failure: {result.stdout + result.stderr!r}"


def test_validator_accepts_utf8_bom(tmp_path):
    """A POWER.md saved with a UTF-8 BOM should still parse correctly."""
    power_md = tmp_path / "POWER.md"
    power_md.write_text(
        "﻿"  # BOM
        "---\n"
        "name: test-power\n"
        "displayName: Test Power\n"
        "description: A test power.\n"
        'keywords: ["test"]\n'
        "author: Test Author\n"
        "---\n"
        "\n"
        "# Test Power\n",
        encoding="utf-8",
    )
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    assert result.returncode == 0, f"unexpected failure: {result.stdout + result.stderr!r}"


def test_validator_accepts_closing_fence_at_eof(tmp_path):
    """A POWER.md whose last bytes are '---' (no trailing newline) should still parse correctly."""
    power_md = tmp_path / "POWER.md"
    power_md.write_text(
        "---\n"
        "name: test-power\n"
        "displayName: Test Power\n"
        "description: A test power.\n"
        'keywords: ["test"]\n'
        "author: Test Author\n"
        "---",  # no trailing newline
        encoding="utf-8",
    )
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    assert result.returncode == 0, f"unexpected failure: {result.stdout + result.stderr!r}"


def test_validator_fails_when_mcp_json_missing(tmp_path):
    """Directory has a valid POWER.md but no mcp.json — validator should fail mentioning mcp.json."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    fails = _failure_lines(output)
    assert len(fails) == 1, f"expected exactly one FAIL line, got: {fails}"
    assert "mcp.json" in fails[0], f"validator output was: {output!r}"


def test_validator_fails_when_mcp_json_invalid_json(tmp_path):
    """mcp.json contains malformed JSON — validator should fail with an invalid JSON message."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text('{"mcpServers":', encoding="utf-8")
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    fails = _failure_lines(output)
    assert len(fails) == 1, f"expected exactly one FAIL line, got: {fails}"
    assert "invalid" in fails[0].lower() or "json" in fails[0].lower(), f"validator output was: {output!r}"


def test_validator_fails_when_brightdata_server_missing(tmp_path):
    """mcp.json is valid JSON but has no mcpServers.brightdata key — validator should fail naming brightdata."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(
        '{"mcpServers": {"other": {"url": "https://example.com"}}}\n',
        encoding="utf-8",
    )
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    fails = _failure_lines(output)
    assert len(fails) == 1, f"expected exactly one FAIL line, got: {fails}"
    assert "brightdata" in fails[0], f"validator output was: {output!r}"


def test_validator_fails_when_url_missing_token_placeholder(tmp_path):
    """mcp.json has a brightdata server but its URL lacks ${BRIGHTDATA_API_KEY} — validator should fail."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(
        '{"mcpServers": {"brightdata": {"url": "https://mcp.brightdata.com/mcp"}}}\n',
        encoding="utf-8",
    )
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    fails = _failure_lines(output)
    assert len(fails) == 1, f"expected exactly one FAIL line, got: {fails}"
    assert "BRIGHTDATA_API_KEY" in fails[0], f"validator output was: {output!r}"


def test_validator_fails_when_mcp_servers_is_not_an_object(tmp_path):
    """mcp.json's mcpServers field is a JSON array, not an object — validator should fail cleanly."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(
        '{"mcpServers": [{"url": "https://example.com"}]}',
        encoding="utf-8",
    )
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    fails = _failure_lines(output)
    assert len(fails) == 1, f"expected exactly one FAIL line, got: {fails}"
    assert "mcpServers must be an object" in fails[0], f"validator output was: {output!r}"


def test_validator_fails_when_brightdata_entry_is_not_an_object(tmp_path):
    """mcp.json's brightdata value is a string instead of an object — validator should fail cleanly."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(
        '{"mcpServers": {"brightdata": "https://mcp.brightdata.com/mcp?token=${BRIGHTDATA_API_KEY}"}}',
        encoding="utf-8",
    )
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    fails = _failure_lines(output)
    assert len(fails) == 1, f"expected exactly one FAIL line, got: {fails}"
    assert "brightdata must be an object" in fails[0], f"validator output was: {output!r}"


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


def test_validator_fails_when_orchestrator_missing_phase_reference(tmp_path):
    """scrape-workflow.md that doesn't mention every phase file should fail validation."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    steering = tmp_path / "steering"
    steering.mkdir()
    # Orchestrator references only 3 of the 4 phases (missing phase4)
    (steering / "scrape-workflow.md").write_text(
        "# Workflow\n\nRead phase1-detect-and-plan.md, then "
        "phase2-scraping-playbook.md, then phase3-integrate.md.\n",
        encoding="utf-8",
    )
    # All four phase files exist (so the missing-file check doesn't fire)
    (steering / "phase1-detect-and-plan.md").write_text("# P1", encoding="utf-8")
    (steering / "phase2-scraping-playbook.md").write_text("# P2", encoding="utf-8")
    (steering / "phase3-integrate.md").write_text("# P3", encoding="utf-8")
    (steering / "phase4-mcp-and-verify.md").write_text("# P4", encoding="utf-8")
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    assert "phase4-mcp-and-verify.md" in output, f"validator output was: {output!r}"
    assert "must reference" in output, f"validator output was: {output!r}"


def test_validator_passes_with_complete_steering(tmp_path):
    """A directory with all five steering files and a properly cross-referencing orchestrator should pass."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    _add_valid_steering(tmp_path)
    result = run_validator(str(tmp_path))
    assert result.returncode == 0, f"unexpected failure: {result.stdout + result.stderr!r}"
    assert "OK" in result.stdout


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
        "never overwrite",  # safety
    ]:
        assert keyword.lower() in text.lower(), f"phase3 missing keyword: {keyword}"


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


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _write_phase3_with_template_refs(tmp_path: "Path", refs: "list[str]") -> None:
    """Overwrite phase3-integrate.md with minimal content that mentions each ref path."""
    body_lines = [
        "# Phase 3: Integrate (test stub)",
        "",
        "References these templates:",
        "",
    ]
    body_lines.extend(f"- `{ref}`" for ref in refs)
    body_lines.append("")
    (tmp_path / "steering" / "phase3-integrate.md").write_text(
        "\n".join(body_lines), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Template path consistency check tests
# ---------------------------------------------------------------------------

def test_validator_warns_when_phase3_references_missing_template(tmp_path):
    """Validator emits WARN for each template path in phase3 that doesn't exist on disk, but still exits 0."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    _add_valid_steering(tmp_path)
    _write_phase3_with_template_refs(
        tmp_path,
        ["templates/module/ts-cheerio.ts", "templates/route/next-app-router.ts"],
    )
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"validator should exit 0 on warnings; output: {output!r}"
    assert "WARN: missing template templates/module/ts-cheerio.ts" in output, (
        f"expected WARN for ts-cheerio.ts; output: {output!r}"
    )
    assert "WARN: missing template templates/route/next-app-router.ts" in output, (
        f"expected WARN for next-app-router.ts; output: {output!r}"
    )


def test_validator_does_not_warn_when_template_exists(tmp_path):
    """Validator does NOT emit a WARN for a template path that actually exists on disk."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    _add_valid_steering(tmp_path)
    _write_phase3_with_template_refs(
        tmp_path,
        ["templates/module/ts-cheerio.ts"],
    )
    # Create the referenced template file
    (tmp_path / "templates" / "module").mkdir(parents=True, exist_ok=True)
    (tmp_path / "templates" / "module" / "ts-cheerio.ts").write_text(
        "// placeholder template\n", encoding="utf-8"
    )
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"validator should exit 0; output: {output!r}"
    assert "WARN: missing template templates/module/ts-cheerio.ts" not in output, (
        f"should not warn for existing template; output: {output!r}"
    )


def test_validator_only_recognizes_known_template_subdirs(tmp_path):
    """Validator does NOT warn for paths under unrecognised template subdirs (not module/route/tool/fallback)."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    _add_valid_steering(tmp_path)
    _write_phase3_with_template_refs(
        tmp_path,
        ["templates/something_else/foo.py"],
    )
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"validator should exit 0; output: {output!r}"
    assert "WARN: missing template templates/something_else/foo.py" not in output, (
        f"should not warn for non-canonical subdir; output: {output!r}"
    )


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


def test_template_next_app_router_route():
    """Next.js App Router route must export GET handler and import the module."""
    p = POWER_DIR / "templates" / "route" / "next-app-router.ts"
    assert p.is_file(), f"missing {p}"
    src = p.read_text(encoding="utf-8")
    assert "export async function GET" in src or "export const GET" in src
    assert "scrape{{TARGET_NAME}}" in src or "scrape" in src.lower()
    assert "NextResponse" in src or "Response" in src


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
