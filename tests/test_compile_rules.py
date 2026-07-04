"""Behaviour tests for the pure rule compiler in tools/build_loon_rules.py."""

from __future__ import annotations

import build_loon_rules as blr


def test_cross_file_exact_dedup_drops_later_duplicate():
    rulesets = [
        blr.RuleSet("a.list", "A", "POLA", sources=("urlA",)),
        blr.RuleSet("b.list", "B", "POLB", sources=("urlB",)),
    ]
    contents = {
        "urlA": "DOMAIN,example.com\n",
        "urlB": "DOMAIN,example.com\n",
    }

    result = blr.compile_rules(rulesets, contents)

    assert blr.Rule("DOMAIN", "example.com") in result.compiled["a.list"]
    assert blr.Rule("DOMAIN", "example.com") not in result.compiled["b.list"]
    assert result.stats.duplicates_dropped == 1


def test_within_file_exact_dedup():
    rulesets = [blr.RuleSet("a.list", "A", "POLA", sources=("urlA",))]
    contents = {"urlA": "DOMAIN,dup.com\nDOMAIN,dup.com\n"}

    result = blr.compile_rules(rulesets, contents)

    assert result.compiled["a.list"].count(blr.Rule("DOMAIN", "dup.com")) == 1
    assert result.stats.duplicates_dropped == 1


def test_suffix_coverage_drops_later_covered_domain():
    rulesets = [
        blr.RuleSet("a.list", "A", "POLA", sources=("urlA",)),
        blr.RuleSet("b.list", "B", "POLB", sources=("urlB",)),
    ]
    contents = {
        "urlA": "DOMAIN-SUFFIX,example.com\n",
        "urlB": "DOMAIN,api.example.com\n",
    }

    result = blr.compile_rules(rulesets, contents)

    assert blr.Rule("DOMAIN", "api.example.com") not in result.compiled["b.list"]
    assert result.stats.covered_dropped == 1


def test_drop_if_covered_false_keeps_covered_rule():
    # The ChinaASN-Direct ruleset sets drop_if_covered=False; a covered rule must survive.
    rulesets = [
        blr.RuleSet("a.list", "A", "POLA", sources=("urlA",)),
        blr.RuleSet("b.list", "B", "POLB", sources=("urlB",), drop_if_covered=False),
    ]
    contents = {
        "urlA": "DOMAIN-SUFFIX,example.com\n",
        "urlB": "DOMAIN,api.example.com\n",
    }

    result = blr.compile_rules(rulesets, contents)

    assert blr.Rule("DOMAIN", "api.example.com") in result.compiled["b.list"]
    assert result.stats.covered_dropped == 0


def test_no_resolve_appends_to_ip_rules():
    rulesets = [blr.RuleSet("a.list", "A", "POLA", sources=("urlA",), no_resolve=True)]
    contents = {"urlA": "IP-CIDR,1.2.3.0/24\n"}

    result = blr.compile_rules(rulesets, contents)

    assert blr.Rule("IP-CIDR", "1.2.3.0/24", ("no-resolve",)) in result.compiled["a.list"]


def test_normalize_filters_keyword_unknown_and_comments():
    rulesets = [blr.RuleSet("a.list", "A", "POLA", sources=("urlA",))]
    contents = {
        "urlA": "\n".join(
            [
                "# a comment",
                "",
                "DOMAIN-KEYWORD,tracker",
                "URL-REGEX,something",
                "DOMAIN,keep.com",
            ]
        )
        + "\n"
    }

    result = blr.compile_rules(rulesets, contents)
    rules = result.compiled["a.list"]

    assert rules == [blr.Rule("DOMAIN", "keep.com")]


def test_bad_json_prefix_source_surfaces_in_failures_not_raised():
    rulesets = [blr.RuleSet("a.list", "A", "POLA", json_prefix_sources=("jsonU",))]
    contents = {"jsonU": "not json"}

    result = blr.compile_rules(rulesets, contents)

    assert any("jsonU" in f and "JSON_PARSE" in f for f in result.failures)


