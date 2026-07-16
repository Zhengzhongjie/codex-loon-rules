# Loon routing order

This config keeps two layers:

1. Dedicated company/service rules first, so sensitive services can use their own policy group.
2. Consolidated category rules later, so uncovered domains still land in the right broad bucket.

## Recommended policy groups

- `广告分流`: `REJECT`, then `DIRECT`.
- `Seetong`: `DIRECT` first for camera latency and LAN-like behavior, then proxy choices.
- `Adobe`: `DIRECT` first unless Adobe account or regional access requires proxy.
- `Apple`: `DIRECT` first, then proxy choices.
- `Claude`: use one stable supported-region group only (`美国节点`, `狮城节点`, `日本节点`, `台湾节点`, `韩国节点`, or `英国节点`). Do not offer `DIRECT`, Hong Kong, Macao, unknown-region, or multi-region chain choices.
- `AI`, `Google`, `YouTube`, `Telegram`, `TikTok`, `Microsoft`, `Meta`, `GitHub`, `金融加密`, `Amazon`, `开发协作`, `海外社交资讯`, `境外流媒体`: proxy first, then `DIRECT`.
- `RedNote`, `抖音`, `Bilibili`, `Weibo`: `DIRECT` first, then proxy choices.

## Rule priority

Use this order in `[Remote Rule]`:

1. `Ads-Reject`
2. `LAN-Direct`
3. `AccountSafety-DIRECT`
4. `Mainland-Services-Direct`
5. `Seetong-Local`
6. `PayPal-Stable`
7. `FinanceCrypto-Stable`
8. `Adobe`
9. `Claude`
10. `AI`
11. `Apple`
12. `RedNote`
13. `Weibo`
14. `TikTok`
15. `Douyin-ByteDance`
16. `Bilibili`
17. `Telegram`
18. `Microsoft`
19. `Meta`
20. `YouTube`
21. `Google`
22. `GitHub`
23. `Developer-Collab`
24. `Global-Social-Info`
25. `Streaming`
26. `Amazon`
27. `Talkatone`
28. `ChinaASN-Direct`
29. `FINAL,全局代理`

## Conflict decisions

- Service-specific rules outrank category catchalls.
- YouTube outranks Google.
- TikTok outranks ByteDance.
- PrimeVideo outranks Amazon.
- Telegram domain rules outrank ASN.Telegram.
- ASN.China stays late and uses hard `DIRECT` so it does not steal explicitly routed global services or expose mainland catchall traffic to manual proxy selection.
- Account-sensitive direct rules outrank ad, app-enhancement, and broad category rules.
- Finance/crypto rules should use a manually selected stable route, not frequent automatic region switching.
- The original upstream subscriptions are build inputs only. The Loon config should subscribe to generated repository rules to avoid duplicate and shadowed entries.

## Test command

```sh
python3 tools/validate_loon_config.py "/Users/alessiozheng/Library/Mobile Documents/iCloud~com~ruikq~decar/Documents/Configs/20260503-loon.lcf"
python3 tools/audit_public_artifacts.py .
```
