# loon-rules-personal

Personal proxy routing: this repo generates sanitized, deduplicated rule lists and
config scaffolding for proxy client apps (Loon today, Shadowrocket in progress). The
repo is public; real nodes, certificates, MITM hostnames, and secrets never enter it.

## Language

### Rules and routing

**Rule list**:
A generated `.list` artifact of policy-agnostic match lines (`DOMAIN-SUFFIX,x`, `IP-CIDR,…`).
It carries no policy in its body — the policy is bound when a config subscribes to it.
_Avoid_: ruleset file, filter, subscription.

**Dialect**:
A client-specific rendering of the same rule data — identical matches, client-appropriate keywords
(IPv6 CIDRs are `IP-CIDR6` in the Loon and Surge dialects, folded into dual-stack `IP-CIDR` in the
Shadowrocket dialect; Surge is the reference implementation the type was copied from, so its fold is
the identity). One source, one generated tree per dialect (`loon`, `shadowrocket`, `surge`).
_Avoid_: format, flavor, variant.

**Policy**:
The routing destination a matched request is sent to — a named policy group (`AI`, `广告分流`)
or a literal (`DIRECT`, `REJECT`, `全局代理`). Both Loon and Shadowrocket name it on the
reference line, not in the rule list body.
_Avoid_: action, target, decision.

**Policy binding**:
The config-level line that attaches a rule list to a policy. Loon writes it in `[Remote Rule]`;
Shadowrocket writes it as `RULE-SET,<url>,<policy>` in `[Rule]`. Same rule list, two syntaxes.
_Avoid_: subscription line, remote rule.

**Policy group**:
A user-selectable group of proxies/decisions bound to a policy name (e.g. `AI` = proxy-then-DIRECT).
Loon calls this a "policy group"; Shadowrocket's config section is `[Proxy Group]` — same concept.
_Avoid_: proxy group (Shadowrocket's word), node group.

**Coverage / covered**:
A rule is *covered* when a broader already-kept rule (e.g. a `DOMAIN-SUFFIX`) subsumes it, so the
builder drops it. Distinct from an exact *duplicate*.
_Avoid_: shadowed, redundant.

**Drift**:
Unintended divergence between artifacts meant to stay in sync. *Upstream drift*: a generated rule
list no longer matches its reviewed upstream sources. *Skeleton drift*: the device variants of a
config skeleton diverge beyond the device delta.
_Avoid_: out-of-date, desync.

### Client apps and their bundles

**Plugin**:
Loon's enhancement bundle (`.plugin`) — MITM hostnames, header rewrites, and scripts. Tends to
embed private data, so it lives in the private config layer, not the public repo.

**Module**:
Shadowrocket's and Surge's equivalent bundle. The Surge-native format is `.sgmodule`; Shadowrocket
imports the same `.sgmodule` but some upstreams also ship a Shadowrocket-native `.srmodule` / `.module`
(preferred for the Shadowrocket port when it exists). The Surge port prefers the `.sgmodule` and loses
none of the Surge-only directives Shadowrocket ignores. Each port maps every Loon plugin to a module.
Same role as a plugin, different file format.
_Avoid_: plugin (that's Loon's word).

### Public / private boundary

**Sanitized artifact**:
Any file this public repo emits: rule lists, config skeletons, module skeletons. Guaranteed free of
_real_ nodes, certificates, MITM hostnames, passphrases — enforced by `tools/audit_public_artifacts.py`.
A config skeleton may legitimately carry private-section headers (`[Proxy]`, `[Mitm]`) with placeholder
values; a header alone is not a leak, only a real value is (see [[docs/adr/0004]]).

**Config skeleton**:
A committed, placeholder-bearing config the public repo generates — a Shadowrocket- and Surge-side
artifact. The real private `.conf` is assembled outside the repo, in iCloud, by filling the skeleton
with private nodes/certs/MITM data (and, for Surge Mac, the HTTP-API key). Loon deliberately has no
skeleton: its `.lcf` is maintained directly in iCloud and the repo only validates it.
_Avoid_: template (too generic), config.

**Placeholder**:
A `{{NAME}}` token standing in for a private value in a config skeleton (`{{PROXY_NODES}}`,
`{{MITM_HOSTNAME}}`, `{{CA_P12}}`). Double braces are chosen because they never collide with
Shadowrocket/Surge config or module syntax (unlike `%…%`, which is the module merge marker).
The audit's leak model treats a non-placeholder real value inside a private section as a leak
(see [[docs/adr/0004]]).
_Avoid_: variable, stub, token (bare).

**Device delta**:
The small, explicitly enumerated set of entries by which the mac variant of a config legitimately
differs from the iphone/ipad (iOS) variant: home-access node and MITM hostname (iOS-only), and — in
the Surge port — Mac-only `[General]` keys (LAN proxy sharing + HTTP API). Any difference outside the
delta is skeleton drift.
_Avoid_: fork, per-device divergence.