def test_good_json_prefix_source_yields_ip_rules():
    rulesets = [blr.RuleSet("a.list", "A", "POLA", json_prefix_sources=("jsonU",))]
    contents = {"jsonU": '{"prefixes":[{"ipv4Prefix":"1.2.3.0/24"}]}'}

    result = blr.compile_rules(rulesets, contents)

    assert blr.Rule("IP-CIDR", "1.2.3.0/24", ("no-resolve",)) in result.compiled["a.list"]
    assert result.failures == []


def test_compile_stats_counts_generated_files():
    rulesets = [blr.RuleSet("a.list", "A", "POLA", sources=("urlA",), notes=("note one",))]
    contents = {"urlA": "DOMAIN,keep.com\n"}

    result = blr.compile_rules(rulesets, contents)

    assert result.compiled["a.list"] == [blr.Rule("DOMAIN", "keep.com")]
    assert result.stats.generated == 1


def test_render_tree_emits_header_body_and_manifest():
    rulesets = [blr.RuleSet("a.list", "A", "POLA", sources=("urlA",), notes=("note one",))]
    contents = {"urlA": "DOMAIN,keep.com\n"}

    files = blr.render_tree(blr.compile_rules(rulesets, contents).compiled, rulesets, blr.LOON_DIALECT)
    body = files["a.list"]

    assert body.startswith("# A\n")
    assert "# Policy: POLA" in body
    assert "# note one" in body
    assert "DOMAIN,keep.com" in body
    manifest = files["MANIFEST.csv"]
    assert manifest.splitlines()[0] == "# Generated Loon rules manifest"
    assert "A,POLA,rules/loon/generated/a.list,1" in manifest


def test_shadowrocket_dialect_folds_ipv6_and_repaths_manifest():
    rulesets = [blr.RuleSet("a.list", "A", "POLA", sources=("urlA",))]
    contents = {"urlA": "IP-CIDR6,2001:db8::/32\nIP-CIDR,1.2.3.0/24\nDOMAIN,keep.com\n"}
    compiled = blr.compile_rules(rulesets, contents).compiled

    loon = blr.render_tree(compiled, rulesets, blr.LOON_DIALECT)["a.list"]
    sr = blr.render_tree(compiled, rulesets, blr.SHADOWROCKET_DIALECT)["a.list"]

    # Loon keeps IP-CIDR6; Shadowrocket folds it into dual-stack IP-CIDR.
    assert "IP-CIDR6,2001:db8::/32" in loon
    assert "IP-CIDR6" not in sr
    assert "IP-CIDR,2001:db8::/32" in sr
    # Non-IPv6 rows are untouched and row count stays in parity across dialects.
    assert "IP-CIDR,1.2.3.0/24" in sr and "DOMAIN,keep.com" in sr
    assert len(loon.splitlines()) == len(sr.splitlines())

    manifest = blr.render_tree(compiled, rulesets, blr.SHADOWROCKET_DIALECT)["MANIFEST.csv"]
    assert manifest.splitlines()[0] == "# Generated Shadowrocket rules manifest"
    assert "A,POLA,rules/shadowrocket/generated/a.list,3" in manifest


def test_write_result_replaces_artefacts(tmp_path):
    (tmp_path / "stale.list").write_text("old\n")
    (tmp_path / "MANIFEST.csv").write_text("old manifest\n")

    blr.write_result(tmp_path, {"new.list": "fresh\n", "MANIFEST.csv": "new manifest\n"})

    assert not (tmp_path / "stale.list").exists()
    assert (tmp_path / "new.list").read_text() == "fresh\n"
    assert (tmp_path / "MANIFEST.csv").read_text() == "new manifest\n"


def test_stats_lines_format():
    lines = blr.stats_lines(
        blr.CompileStats(generated=3, duplicates_dropped=2, covered_dropped=1, allowlisted_dropped=4)
    )

    assert lines == [
        "generated=3",
        "duplicates_dropped=2",
        "covered_later_rules_dropped=1",
        "service_allowlisted_dropped=4",
    ]
