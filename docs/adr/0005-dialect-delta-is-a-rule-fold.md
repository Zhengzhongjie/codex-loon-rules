# The dialect delta is a Rule→Rule fold; render_rule stays dialect-blind

Loon and Shadowrocket share one rule-list text grammar (`TYPE,value[,modifier...]`). The only
divergence (per [[docs/adr/0002]]) is a single rule *type*: IPv6 CIDRs are `IP-CIDR6` in the Loon
dialect and dual-stack `IP-CIDR` in the Shadowrocket dialect. So the dialect delta is a
**`Rule → Rule` normalization**, not a rendering difference.

Design of the "compile once, render twice" seam (D6):

- **`compile_rules` returns canonical rules** — `dict[str, list[Rule]]` — with all dedup/coverage
  run once on canonical `IP-CIDR6` rules. It no longer renders text, headers, or the manifest.
- **The fold lives in `rulegrammar.py`** as `fold(rule, dialect) -> Rule` (Loon = identity,
  Shadowrocket = `IP-CIDR6 → IP-CIDR`), applied at render time, strictly downstream of all dedup.
  This preserves cross-dialect row-count parity: both trees dedup identically, then fold 1:1.
- **`render_rule` does not change** — it stays a single dialect-blind `Rule → text` function, and its
  round-trip tests survive untouched. That the existing render survives byte-for-byte is the signal
  the seam is in the right place.
- **`header()` and `manifest_path()` stay builder-side** — they are per-dialect near-constants
  (attribution string, `rules/{dialect}/generated/`), builder output concerns, not grammar.

Rollout is staged. The compile/render split lands first, Loon-only, with `rules/loon/generated/`
byte-identical to the committed tree as the acceptance test — no dialect parameter yet. The
`fold`/`dialect` seam ships with its second, real adapter in the Shadowrocket port PR, so the seam is
never built ahead of a real crosser.

## Considered Options

- **Bundle fold + render into `Dialect.render_rule(Rule) -> str`** — rejected: forces `render_rule`
  to change and mixes the text grammar with dialect knowledge, when the delta is purely a Rule-type
  rename that the existing renderer already handles once folded.
- **Fold at compile time (emit different Rules per dialect)** — rejected: breaks row-count parity;
  dedup would run on already-folded rules and could treat the two trees' rules as distinct, so both
  the validator's coverage check and the manifest counts would diverge across dialects.
- **A standalone `dialect.py` both grammar and builder import** — rejected for now: D6 places the
  transform in `rulegrammar.py`, and a Rule-level fold belongs next to the Rule grammar; header/path
  belong to the builder. No third home earns its keep at two dialects.
