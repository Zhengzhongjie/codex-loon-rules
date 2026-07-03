# Config skeletons keep private-section headers with placeholder values

The committed Shadowrocket config skeleton retains its private sections —
`[Proxy]`, `[Remote Proxy]`, `[Mitm]` — as headers with placeholder values, rather than omitting
them and having private assembly append the sections. iCloud assembly fills the placeholders with
real nodes, certificates, and MITM hostnames.

This directly changes the public-artifact audit's leak model. Today `audit_public_artifacts.py`
treats the mere presence of a `[Proxy]`/`[Remote Proxy]`/`[Mitm]` section header as a leak, because
the public repo commits no config at all (the Loon `.lcf` is never committed). Once a skeleton
carrying those headers is committed, that pattern would flag the intended sanitized artifact — a
false positive that breaks CI on exactly the file it is meant to guard.

So when the skeleton lands, the audit's section-header check must become **placeholder-aware**:
a value-bearing line inside a private section is a leak only if it is a real value, not a placeholder
token. The strong value patterns (PEM blocks, SS/VMess/VLESS-style proxy-URI schemes, and
token/key query-parameter secrets) stay unconditional and keep catching real leaks regardless of
section. The placeholder convention itself is defined when the skeleton format is designed.

Consequence for a future reader: seeing `[Proxy]` or `[Mitm]` in a public-repo file is **not** a leak
by itself — check whether the values are placeholders. This is why the scan-set widening (scan every
file by default, ADR context: fail closed) shipped separately and ahead of the leak-model change: the
two are independent, and the section-header model can only be finalized alongside the skeleton.

## Considered Options

- **Section-stripped skeleton** — omit `[Proxy]`/`[Remote Proxy]`/`[Mitm]` entirely; private
  assembly appends them. Rejected: chosen against in favor of a skeleton that shows its full shape
  (every section present, values stubbed) so the assembly step is a fill, not a structural graft.
  Would have kept the audit's strict section-header model unchanged — the trade-off is audit
  simplicity vs. skeleton completeness, and completeness won.
- **Keep the strict header-is-leak audit and commit a section-stripped skeleton** — same as above;
  rejected with it.
