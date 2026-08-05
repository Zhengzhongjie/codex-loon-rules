#!/usr/bin/env python3
"""Generate the public Shadowrocket config skeletons from a committed sanitized spec.

The skeleton is a full-shape `.conf` with placeholders (``{{NAME}}``) for every private value —
proxy nodes, MITM certificate, and passphrase. iCloud assembly fills the placeholders to produce
the real private `.conf`. Rule-list bindings are derived from the shared RULESETS catalogue so the
Shadowrocket [Rule] section can never drift from the generated rule trees. Modules are NOT part of
a Shadowrocket .conf (they are installed in-app); see docs/shadowrocket-modules.md.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from build_loon_rules import RULESETS

SR_RAW_BASE = "https://raw.githubusercontent.com/Zhengzhongjie/loon-rules-personal/main/rules/shadowrocket/generated"
TEST_URL = "http://cp.cloudflare.com/generate_204"

# Region order used inside every service group's member list (from the Loon global group).
REGIONS = ["美国节点", "香港节点", "澳门节点", "台湾节点", "日本节点", "韩国节点", "狮城节点", "英国节点", "其他节点"]

# Claude rejects unsupported or inconsistent region signals. Keep it on one explicitly supported
# region and exclude DIRECT, Hong Kong, Macao, unknown regions, and multi-region chain selectors.
CLAUDE_REGIONS = ["美国节点", "狮城节点", "日本节点", "台湾节点", "韩国节点", "英国节点"]

# Region latency groups: node members are private, so each carries a {{…}} placeholder plus the
# non-secret url-test parameters carried over from the Loon config.
REGION_GROUPS = [
    ("美国节点", "url-test", "{{US_NODES}}", "interval=600"),
    ("香港节点", "url-test", "{{HK_NODES}}", "interval=60,tolerance=50"),
    ("澳门节点", "url-test", "{{MO_NODES}}", "interval=60,tolerance=50"),
    ("台湾节点", "url-test", "{{TW_NODES}}", "interval=60,tolerance=50"),
    ("日本节点", "url-test", "{{JP_NODES}}", "interval=600"),
    ("韩国节点", "url-test", "{{KR_NODES}}", "interval=60,tolerance=50"),
    ("狮城节点", "url-test", "{{SG_NODES}}", "interval=60,tolerance=50"),
    ("英国节点", "url-test", "{{UK_NODES}}", "interval=60,tolerance=50"),
    ("其他节点", "select", "{{OTHER_NODES}}", ""),
]

# Chain groups (Loon [Proxy Chain]); the chained nodes and their underlying-proxy wiring are private.
CHAIN_GROUPS = [
    ("链式代理节点", "select", ["{{CHAIN_NODES}}"]),
    ("链式代理链路", "select", ["DIRECT", "{{CHAIN_LINK_NODES}}"]),
]

# Service groups that route through the chain first (proxy-leaning), then DIRECT, then the regions.
PROXY_FIRST = [
    "Adobe", "AI", "PayPal", "Binance", "金融加密", "Amazon", "X", "开发协作", "海外社交资讯",
    "YouTube", "Google", "GitHub", "境外流媒体", "Microsoft", "Meta", "Telegram", "TikTok",
]
# China-friendly services that prefer DIRECT first.
DIRECT_FIRST = ["Seetong", "TradingView", "Apple", "Bilibili", "RedNote", "抖音", "Weibo"]


def service_group(name: str, direct_first: bool) -> str:
    lead = ["DIRECT", "链式代理链路"] if direct_first else ["链式代理链路", "DIRECT"]
    members = lead + REGIONS
    return f"{name} = select,{','.join(members)},url={TEST_URL}"


@dataclass(frozen=True)
class Device:
    name: str                       # output basename: <name>.conf
    proxies: tuple[str, ...]        # [Proxy] placeholder lines specific to this device
    mitm_hostname: str              # [MITM] hostname value (placeholder or empty)


DEVICES = (
    # iPhone/iPad also carries the WireGuard home-access node and a MITM hostname list.
    Device(
        "iphone",
        proxies=("{{PROXY_NODES}}", "Home-Orca-WG = {{HOME_WG_NODE}}"),
        mitm_hostname="{{MITM_HOSTNAMES}}",
    ),
    # Mac mini is the home-access target, so it has no home tunnel and no MITM hostname list.
    Device(
        "mac",
        proxies=("{{PROXY_NODES}}",),
        mitm_hostname="",
    ),
)


def general_section() -> list[str]:
    # Mapped from the Loon [General] block; SR-unsupported keys (wifi-access, sni-sniffing,
    # resource-parser, geoip-url, …) are dropped, test URLs move to per-group url= params.
    return [
        "[General]",
        "bypass-system = true",
        "ipv6 = false",
        "prefer-ipv6 = false",
        "udp-policy-not-supported-behaviour = REJECT",
        "dns-server = system",
        "skip-proxy = 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,localhost,*.local,e.crashlytics.com",
        "bypass-tun = 10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.0.0.0/24,192.0.2.0/24,192.88.99.0/24,192.168.0.0/16,198.51.100.0/24,203.0.113.0/24,224.0.0.0/4,255.255.255.255/32",
    ]


# Domains whose DNS is geo-steered and whose default (system) resolver returns a dead sinkhole
# instead of a working edge — pin them to an encrypted resolver so they reach the reachable line.
# OKX/OKLink/OKEX: the system resolver (Tailscale MagicDNS upstream) answers www.okx.com with a
# link-local 169.254.0.2 black hole (the AWS-China okpool line); Cloudflare DoH returns the working
# global Cloudflare line. DoH (not plain UDP) so a hostile network can't spoof the answer back.
DOH_PINNED_HOSTS: tuple[str, ...] = (
    "okx.com",
    "oklink.com",
    "okex.com",
)
CLEAN_DOH = "https://1.1.1.1/dns-query"


def host_section() -> list[str]:
    # Scoped narrowly (apex + subdomains of a few finance hosts) so the tailnet's MagicDNS stays the
    # default resolver for everything else — including home-access tailnet machine names.
    lines = ["[Host]"]
    for domain in DOH_PINNED_HOSTS:
        lines.append(f"{domain} = server:{CLEAN_DOH}")
        lines.append(f"*.{domain} = server:{CLEAN_DOH}")
    return lines


def proxy_group_section() -> list[str]:
    lines = ["[Proxy Group]"]
    lines.append(f"全局代理 = select,链式代理链路,{','.join(REGIONS)},DIRECT,url={TEST_URL}")
    for name, typ, members in CHAIN_GROUPS:
        lines.append(f"{name} = {typ},{','.join(members)}")
    lines.append("广告分流 = select,REJECT,DIRECT")
    lines.append(f"大陆流量 = select,DIRECT,链式代理链路,REJECT,{','.join(REGIONS)},url={TEST_URL}")
    lines.append(f"Claude = select,{','.join(CLAUDE_REGIONS)},url={TEST_URL}")
    for name in PROXY_FIRST:
        lines.append(service_group(name, direct_first=False))
    for name in DIRECT_FIRST:
        lines.append(service_group(name, direct_first=True))
    for name, typ, nodes, params in REGION_GROUPS:
        parts = [nodes] if typ == "select" else [nodes, f"url={TEST_URL}"]
        if params:
            parts.append(params)
        lines.append(f"{name} = {typ},{','.join(parts)}")
    return lines


def rule_section() -> list[str]:
    # One RULE-SET line per generated Shadowrocket rule tree, in RULESETS priority order, then FINAL.
    lines = ["[Rule]"]
    for rs in RULESETS:
        lines.append(f"RULE-SET,{SR_RAW_BASE}/{rs.file},{rs.policy}")
    lines.append("FINAL,全局代理")
    return lines


def proxy_section(device: Device) -> list[str]:
    return ["[Proxy]", *device.proxies]


def mitm_section(device: Device) -> list[str]:
    lines = ["[MITM]", "enable = true"]
    if device.mitm_hostname:
        lines.append(f"hostname = {device.mitm_hostname}")
    lines.append("ca-passphrase = {{CA_PASSPHRASE}}")
    lines.append("ca-p12 = {{CA_P12}}")
    return lines


def render_config(device: Device) -> str:
    header = [
        f"# Shadowrocket config skeleton ({device.name}) — generated by tools/build_shadowrocket_config.py.",
        "# Public skeleton only: every private value is a {{PLACEHOLDER}} filled during iCloud assembly.",
        "# Modules are installed separately in-app (Config > Modules); see docs/shadowrocket-modules.md.",
    ]
    blocks = [
        header,
        general_section(),
        host_section(),
        proxy_section(device),
        proxy_group_section(),
        rule_section(),
        mitm_section(device),
    ]
    return "\n".join("\n".join(block) for block in blocks) + "\n"


def build(configs_dir: Path) -> int:
    configs_dir.mkdir(parents=True, exist_ok=True)
    for device in DEVICES:
        (configs_dir / f"{device.name}.conf").write_text(render_config(device))
    print(f"wrote {len(DEVICES)} config skeletons to {configs_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configs-dir", type=Path, default=Path("configs/shadowrocket"))
    args = parser.parse_args()
    return build(args.configs_dir)


if __name__ == "__main__":
    raise SystemExit(main())
