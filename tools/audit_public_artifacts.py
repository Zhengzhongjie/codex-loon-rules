#!/usr/bin/env python3
"""Fail if public repository artifacts contain obvious private material."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PEM_BOUNDARY = "-" * 5

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private key", re.compile(PEM_BOUNDARY + r"BEGIN [A-Z ]*PRIVATE KEY" + PEM_BOUNDARY)),
    ("certificate", re.compile(PEM_BOUNDARY + r"BEGIN CERTIFICATE" + PEM_BOUNDARY)),
    ("proxy uri", re.compile(r"\b(?:ss|ssr|vmess|vless|trojan|hysteria2?|tuic)://", re.I)),
    (
        "token query parameter",
        re.compile(r"[?&](?:token|key|api_key|access_token|auth|password|passwd|secret)=", re.I),
    ),
]

# Placeholder-aware leak model for private config sections. A config skeleton legitimately carries
# [Proxy]/[Mitm] section headers, so a header alone is not a leak (ADR-0004). Instead, any value in a
# private section must be a {{PLACEHOLDER}}; a real node definition or a real CA cert/passphrase is
# the leak. This runs in addition to the unconditional value patterns above.
_PLACEHOLDER = re.compile(r"\{\{[A-Za-z0-9_-]+\}\}")
_PROXY_SECTIONS = {"proxy", "remote proxy"}
_MITM_SECTIONS = {"mitm", "https"}
# Allowlist of MITM keys that may carry a real value; everything else (hostname, ca-p12,
# ca-passphrase, and any future cert/key option) must be a placeholder in a public skeleton.
# MITM hostnames are private per docs/security-posture.md — they reveal which apps are intercepted.
_MITM_PUBLIC_KEYS = {"enable", "h2"}


def _is_placeholder_value(value: str) -> bool:
    """True when the value is only {{…}} placeholders (plus separators) — nothing real leaks."""
    return _PLACEHOLDER.sub("", value).strip(" ,\t") == ""


def private_section_leaks(text: str) -> list[str]:
    """Flag real (non-placeholder) values inside private config sections."""
    problems: list[str] = []
    section: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        if not line or line.startswith(("#", ";")):
            continue
        if section in _PROXY_SECTIONS:
            value = line.split("=", 1)[1] if "=" in line else line
            if not _is_placeholder_value(value):
                problems.append(f"non-placeholder value in [{section}] section: {line}")
        elif section in _MITM_SECTIONS and "=" in line:
            key, value = line.split("=", 1)
            if key.strip().lower() not in _MITM_PUBLIC_KEYS and not _is_placeholder_value(value):
                problems.append(f"non-placeholder value in MITM section: {line}")
    return problems

# Scan every committed file as text by default, excluding only known-binary
# suffixes. Fails closed: a new artifact type (config skeleton .conf, module
# .sgmodule/.srmodule) is covered the moment it lands, instead of silently
# skipped until someone remembers to widen an allowlist. Binaries that slip
# through are caught by the UnicodeDecodeError guard in main().
SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".pdf",
    ".zip",
    ".gz",
    ".tar",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
}


def should_scan(path: Path) -> bool:
    if ".git" in path.parts or "__pycache__" in path.parts:
        return False
    if path.name == ".DS_Store":
        return False
    return path.suffix.lower() not in SKIP_SUFFIXES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    args = parser.parse_args()

    errors: list[str] = []
    for path in sorted(p for p in args.root.rglob("*") if p.is_file() and should_scan(p)):
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path}: contains {label}")
        errors.extend(f"{path}: {problem}" for problem in private_section_leaks(text))

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("OK: public artifact audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
