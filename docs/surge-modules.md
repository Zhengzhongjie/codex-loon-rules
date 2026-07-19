# Surge modules

A Surge `.conf` **does not embed module URLs** — modules are a separate, app-managed file type
(`.sgmodule`, the Surge-native format the Loon `.plugin` / Shadowrocket `.sgmodule` ecosystems both
descend from). So this repo emits the config skeleton and this module list as **independent
artifacts**: the `.conf` handles routing, and you install the modules separately in-app.

Install each module in Surge: **Home → Modules → Install from URL → paste URL → Done** (iCloud then
syncs the installed module list across iPhone, iPad, and Mac). Per
[ADR-0003](adr/0003-modules-referenced-from-upstream.md), these are referenced from upstream, not
vendored or converted; Surge is the **reference implementation** these `.sgmodule` files are written
for, so the Surge-native `.sgmodule` build is preferred wherever one exists.

## Full fidelity, unlike the Shadowrocket port

The Shadowrocket port ([docs/shadowrocket-modules.md](shadowrocket-modules.md)) documents directives
that Shadowrocket silently ignores — `engine=webview` scripts, `http-response-jq` / `[Body Rewrite]`,
`[Map Local]`, `force-http-engine-hosts`. **Surge supports all of them**, so the Surge port carries no
such degradations: prefer the `.sgmodule` over any `.srmodule` sibling, and the Surge-only argument
and script features run as authored.

## Module map (Loon plugin → Surge module)

| Loon plugin | Surge module URL | Notes |
| --- | --- | --- |
| wloc.lpx | `https://raw.githubusercontent.com/Yu9191/wloc/refs/heads/main/modules/wloc.sgmodule` | Surge-native `.sgmodule`; coordinates hardcoded (edit or use the project's picker). Verify the path on install. |
| boxjs.rewrite.loon.plugin | `https://raw.githubusercontent.com/chavyleung/scripts/master/box/rewrite/boxjs.rewrite.surge.sgmodule` | Surge flavor; `force-http-engine-hosts` runs on Surge |
| General.plugin | `https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/sgmodule/General.sgmodule` | `always-real-ip` works with Surge's built-in Fake-IP DNS |
| DNS.plugin | `https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/sgmodule/DNS.sgmodule` | Surge-5 `[General]` keys apply natively |
| HTTPDNS.Block.plugin | `https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/sgmodule/HTTPDNS.Block.sgmodule` | `force-http-engine-hosts` runs on Surge |
| AdvertisingLite.plugin | `https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Surge/AdvertisingLite/AdvertisingLite.sgmodule` | Surge-specific build (rewrite/Surge/ path) |
| YouTube_remove_ads.lpx | `https://raw.githubusercontent.com/Maasea/sgmodule/master/YouTube.Enhance.sgmodule` | `[Map Local]` runs on Surge |
| DualSubs.YouTube.plugin | `https://github.com/DualSubs/YouTube/releases/latest/download/DualSubs.YouTube.sgmodule` | `engine=webview` scripts run on Surge |
| iRingo.LocationService.plugin | `https://github.com/NSRingo/LocationServices/releases/latest/download/iRingo.LocationService.sgmodule` | official same-release |
| iRingo.Maps.plugin | `https://github.com/NSRingo/Maps/releases/latest/download/iRingo.Maps.sgmodule` | `engine=webview` runs on Surge |
| iRingo.TV.plugin | `https://github.com/NSRingo/TV/releases/latest/download/iRingo.TV.sgmodule` | Surge-native `.sgmodule` preferred over the SR `.srmodule` |
| iRingo.WeatherKit.Workers.plugin | `https://github.com/NSRingo/WeatherKit/raw/main/modules/iRingo.WeatherKit.Workers.sgmodule` | Workers variant (main branch) |
| iRingo.News.plugin | `https://github.com/NSRingo/News/releases/latest/download/iRingo.News.sgmodule` | uses `{{{Proxy}}}` module argument (native Surge) |
| BiliBili.ADBlock.plugin | `https://github.com/BiliUniverse/ADBlock/releases/latest/download/BiliBili.ADBlock.sgmodule` | `http-response-jq` body rewrite runs on Surge 5 |
| BiliBili.Enhanced.plugin | `https://github.com/BiliUniverse/Enhanced/releases/latest/download/BiliBili.Enhanced.sgmodule` | `.sgmodule` preferred; `#!arguments` run on Surge |
| BiliBili.Global.plugin | `https://github.com/BiliUniverse/Global/releases/latest/download/BiliBili.Global.sgmodule` | `.sgmodule` preferred over the SR `.srmodule` |
| BiliBili.Redirect.plugin | `https://github.com/BiliUniverse/Redirect/releases/latest/download/BiliBili.Redirect.sgmodule` | `force-http-engine-hosts` (PCDN ports) runs on Surge |
| Disney+.plugin | `https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/sgmodule/Disney%2B.sgmodule` | Surge script params apply natively |
| Netflix.beta.plugin | `https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/sgmodule/Netflix.beta.sgmodule` | official same-source |
| Sub-Store Loon.plugin | `https://raw.githubusercontent.com/sub-store-org/Sub-Store/master/config/Surge-Noability.sgmodule` | Surge flavor from the same repo |
| MediaCheck.lpx | **restored as a Surge Panel** — the module's upstream (Keywos) ships a Surge build: `https://kelee.one/Tool/Surge/Module/MediaCheck_Streaming-Media-Detection.sgmodule` | Loon's MediaCheck was a **panel**; Shadowrocket dropped it (no panel concept), but Surge has Panels, so the diagnostic surface is restored. The host is Cloudflare-gated, so it cannot be checked with curl — open the URL in a browser / install it in-app to verify. Any maintained streaming-unlock Panel `.sgmodule` works if you prefer another. |

All 21 Loon plugins map onto Surge: the 20 that the Shadowrocket port carried keep their `.sgmodule`
(three swap the SR `.srmodule` for the Surge-native `.sgmodule`), and MediaCheck — dropped on
Shadowrocket for lack of a panel concept — is **restored as a Surge Panel**.

## No known degradations

Every directive the Shadowrocket port lists as silently ignored is supported on Surge. Keep the
modules upstream-maintained; do not vendor or patch them.
