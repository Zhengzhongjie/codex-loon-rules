# DNS authority sits at the tailnet layer; a clean upstream resolver bypasses OKX's mainland DNS geo-block

The failure that forced this: `www.okx.com` would not open on any device at home. Diagnosis
(reproduced live) is a **mainland-scoped DNS block of `www.okx.com`**, not a local hijack. The
gateway `192.168.1.1` — and several mainland resolvers (Tencent `119.29.29.29`, Baidu
`180.76.76.76`) — answer `www.okx.com` with a CNAME to `awscn.okpool.top`, whose authoritative
record is the dead link-local `169.254.0.2` on every resolver (AliDNS, 114DNS, Cloudflare all agree).
AliDNS (`223.5.5.5`) and 114DNS return the real Cloudflare CDN answer for the same name, and a request
to that answer gets a live `302` from OKX. DNS is the only broken link — the transport works. A
blast-radius scan across exchanges, wallets, banks, and mining pools found `www.okx.com` the *only*
name returning the dead address, so this is OKX's own geo-scoped authoritative DNS (a mainland
geo-block after its China-market exit), not a compromised gateway — the gateway just forwards to a
mainland resolver that honors the block.

Why it reached every device, and why the earlier fix missed: **Tailscale MagicDNS
(`100.100.100.100`) owns the system resolver**, and with no tailnet nameserver configured it
forwarded non-`ts.net` queries to the system default — the mainland resolver behind the gateway. The
`okx.com`/`oklink.com`/`okex.com` DoH pins in `configs/shadowrocket/*.conf` (commit `e0800b6`) never
get consulted on that path, because the proxy client is downstream of Tailscale's resolver. Pinning
DNS inside Loon/Shadowrocket fixes the wrong layer.

Decision: **put DNS authority at the tailnet layer.** In the Tailscale admin console set a global
nameserver to a clean upstream — **AliDNS `223.5.5.5`** — and enable **Override Local DNS**. One
tailnet-level change routes every device's non-`ts.net` DNS to a resolver that returns the real
answer, so the block is bypassed on Mac, iPhone, and iPad at once, and it holds even when Tailscale
(not Loon) owns the single iOS VPN slot. MagicDNS `*.ts.net` resolution is unaffected. AliDNS is
chosen for mainland reliability — `8.8.8.8` and `1.1.1.1` are unreachable/unstable on this network;
AliDNS resolves `www.okx.com` to the real Cloudflare answer and is not itself blocked. It is sent as
plain `:53`, which is acceptable because nothing on this path rewrites the answer — a direct
`@223.5.5.5` query returns clean. If a future on-path DNS interception ever tampers with plain-53,
escalate to an encrypted upstream: Cloudflare via Tailscale's automatic DoH, or NextDNS.

The client-layer DoH pins stay as a **second, independent layer**, not a replacement. When a proxy
client owns DNS — Loon on the Mac, or Loon holding the iOS slot — `configs/shadowrocket/*.conf` still
pins the OKX apex and subdomains to `1.1.1.1` DoH. Two layers own DNS in two different topologies:
the tailnet layer for "Tailscale is the resolver," the client layer for "the proxy client is the
resolver." Neither subsumes the other, so both are kept.

Residuals recorded, not resolved here:

- **iPhone single VPN slot.** OKX needs the proxy for login and trading, not just a clean name. When
  Tailscale holds the slot for home access, Loon is not running and OKX has no proxy path — clean DNS
  opens the page but not the proxied session. Fully proxied OKX on iPhone wants **Loon to own the
  slot** (proxy + DNS) with home access moved to a WireGuard peer inside Loon (WireGuard-in-Loon),
  retiring Tailscale from the iOS slot. That is the standing direction; it is not built in this
  change.
- **The block is upstream, not local.** Bypassing it at the tailnet layer protects only devices on
  the tailnet's clean DNS; any home device resolving through a mainland upstream (guests, a phone with
  Tailscale off) still gets the dead answer for `www.okx.com`. This is OKX's mainland geo-restriction,
  not a device compromise — so full login/trading needs a non-mainland proxy exit, not just clean DNS.
  Documented in [[docs/security-posture.md]].

## Considered Options

- **Point the gateway's own upstream DNS at a clean resolver** (set the router's WAN DNS to AliDNS so
  the whole LAN resolves clean) — reaches even non-tailnet devices on the home network. Rejected as
  the *primary* layer: it depends on controlling the gateway, covers only devices while they are on
  that LAN (nothing on cellular), and evaporates the moment the gateway is swapped or reset. A useful
  complement, not the load-bearing fix — the tailnet layer follows the device everywhere.
- **Let the proxy client own DNS everywhere** (Loon in the iOS slot, DoH pins as the only DNS
  authority) — rejected: it forfeits Tailscale home access on iPhone under the single-slot
  constraint, and does nothing on any device where Tailscale is the resolver. It is the right answer
  only *after* WireGuard-in-Loon removes the slot conflict.
- **Keep pinning at the client layer only** (extend the `*.conf` DoH pins, change nothing at the
  tailnet) — rejected: proven not to work here. Tailscale's resolver sits upstream of the proxy
  client, so client-layer pins are bypassed whenever MagicDNS answers first, which is exactly the
  failing path.
