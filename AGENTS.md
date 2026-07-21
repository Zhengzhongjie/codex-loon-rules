# loon-rules-personal — Agent Instructions

Personal Loon routing notes, supplemental rule lists, and validation tooling. See `README.md` for the project map.

## HARD RULE — WireGuard node lines (recurred 4×, do not regenerate)

- NEVER regenerate or "pretty-print" the `Home-Orca-WG` (or any Loon WireGuard) proxy line from scratch. Copy it VERBATIM from the canonical snapshot: `.backups-loon-lcf/home-orca-wg.loon1-node.*.txt` (gitignored, contains real keys).
- Loon is NOT TOML. `private-key`, `public-key`, `preshared-key`, `allowed-ips` MUST stay double-quoted — base64 `=`/`+`/`/` and CIDR `/` collide with Loon's `=` and `,` delimiters. No spaces around `=` or after `,` (compact format only).
- Before handing any WireGuard line to the user or writing it anywhere, run `python3 tools/validate_loon_config.py` (or `check_proxy_wireguard` directly) and require OK.
- Target device is iPhone **Loon1** only. Never round-trip the line through Loon2 — it strips the quotes.

## Agent skills

### Issue tracker

Issues are tracked across **Linear (primary, source of truth)** and **GitHub (secondary, code + PRs)**. `/triage`, `to-issues`, `to-prd`, and `qa` read/write Linear first and mirror to GitHub when code is involved. External PRs are **not** a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Canonical defaults: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix` (mapped to Linear workflow states). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root, created lazily by `/domain-modeling`. See `docs/agents/domain.md`.
