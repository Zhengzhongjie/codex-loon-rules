# Shadowrocket modules

A Shadowrocket `.conf` **cannot embed module URLs** — there is no `[Module]`/`[Plugin]` section, no
`module = <url>` key, and no module-subscription directive inside the config (confirmed across the
Repcz/Tool, johnshall, Hackl0us, and official `Shadowrocket/config` configs, and the LOWERTOP
manual). Modules are a separate, app-managed file type (`.sgmodule` / `.module` / `.srmodule`,
Surge-compatible). So this repo emits the config skeleton and this module list as **independent
artifacts**: the `.conf` handles routing, and you install the modules separately in-app.

Install each module in Shadowrocket: **Config → Modules → ➕ → paste URL → Download** (iCloud then
syncs the installed module list across devices). Per [ADR-0003](adr/0003-modules-referenced-from-upstream.md),
these are referenced from upstream, not vendored or converted; prefer a maintainer's
Shadowrocket-native `.srmodule` where one exists.

## Module map (Loon plugin → Shadowrocket module)

| Loon plugin | Shadowrocket module URL | Notes |
| --- | --- | --- |
| wloc.lpx | `https://raw.githubusercontent.com/Yu9191/wloc/refs/heads/main/modules/wloc.module` | SR-native `.module`; coordinates hardcoded (edit or use the project's picker) |
| boxjs.rewrite.loon.plugin | `https://raw.githubusercontent.com/chavyleung/scripts/master/box/rewrite/boxjs.rewrite.surge.sgmodule` | `force-http-engine-hosts` is Surge-only, ignored by SR (harmless) |
| General.plugin | `https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/sgmodule/General.sgmodule` | `always-real-ip` needs SR Fake-IP DNS mode |
| DNS.plugin | `https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/sgmodule/DNS.sgmodule` | Some `[General]` keys are Surge-5-only; SR ignores them |
| HTTPDNS.Block.plugin | `https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/sgmodule/HTTPDNS.Block.sgmodule` | `force-http-engine-hosts` best-effort on recent SR |
| AdvertisingLite.plugin | `https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Shadowrocket/AdvertisingLite/AdvertisingLite.sgmodule` | SR-specific build (rewrite/Shadowrocket/ path) |
| YouTube_remove_ads.lpx | `https://raw.githubusercontent.com/Maasea/sgmodule/master/YouTube.Enhance.sgmodule` | `[Map Local]` may be limited in SR |
| DualSubs.YouTube.plugin | `https://github.com/DualSubs/YouTube/releases/latest/download/DualSubs.YouTube.sgmodule` | `engine=webview` scripts ignored; SR runs its own JS core |
| iRingo.LocationService.plugin | `https://github.com/NSRingo/LocationServices/releases/latest/download/iRingo.LocationService.sgmodule` | official same-release |
| iRingo.Maps.plugin | `https://github.com/NSRingo/Maps/releases/latest/download/iRingo.Maps.sgmodule` | `engine=webview` ignored |
| iRingo.TV.plugin | `https://github.com/NSRingo/TV/releases/latest/download/iRingo.TV.srmodule` | SR-native `.srmodule` preferred |
| iRingo.WeatherKit.Workers.plugin | `https://github.com/NSRingo/WeatherKit/raw/main/modules/iRingo.WeatherKit.Workers.sgmodule` | Workers variant (main branch) |
| iRingo.News.plugin | `https://github.com/NSRingo/News/releases/latest/download/iRingo.News.sgmodule` | uses `{{{Proxy}}}` module argument |
| BiliBili.ADBlock.plugin | `https://github.com/BiliUniverse/ADBlock/releases/latest/download/BiliBili.ADBlock.sgmodule` | `http-response-jq` body rewrite is Surge-5-only |
| BiliBili.Enhanced.plugin | `https://github.com/BiliUniverse/Enhanced/releases/latest/download/BiliBili.Enhanced.srmodule` | SR-native `.srmodule` preferred (avoids `#!arguments`) |
| BiliBili.Global.plugin | `https://github.com/BiliUniverse/Global/releases/latest/download/BiliBili.Global.srmodule` | SR-native `.srmodule` preferred |
| BiliBili.Redirect.plugin | `https://github.com/BiliUniverse/Redirect/releases/latest/download/BiliBili.Redirect.sgmodule` | `force-http-engine-hosts` (PCDN ports) ignored by SR |
| Disney+.plugin | `https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/sgmodule/Disney%2B.sgmodule` | Surge script params ignored (harmless) |
| Netflix.beta.plugin | `https://raw.githubusercontent.com/VirgilClyne/GetSomeFries/main/sgmodule/Netflix.beta.sgmodule` | official same-source |
| Sub-Store Loon.plugin | `https://raw.githubusercontent.com/sub-store-org/Sub-Store/master/config/Surge-Noability.sgmodule` | Surge flavor from the same repo |
| MediaCheck.lpx | — **dropped** | Loon panel; Shadowrocket has no panel concept, so there is no equivalent |

20 of the 21 Loon plugins have an upstream Shadowrocket module. MediaCheck is a Loon **panel** (a
diagnostic surface Shadowrocket does not have) and is intentionally dropped rather than rewritten.

## Known degradations

Some modules carry Surge-only directives that Shadowrocket silently ignores (feature loss, not
breakage): `engine=webview` scripts, `http-response-jq` / `[Body Rewrite]`, `[Map Local]`, and
`force-http-engine-hosts`. These are documented, not patched — the modules stay upstream-maintained.
