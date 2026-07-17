#!/usr/bin/env python3
"""Validate a generated rule-list tree — dialect-neutral, shared by every client validator.

The two dialect trees (rules/loon/generated, rules/shadowrocket/generated) re-converge here: both
are just deduped `.list` trees plus a MANIFEST.csv, so this validator needs no dialect branching. It
checks the manifest order against the RULESETS oracle, flags stale files, and re-runs the builder's
dedup/coverage over the emitted lines. Both the order and the coverage exemption are derived from
RULESETS so the check tracks the builder's authored intent, not a hand-copied mirror.
"""

from __future__ import annotations

from pathlib import Path

import build_loon_rules
from rulegrammar import CoverageIndex, parse_rule

# Authored intent, shared across dialects: the tag order and the "keep even if covered" exemption.
RULESET_ORDER = [ruleset.tag for ruleset in build_loon_rules.RULESETS]
NO_COVER_TAGS = frozenset(rs.tag for rs in build_loon_rules.RULESETS if not rs.drop_if_covered)

# Host/IP-matching rule types whose value never legitimately contains whitespace.
_NO_WHITESPACE_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-REGEX", "IP-CIDR", "IP-CIDR6", "IP-ASN"}


def active_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def rule_value_problems(rule) -> list[str]:
    """Semantic value checks for a parsed rule (guards against leaked inline comments).

    Domain/IP values never contain whitespace; USER-AGENT/PROCESS-NAME legitimately may, so the
    whitespace check is scoped to host/IP-matching types. IP-ASN must be a bare AS number.
    """
    problems: list[str] = []
    if rule.rule_type in _NO_WHITESPACE_TYPES and any(ch.isspace() for ch in rule.value):
        problems.append("rule value has whitespace (inline comment?)")
    if rule.rule_type == "IP-ASN" and not rule.value.isdigit():
        problems.append("IP-ASN value must be a bare AS number")
    return problems


def manifest_entries(generated_dir: Path) -> list[tuple[str, str, str]]:
    """(tag, policy, filename) rows from a tree's own MANIFEST.csv."""
    entries: list[tuple[str, str, str]] = []
    for raw in (generated_dir / "MANIFEST.csv").read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        tag, policy, path, _count = [part.strip() for part in line.split(",", 3)]
        entries.append((tag, policy, Path(path).name))
    return entries


def validate_generated_tree(generated_dir: Path) -> list[str]:
    """Return a list of invariant violations for one generated rule tree (empty = valid)."""
    errors: list[str] = []
    entries = manifest_entries(generated_dir)
    if [tag for tag, _policy, _file in entries] != RULESET_ORDER:
        errors.append(f"{generated_dir.name}: manifest order does not match expected RULESETS order")
    expected_files = {filename for _tag, _policy, filename in entries}
    actual_files = {path.name for path in generated_dir.glob("*.list")}
    stale_files = sorted(actual_files - expected_files)
    if stale_files:
        errors.append(f"{generated_dir.name}: stale generated rule files: " + ", ".join(stale_files))

    index = CoverageIndex()
    for tag, _policy, filename in entries:
        path = generated_dir / filename
        if not path.exists():
            errors.append(f"generated rule file missing: {filename}")
            continue
        local_seen: set[tuple[str, str]] = set()
        lines = active_lines(path.read_text())
        if not lines:
            # The builder never emits a rule list without rules — an empty file means a
            # truncated or corrupted artifact and must not validate.
            errors.append(f"{filename}: rule file has no active rules")
        for raw in lines:
            rule = parse_rule(raw)
            if rule is None:
                errors.append(f"{filename}: invalid rule line: {raw}")
                continue
            if rule.rule_type not in build_loon_rules.ALLOWED_RULE_TYPES:
                errors.append(f"{filename}: unknown rule type {rule.rule_type}: {raw}")
                continue
            errors.extend(f"{filename}: {msg}: {raw}" for msg in rule_value_problems(rule))
            key = (rule.rule_type, rule.value)
            if key in local_seen:
                errors.append(f"{filename}: duplicate local rule: {raw}")
            cross_tag = index.exact_tag(rule)
            if cross_tag is not None:
                errors.append(f"{filename}: duplicate cross-file rule also in {cross_tag}: {raw}")
            covered = index.covered_by(rule)
            if covered is not None and tag not in NO_COVER_TAGS:
                errors.append(f"{filename}: rule covered by earlier {covered}: {raw}")
            local_seen.add(key)
            index.add(rule, tag)
    return errors
