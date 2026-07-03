# Shadowrocket modules are referenced from upstream, not vendored or converted

The Shadowrocket config skeletons reference each enhancement module at its upstream URL, exactly as
the Loon `.lcf` references upstream `.plugin` URLs today (including auto-updating
`releases/latest/download/` links). A per-plugin survey of all 21 referenced plugins found 20 with
an upstream official Surge/Shadowrocket build — preferring the Shadowrocket-native
`.srmodule`/`.module` where the maintainer ships one. The single gap (MediaCheck, a Loon *panel* —
a concept Shadowrocket lacks entirely) is dropped from the Shadowrocket config rather than
rewritten. Known degradations from Surge-only directives that Shadowrocket silently ignores
(`http-response-jq` body rewrites, `[Map Local]`, `force-http-engine-hosts`, `engine=webview`) are
documented, not patched.

This looks inconsistent with ADR 0002 (the repo *does* generate per-client rule dialects itself).
It isn't: rule lists are policy-agnostic data whose dialect delta is one keyword this repo already
owns end-to-end; modules are living code maintained upstream. Vendoring or forking them would
freeze the code, transfer the update burden here, and change a trust model that has worked on the
Loon side for years. The port must not change the trust model.

## Considered Options

- **Convert all 21 plugins into committed module skeletons** — rejected: requires maintaining a
  Loon→Surge converter for rewrite/script syntax, loses automatic upstream updates, and duplicates
  work most maintainers already do (they ship both flavors from one source, updated in lockstep).
- **Fork/patch modules to fix the Surge-only degradations** — rejected: permanent maintenance
  burden; the degradations are silent-ignore feature losses, not breakage.
- **Rewrite MediaCheck for Shadowrocket** — rejected: Loon panels have no Shadowrocket
  counterpart; it is a diagnostic tool, not routing-critical.
