"""Tests for scripts/validate_power.py.

Each test corresponds to one validation rule the script enforces.
Adding a new rule = add a fixture + add a test + extend the script.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
POWER_DIR = REPO_ROOT / "brightdata-scrape"


def run_validator(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(REPO_ROOT / "scripts" / "validate_power.py"), *args],
        capture_output=True,
        text=True,
    )


def test_validator_runs_and_reports_missing_power_md(tmp_path):
    """With a directory that has no POWER.md, validator should fail and mention POWER.md."""
    result = run_validator(str(tmp_path))
    assert result.returncode != 0
    assert "POWER.md" in (result.stdout + result.stderr)


def test_validator_fails_when_powermd_missing_frontmatter(tmp_path):
    """POWER.md exists but has no '---' fence — validator should fail with a frontmatter message."""
    power_md = tmp_path / "POWER.md"
    power_md.write_text("# My Power\n\nSome content without any frontmatter.\n", encoding="utf-8")
    result = run_validator(str(tmp_path))
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "frontmatter" in output.lower()


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
    result = run_validator(str(tmp_path))
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "keywords" in output


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
    result = run_validator(str(tmp_path))
    assert result.returncode == 0
    assert "OK" in result.stdout
