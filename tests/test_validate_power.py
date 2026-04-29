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


def run_validator(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(REPO_ROOT / "scripts" / "validate_power.py"), *args],
        capture_output=True,
        text=True,
    )


def test_validator_runs_and_reports_missing_power_md(tmp_path):
    """With a directory that has mcp.json but no POWER.md, only the missing-file rule for POWER.md should fire."""
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    assert "missing required file" in output, f"validator output was: {output!r}"
    assert "POWER.md" in output, f"validator output was: {output!r}"


def test_validator_fails_when_powermd_missing_frontmatter(tmp_path):
    """POWER.md exists but has no '---' fence — validator should fail with a frontmatter message."""
    power_md = tmp_path / "POWER.md"
    power_md.write_text("# My Power\n\nSome content without any frontmatter.\n", encoding="utf-8")
    (tmp_path / "mcp.json").write_text(VALID_MCP_JSON, encoding="utf-8")
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    assert "POWER.md frontmatter" in output, f"validator output was: {output!r}"


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
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    assert "missing field 'keywords'" in output, f"validator output was: {output!r}"


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
    result = run_validator(str(tmp_path))
    assert result.returncode == 0, f"unexpected failure: {result.stdout + result.stderr!r}"


def test_validator_fails_when_mcp_json_missing(tmp_path):
    """Directory has a valid POWER.md but no mcp.json — validator should fail mentioning mcp.json."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    assert "mcp.json" in output, f"validator output was: {output!r}"


def test_validator_fails_when_mcp_json_invalid_json(tmp_path):
    """mcp.json contains malformed JSON — validator should fail with an invalid JSON message."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text('{"mcpServers":', encoding="utf-8")
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    assert "invalid" in output.lower() or "json" in output.lower(), f"validator output was: {output!r}"


def test_validator_fails_when_brightdata_server_missing(tmp_path):
    """mcp.json is valid JSON but has no mcpServers.brightdata key — validator should fail naming brightdata."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(
        '{"mcpServers": {"other": {"url": "https://example.com"}}}\n',
        encoding="utf-8",
    )
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    assert "brightdata" in output, f"validator output was: {output!r}"


def test_validator_fails_when_url_missing_token_placeholder(tmp_path):
    """mcp.json has a brightdata server but its URL lacks ${BRIGHTDATA_API_KEY} — validator should fail."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(
        '{"mcpServers": {"brightdata": {"url": "https://mcp.brightdata.com/mcp"}}}\n',
        encoding="utf-8",
    )
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    assert "BRIGHTDATA_API_KEY" in output, f"validator output was: {output!r}"


def test_validator_fails_when_mcp_servers_is_not_an_object(tmp_path):
    """mcp.json's mcpServers field is a JSON array, not an object — validator should fail cleanly."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(
        '{"mcpServers": [{"url": "https://example.com"}]}',
        encoding="utf-8",
    )
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    assert "mcpServers must be an object" in output, f"validator output was: {output!r}"


def test_validator_fails_when_brightdata_entry_is_not_an_object(tmp_path):
    """mcp.json's brightdata value is a string instead of an object — validator should fail cleanly."""
    (tmp_path / "POWER.md").write_text(VALID_POWER_MD, encoding="utf-8")
    (tmp_path / "mcp.json").write_text(
        '{"mcpServers": {"brightdata": "https://mcp.brightdata.com/mcp?token=${BRIGHTDATA_API_KEY}"}}',
        encoding="utf-8",
    )
    result = run_validator(str(tmp_path))
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"validator output was: {output!r}"
    assert "brightdata must be an object" in output, f"validator output was: {output!r}"
