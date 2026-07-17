"""Offline tests for tools/check_loon_rule_drift.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import build_loon_rules
import check_loon_rule_drift as drift


def _compiled_tree(monkeypatch, dialect=build_loon_rules.LOON_DIALECT):
    rulesets = [
        build_loon_rules.RuleSet(
            "sample.list",
            "Sample",
            "DIRECT",
            additions=("DOMAIN,example.com",),
        )
    ]
    monkeypatch.setattr(build_loon_rules, "RULESETS", rulesets)
    result = build_loon_rules.compile_rules(rulesets, {})
    return result, build_loon_rules.render_tree(result.compiled, rulesets, dialect)


def _write_generated_tree(rules_dir: Path, dialect, files: dict[str, str]) -> Path:
    generated_dir = rules_dir / dialect.subdir / "generated"
    generated_dir.mkdir(parents=True)
    for name, contents in files.items():
        path = generated_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
    return generated_dir


def test_report_tree_returns_zero_when_generated_tree_matches(monkeypatch, tmp_path, capsys):
    result, rebuilt = _compiled_tree(monkeypatch)
    rules_dir = tmp_path / "rules"
    _write_generated_tree(rules_dir, build_loon_rules.LOON_DIALECT, rebuilt)

    exit_code = drift.report_tree(
        build_loon_rules.LOON_DIALECT,
        result,
        rules_dir,
        diff=False,
        max_diff_lines=20,
    )

    assert exit_code == 0
    assert "OK: generated loon rules match" in capsys.readouterr().out


def test_report_tree_returns_one_when_generated_directory_is_missing(tmp_path, capsys):
    result = build_loon_rules.CompileResult(
        compiled={},
        stats=build_loon_rules.CompileStats(0, 0, 0),
        failures=[],
    )

    exit_code = drift.report_tree(
        build_loon_rules.LOON_DIALECT,
        result,
        tmp_path / "rules",
        diff=False,
        max_diff_lines=20,
    )

    assert exit_code == 1
    assert "FAIL: generated rule directory does not exist" in capsys.readouterr().out


def test_report_tree_returns_two_and_classifies_added_removed_changed(
    monkeypatch, tmp_path, capsys
):
    result, rebuilt = _compiled_tree(monkeypatch)
    rules_dir = tmp_path / "rules"
    current = {
        "MANIFEST.csv": rebuilt["MANIFEST.csv"] + "local edit\n",
        "removed.list": "DOMAIN,removed.example\n",
    }
    _write_generated_tree(rules_dir, build_loon_rules.LOON_DIALECT, current)

    exit_code = drift.report_tree(
        build_loon_rules.LOON_DIALECT,
        result,
        rules_dir,
        diff=False,
        max_diff_lines=20,
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "added: sample.list" in output
    assert "removed: removed.list" in output
    assert "changed: MANIFEST.csv" in output


def test_main_diff_output_honors_max_diff_lines(monkeypatch, tmp_path, capsys):
    rules_dir = tmp_path / "rules"
    _write_generated_tree(
        rules_dir,
        build_loon_rules.LOON_DIALECT,
        {"MANIFEST.csv": "old manifest\nold detail\n"},
    )
    monkeypatch.setattr(build_loon_rules, "RULESETS", [])
    monkeypatch.setattr(build_loon_rules, "DIALECTS", (build_loon_rules.LOON_DIALECT,))
    monkeypatch.setattr(build_loon_rules, "fetch_all", lambda: ({}, []))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_loon_rule_drift.py",
            "--rules-dir",
            str(rules_dir),
            "--diff",
            "--max-diff-lines",
            "4",
        ],
    )

    exit_code = drift.main()

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "--- current/loon/MANIFEST.csv" in output
    assert "+++ rebuilt/loon/MANIFEST.csv" in output
    assert "... diff truncated after 4 lines" in output


@pytest.mark.parametrize("failure_kind", ["fetch", "parse"])
def test_main_fails_closed_on_fetch_or_parse_failure(
    failure_kind, monkeypatch, tmp_path, capsys
):
    if failure_kind == "fetch":
        monkeypatch.setattr(build_loon_rules, "RULESETS", [])
        monkeypatch.setattr(
            build_loon_rules,
            "fetch_all",
            lambda: ({}, ["https://example.invalid/rules.list: offline failure"]),
        )
    else:
        source = "https://example.invalid/prefixes.json"
        monkeypatch.setattr(
            build_loon_rules,
            "RULESETS",
            [
                build_loon_rules.RuleSet(
                    "prefixes.list",
                    "Prefixes",
                    "DIRECT",
                    json_prefix_sources=(source,),
                )
            ],
        )
        monkeypatch.setattr(
            build_loon_rules,
            "fetch_all",
            lambda: ({source: "not valid JSON"}, []),
        )

    monkeypatch.setattr(
        sys,
        "argv",
        ["check_loon_rule_drift.py", "--rules-dir", str(tmp_path / "rules")],
    )

    exit_code = drift.main()

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "FETCH_FAIL:" in output
    assert "FAIL: cannot assess drift after upstream fetch or parse failures" in output
