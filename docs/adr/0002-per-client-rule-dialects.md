# Rule lists are generated per client dialect; Shadowrocket gets IPv6 as dual-stack IP-CIDR

The builder emits one generated tree per client (`rules/loon/generated/`,
`rules/shadowrocket/generated/`) from the same source data. The only dialect divergence today is
IPv6: Loon's documented type is `IP-CIDR6` (official manual, the Loon author's own example ruleset,
and every major generator agree), while Shadowrocket's documented type is dual-stack `IP-CIDR`.
The Shadowrocket dialect therefore folds `IP-CIDR6` lines into `IP-CIDR` (20 lines today).

Context that will be surprising later: current Shadowrocket *does* parse `IP-CIDR6` — it silently
dropped such lines until v2.2.33 (2023-07) fixed it, and Repcz/Tool ships `IP-CIDR6` to Shadowrocket
unchanged. We still rewrite, because the keyword remains absent from Shadowrocket's documentation,
the pre-fix failure mode was a *silent* routing gap (the hardest kind to notice), and blackmatrix7
still normalizes the same way. Per-client trees are also the dominant community pattern
(blackmatrix7, Repcz, SukkaW, dler-io).

## Considered Options

- **Shared file keeping `IP-CIDR6`** — rejected: Shadowrocket would subscribe to an undocumented
  keyword on the strength of one changelog line; a regression or old build re-introduces the silent
  v6 gap.
- **Per-client tree with byte-identical content** (Repcz style) — rejected: reserves the URL
  namespace but keeps the same undocumented-keyword bet.
- **Shared file with unified `IP-CIDR,<v6>`** — rejected: undocumented in Loon, no generator
  precedent, contradicted by the Loon author's own rulesets.
