# Surge is the third dialect: identity fold, own tree, full-fidelity modules

The migration target moves from Loon to Surge across iPhone, iPad, and Mac. Surge is the **reference
implementation** the Loon and Shadowrocket rule/module syntax descend from, so the port reuses the
existing "compile once, render per dialect" seam ([[docs/adr/0002]], [[docs/adr/0005]]) rather than
introducing anything new in the grammar.

## Rule dialect: identity fold, dedicated tree

- **Fold is the identity.** Surge natively keeps the separate `IP-CIDR6` type for IPv6 (Loon copied
  it from Surge; only Shadowrocket collapses IPv6 into dual-stack `IP-CIDR`). So `fold(rule, "surge")`
  passes through unchanged — the pre-existing "unhandled dialect passes through" branch already did the
  right thing; `SURGE` is added only to name it and document the intent.
- **Surge gets its own generated tree** (`rules/surge/generated/`) even though its `.list` bodies are
  byte-identical to the Loon tree (both fold to identity; only the manifest title and path prefix
  differ). This follows the per-client-tree pattern from [[docs/adr/0002]]: the config's `RULE-SET`
  URLs live in a reserved `surge/` namespace and can evolve independently, and cross-dialect row-count
  parity is preserved because dedup still runs once on canonical rules upstream of any fold.

## Config skeletons: mirror the Shadowrocket generator, Surge-ified

`tools/build_surge_config.py` mirrors `tools/build_shadowrocket_config.py`, deriving the `[Rule]`
bindings from the shared `RULESETS` catalogue so routing can never drift from the generated tree.
Surge-specific choices:

- **`[General]` in Surge idiom.** Shadowrocket-only keys (`bypass-system`) are dropped; Surge adds
  `loglevel`, `exclude-simple-hostnames`, and its own `internet-test-url` / `proxy-test-url` /
  `test-timeout`. `[Host]` DoH pinning (OKX/OKLink/OKEX) and the proxy-group shape carry over
  unchanged — `server:https://…` and `url-test` are Surge syntax to begin with.
- **Two devices, `ios` + `mac`.** One Surge iOS config serves both iPhone and iPad (Surge iOS is a
  single binary), so the skeleton is named `ios.conf`, not `iphone.conf`.
- **Device delta grows a third axis.** Beyond the existing delta (the `ios` variant carries the
  WireGuard home-access node and the MITM hostname list; `mac`, the home-access *target*, carries
  neither — see [[docs/adr/0004]]), the `mac` variant adds Mac-only `[General]` keys:
  `allow-wifi-access` + `wifi-access-*-port` (LAN proxy gateway) and `http-api` +
  `http-api-web-dashboard` (remote control). The HTTP-API key stays a `{{HTTP_API_KEY}}` placeholder;
  `[General]` is not a MITM/Proxy secret section, but the key is private, so it is filled during iCloud
  assembly like every other placeholder.

## Modules: full fidelity, MediaCheck restored

`docs/surge-modules.md` maps each Loon plugin to a Surge `.sgmodule`, preferring the Surge-native
build over any `.srmodule` sibling. Because Surge is the reference target, the directives the
Shadowrocket port lists as silently ignored (`engine=webview`, `http-response-jq`, `[Map Local]`,
`force-http-engine-hosts`) all run — the port carries **no known degradations**. Loon's `MediaCheck`
panel, dropped on Shadowrocket for lack of a panel concept, is **restored as a Surge Panel**.

## Considered Options

- **Subscribe Surge to the existing Loon tree** (share the URL namespace) — rejected: it couples two
  clients to one namespace and contradicts the per-client-tree pattern already established for
  Shadowrocket; a Surge-only future change would then be impossible without disturbing Loon.
- **One `iphone.conf` reused on iPad, mirroring the Loon `.lcf` naming** — rejected: the migration is
  Surge-first and the user explicitly runs iPad; `ios.conf` names the shared iOS surface honestly.
- **Minimal Mac delta (mirror Shadowrocket exactly)** — rejected for this migration: the Mac mini is
  the home-access target and benefits from being a LAN proxy gateway with remote control, so the
  Mac-only `[General]` keys are part of the intended device delta rather than drift.
- **Drop MediaCheck like the Shadowrocket port** — rejected: Surge has Panels, so the diagnostic
  surface can be restored instead of lost.
