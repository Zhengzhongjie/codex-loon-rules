"""Tests for the shared, dialect-neutral generated-tree validator."""

from __future__ import annotations

from pathlib import Path

import pytest

import validate_generated as vg
from rulegrammar import Rule

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_single_file_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str) -> Path:
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    monkeypatch.setattr(vg, "RULESET_ORDER", ["Test"])
    (generated_dir / "MANIFEST.csv").write_text(
        "Test,DIRECT,rules/loon/generated/test.list,1\n"
    )
    (generated_dir / "test.list").write_text(body)
    return generated_dir


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


def test_committed_surge_tree_is_valid():
    assert vg.validate_generated_tree(REPO_ROOT / "rules" / "surge" / "generated") == []


def test_manifest_entries_reads_tag_policy_filename():
    entries = vg.manifest_entries(REPO_ROOT / "rules" / "loon" / "generated")
    assert [tag for tag, _p, _f in entries] == vg.RULESET_ORDER
    assert all(fname.endswith(".list") for _t, _p, fname in entries)


def test_missing_generated_directory_fails_closed(tmp_path):
    generated_dir = tmp_path / "missing-generated"

    try:
        errors = vg.validate_generated_tree(generated_dir)
    except FileNotFoundError:
        return

    assert errors, "a missing generated directory must not validate successfully"


def test_empty_generated_rule_file_is_reported(tmp_path, monkeypatch):
    generated_dir = _write_single_file_tree(tmp_path, monkeypatch, "")

    errors = vg.validate_generated_tree(generated_dir)

    assert errors, "an empty generated rule file must not validate successfully"


def test_unknown_generated_rule_type_is_reported(tmp_path, monkeypatch):
    generated_dir = _write_single_file_tree(
        tmp_path,
        monkeypatch,
        "UNKNOWN-RULE,example.com\n",
    )

    errors = vg.validate_generated_tree(generated_dir)

    assert errors, "an unknown generated rule type must not validate successfully"
