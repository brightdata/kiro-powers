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
