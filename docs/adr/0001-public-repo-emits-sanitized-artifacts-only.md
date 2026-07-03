# Public repo emits sanitized artifacts only; private config assembled in iCloud

The Shadowrocket port targets a full private config (`.conf` + ~21 modules + nodes/certs/MITM),
but this repo is public. We keep the existing Loon boundary: the repo emits only **sanitized
artifacts** — rule lists, config skeletons, and module skeletons with placeholders for MITM
hostnames, script URLs, and secrets. The real private `.conf` is assembled outside the repo, in
iCloud, the same way the Loon `.lcf` already is. `tools/audit_public_artifacts.py` continues to
guard the boundary.

## Considered Options

- **Separate private repo** for the full Shadowrocket config — rejected: adds a second repo and CI,
  and two-repo sync, for no benefit over assembling in iCloud like `.lcf`.
- **Commit the full private config here** — rejected: violates the security posture; would write
  nodes, certificates, and MITM hostnames into public git history.
