"""Claude traffic must not split across the broad AI policy."""

from __future__ import annotations

from pathlib import Path

import pytest

import build_loon_rules as blr
from rulegrammar import parse_rule


REPO_ROOT = Path(__file__).resolve().parents[1]
DIALECT_DIRS = [
    REPO_ROOT / "rules" / "loon" / "generated",
    REPO_ROOT / "rules" / "shadowrocket" / "generated",
    REPO_ROOT / "rules" / "surge" / "generated",
]


def _values(path: Path) -> set[str]:
    values: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        rule = parse_rule(line)
        if rule is not None:
            values.add(rule.value)
    return values


def test_claude_ruleset_precedes_general_ai():
    tags = [ruleset.tag for ruleset in blr.RULESETS]
    assert tags.index("Claude") < tags.index("AI")


@pytest.mark.parametrize("generated_dir", DIALECT_DIRS, ids=lambda path: path.parent.name)
def test_claude_owned_domains_are_not_split_to_ai(generated_dir: Path):
    claude_values = _values(generated_dir / "08-Claude.list")
    ai_values = _values(generated_dir / "08-AI.list")
    required = set(blr.CLAUDE_FIRST_PARTY_SUFFIXES) | set(blr.CLAUDE_EXACT_HOSTS)

    assert required <= claude_values
    assert not (required & ai_values)
    assert not {value for value in ai_values if "claude" in value or "anthropic" in value}
