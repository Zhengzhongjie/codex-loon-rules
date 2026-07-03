"""Tests for the Shadowrocket config skeleton generator."""

from __future__ import annotations

import build_shadowrocket_config as sr
from build_loon_rules import RULESETS

BUILTIN_POLICIES = {"DIRECT", "REJECT", "PROXY"}


def _sections(conf: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = None
    for raw in conf.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections[current] = []
        elif current and line and not line.startswith("#"):
            sections[current].append(line)
    return sections


def test_canonical_sections_present_and_ordered():
    conf = sr.render_config(sr.DEVICES[0])
    headers = [ln.strip()[1:-1] for ln in conf.splitlines() if ln.startswith("[") and ln.strip().endswith("]")]
    assert headers == ["General", "Proxy", "Proxy Group", "Rule", "MITM"]


def test_rule_section_derives_one_ruleset_line_each_plus_final():
    rules = _sections(sr.render_config(sr.DEVICES[0]))["Rule"]
    rule_set_lines = [ln for ln in rules if ln.startswith("RULE-SET,")]
    assert len(rule_set_lines) == len(RULESETS)
    assert rules[-1] == "FINAL,全局代理"
    # Each ruleset maps to its policy at its Shadowrocket tree URL, in RULESETS priority order.
    for ruleset, line in zip(RULESETS, rule_set_lines):
        assert line == f"RULE-SET,{sr.SR_RAW_BASE}/{ruleset.file},{ruleset.policy}"


def test_every_rule_policy_resolves_to_a_group_or_builtin():
    conf = sr.render_config(sr.DEVICES[0])
    sections = _sections(conf)
    group_names = {ln.split("=", 1)[0].strip() for ln in sections["Proxy Group"]}
    for line in sections["Rule"]:
        policy = line.rsplit(",", 1)[1]
        assert policy in group_names or policy in BUILTIN_POLICIES, f"dangling policy: {policy}"


def test_device_delta_is_exactly_home_access_and_mitm_hostname():
    iphone = sr.render_config(sr.DEVICES[0]).splitlines()
    mac = sr.render_config(sr.DEVICES[1]).splitlines()
    # Ignore the first line (header names the device).
    only_iphone = set(iphone[1:]) - set(mac[1:])
    only_mac = set(mac[1:]) - set(iphone[1:])
    assert only_iphone == {"Home-Orca-WG = {{HOME_WG_NODE}}", "hostname = {{MITM_HOSTNAMES}}"}
    assert only_mac == set()


def test_private_sections_are_all_placeholders():
    import audit_public_artifacts as audit

    for device in sr.DEVICES:
        assert audit.private_section_leaks(sr.render_config(device)) == []


def test_build_writes_both_devices(tmp_path):
    sr.build(tmp_path)
    assert (tmp_path / "iphone.conf").exists()
    assert (tmp_path / "mac.conf").exists()
