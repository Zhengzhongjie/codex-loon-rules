# Loon security posture

This repository must stay safe to publish. Do not commit full `.lcf` files,
proxy nodes, remote proxy subscription URLs, certificates, passphrases, API
tokens, or MITM hostnames.

## Account-risk posture

- Prefer stable routing over fastest-node switching for finance, crypto,
  payment, social, and streaming accounts.
- Keep mainland实名 services on `DIRECT` unless there is a specific reason to
  proxy them.
- Keep PayPal separate from the broader finance/crypto group so it can use a
  dedicated stable exit.
- Avoid MITM/rewrite plugins for authenticated app business traffic. DNS and
  HTTPDNS hygiene are lower risk than request-body/header rewriting.
- Treat ad blocking and app enhancement plugins as optional. Disable them first
  when login, playback, payment, captcha, or account-risk signals appear.

## Public artifacts

Safe to publish:

- Domain rule lists under `rules/loon/`.
- Routing-order documentation.
- Validation and secret-audit tooling.

Unsafe to publish:

- `[Proxy]`, `[Remote Proxy]`, and complete `[Mitm]` material.
- Node names if they reveal subscription/provider identity.
- Subscription URLs or URLs with token-like query parameters.
- Certificates, passphrases, private keys, cookies, or account identifiers.

## Leak defense: audit the index, gate the commit

`tools/audit_public_artifacts.py` scans the **git index** (tracked ∪ staged — exactly
what the next commit publishes) by default, reading blob content from the index rather
than the working tree. Untracked local files (real-config backups under
`.backups-loon-lcf/`, tool logs) are deliberately out of scope: they cannot enter a
commit, and flagging them trains people to ignore failures. `--all` restores the
whole-disk sweep for ad-hoc use.

The audit runs at two points, fail-closed at both:

1. **Locally, before every commit** — `githooks/pre-commit` (enable once per clone with
   `git config core.hooksPath githooks`). This is the only gate that fires *before*
   content becomes public; CI runs after push, when retraction is already ineffective.
2. **In CI** (`loon-rule-drift.yml`) — the backstop for clones that skipped the hook
   setup or committed with `--no-verify`.

Real-config backups (`.backups-loon-lcf/*.lcf`) are on-disk rollback snapshots that
carry real nodes/certs/MITM values. They are gitignored and must never be staged; the
index audit is the enforcement if the ignore rule is ever bypassed.

## Local Loon policy

Use the generated rules in `rules/loon/generated/` as the subscription source.
The generator pulls reviewed upstream sources, applies local supplements, and
drops exact duplicates plus later rules already covered by earlier
`DOMAIN-SUFFIX` rules.

High-level generated order:

1. Reject and LAN rules.
2. `AccountSafety-DIRECT` and mainland direct foundations.
3. Device/service rules such as `Seetong-Local`.
4. Stable payment, finance, and crypto rules.
5. Company/service rules.
6. Category aggregation rules.
7. ASN/direct catchalls.

The config should not mix these generated subscriptions with the original
upstream subscriptions, because that reintroduces duplicate and shadowed rules.

## www.okx.com resolves dead on mainland DNS (not a gateway compromise)

`www.okx.com` resolves to the dead link-local `169.254.0.2` when queried through
the home gateway (`192.168.1.1`) and several mainland recursive resolvers
(Tencent `119.29.29.29`, Baidu `180.76.76.76`). The answer is a CNAME to
`awscn.okpool.top`, whose authoritative record is `169.254.0.2` everywhere —
AliDNS, 114DNS, and Cloudflare all return the same dead address for it, so that
sinkhole record is set at the `okpool.top` zone, not injected locally.

This is **not** a gateway compromise. A blast-radius scan (crypto exchanges,
wallets, banks, mining pools, common sites) found `www.okx.com` to be the *only*
name returning the dead address; every other domain resolved to real IPs on the
gateway, differing from a clean resolver by nothing more than normal CDN/geo
variance. AliDNS (`223.5.5.5`/`223.6.6.6`) and 114DNS (`114.114.114.114`) return
the real Cloudflare answer for the same name. The split — some mainland resolvers
dead, others live — is OKX's own geo-scoped authoritative DNS (a mainland
geo-block after its China-market exit); the gateway merely forwards to a resolver
that honors it.

The fix is resolver choice, not gateway cleanup: resolve through AliDNS at the
tailnet layer (see [[docs/adr/0006]]). Notes:

- No router audit or reflash is warranted on this evidence. The gateway is not
  rewriting exchange/bank domains to attacker infrastructure.
- The bypass protects only devices on the tailnet's clean DNS. Any device
  resolving through a mainland upstream (guests, a phone with Tailscale off) will
  still get the dead answer for `www.okx.com`.
- Clean DNS opens the page but does not defeat the geo-block for login/trading —
  that still needs a non-mainland proxy exit (Loon), which is the routing half,
  separate from the DNS half.
