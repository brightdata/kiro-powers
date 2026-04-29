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

    if failures:
        for f in failures:
            fail(f)
        return 1
    print(f"OK: {power_dir} passed all checks")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
