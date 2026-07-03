"""Tests for the shared, dialect-neutral generated-tree validator."""

from __future__ import annotations

from pathlib import Path

import validate_generated as vg
from rulegrammar import Rule

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_rule_value_problems_flags_inline_comment_residue():
    assert vg.rule_value_problems(Rule("IP-ASN", "4134 // 中国电信骨干网", ("no-resolve",))) != []
    assert any("bare AS number" in p for p in vg.rule_value_problems(Rule("IP-ASN", "4134x", ())))
    assert any("whitespace" in p for p in vg.rule_value_problems(Rule("DOMAIN", "a b.com", ())))


def test_rule_value_problems_passes_clean_rules():
    assert vg.rule_value_problems(Rule("IP-ASN", "4134", ("no-resolve",))) == []
    assert vg.rule_value_problems(Rule("DOMAIN-SUFFIX", "telegra.ph", ())) == []
    # USER-AGENT values legitimately contain spaces — must not be flagged.
    assert vg.rule_value_problems(Rule("USER-AGENT", "Mozilla/5.0 (iPhone; CPU)", ())) == []


def test_committed_loon_tree_is_valid():
    assert vg.validate_generated_tree(REPO_ROOT / "rules" / "loon" / "generated") == []


def test_committed_shadowrocket_tree_is_valid():
    assert vg.validate_generated_tree(REPO_ROOT / "rules" / "shadowrocket" / "generated") == []


def test_manifest_entries_reads_tag_policy_filename():
    entries = vg.manifest_entries(REPO_ROOT / "rules" / "loon" / "generated")
    assert [tag for tag, _p, _f in entries] == vg.RULESET_ORDER
    assert all(fname.endswith(".list") for _t, _p, fname in entries)
