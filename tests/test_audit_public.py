"""Tests for the placeholder-aware public-artifact audit."""

from __future__ import annotations

import audit_public_artifacts as audit


def test_placeholder_private_sections_pass():
    skeleton = (
        "[Proxy]\n"
        "{{PROXY_NODES}}\n"
        "Home-Orca-WG = {{HOME_WG_NODE}}\n"
        "[MITM]\n"
        "enable = true\n"
        "hostname = {{MITM_HOSTNAMES}}\n"
        "ca-passphrase = {{CA_PASSPHRASE}}\n"
        "ca-p12 = {{CA_P12}}\n"
    )
    assert audit.private_section_leaks(skeleton) == []


def test_real_node_definition_is_flagged():
    leak = "[Proxy]\nMyNode = vless, 1.2.3.4, 443\n"
    assert audit.private_section_leaks(leak)


def test_real_ca_material_is_flagged():
    leak = "[MITM]\nca-p12 = MIIJRQIBAzCCCQ8\nca-passphrase = 24961EL2\n"
    assert len(audit.private_section_leaks(leak)) == 2


def test_mitm_public_keys_allowed_but_hostname_flagged():
    # enable / h2 are non-secret and may carry real values...
    assert audit.private_section_leaks("[MITM]\nenable = true\nh2 = true\n") == []
    # ...but a real MITM hostname is private (reveals intercepted apps) and must be a placeholder.
    assert audit.private_section_leaks("[MITM]\nhostname = *.paypal.com\n")


def test_hyphenated_placeholder_is_recognized():
    assert audit.private_section_leaks("[Proxy]\n{{US-NODES}}\n") == []


def test_public_sections_are_ignored():
    # A real value in [Proxy Group] (public wiring) is not a private-section leak.
    conf = "[Proxy Group]\nAI = select,链式代理链路,DIRECT\n"
    assert audit.private_section_leaks(conf) == []
