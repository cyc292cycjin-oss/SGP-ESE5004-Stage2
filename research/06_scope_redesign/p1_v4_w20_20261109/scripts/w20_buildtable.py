"""V4 W20: build summary of the 17 coalition networks from their COALITION_RECEIPT.json files (tables/W20_COALITION_BUILD.csv, markdown snippets)."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

nets = Path(sys.argv[1]); out_csv = Path(sys.argv[2]); out_md = Path(sys.argv[3])
sys.path.insert(0, "/home/jin/wt_v4_w20/scripts_project")
from v4_coalition import COALITION_ORDER  # noqa: E402

rows, md = [], []
for name in COALITION_ORDER:
    R = json.loads((nets / f"{name}_56_COALITION_RECEIPT.json").read_text()); L = R["ledger"]
    rb = L["removed_by_rule"]; ca = L["components_after"]
    bcar = Counter()
    for k, v in L["boundary_by_carrier"].items():
        bcar[k.split("|", 1)[1]] += v
    rows.append(dict(coalition=name, members=" ".join(L["members"]), network_sha256=R["output"]["sha256"], bytes=R["output"]["bytes"],
                     buses=ca.get("Bus"), lines=ca.get("Line"), links=ca.get("Link"), generators=ca.get("Generator"), stores=ca.get("Store"), storage_units=ca.get("StorageUnit"), loads=ca.get("Load"),
                     R1_buses=rb.get("R1_bus_country", {}).get("Bus", 0), R1_components=sum(v for k, v in rb.get("R1_bus_country", {}).items() if k != "Bus"),
                     R2_boundary=sum(rb.get("R2_boundary", {}).values()), R3_bunker=sum(rb.get("R3_bunker", {}).values()),
                     R5_dangling_buses=len(L["dangling_buses_removed"]), R5_carriers=len(L["carriers_removed"]),
                     boundary_by_carrier="; ".join(f"{k} {v}" for k, v in sorted(bcar.items())),
                     retained_cross_border=len(L["retained_cross_border"]), retained_stock=len(L["retained_cross_border_stock"]),
                     retained_trade_links="; ".join(f"{k} {v}" for k, v in sorted(L["retained_cross_border_trade_links"].items())),
                     transit_via_non_member=len(L["transit_via_non_member"]), dead_end_kept=len(L["dead_end_member_components_kept"]),
                     dead_end_fixed_cost_eur=L["dead_end_fixed_cost_constant_eur"], xb_fom_boundary_eur=L["existing_cross_border_fom_boundary_eur"], d8_addback_eur=L["d8_addback_eur"],
                     existing_fom_after_eur=(L["meta"].get("existing_annual_fixed_om_eur") or {}).get("after"), demand_removed_R1_TWh=L["demand_removed_mwh"]["R1_mwh"] / 1e6,
                     demand_removed_R3_TWh=L["demand_removed_mwh"]["R3_mwh"] / 1e6, hooks=" ".join(L["meta"]["required_constraint_hooks"])))
    st = L["retained_cross_border_stock"]
    md.append(f"#### {name}（{' '.join(L['members'])}）：保留的存量跨境设施 {len(st)} 项")
    by = {}
    for s in st:
        by.setdefault(("|".join(s["countries"]), s["carrier"]), []).append(f"`{s['component']}` {s['existing_mw']:.1f} MW")
    for (p, c), v in sorted(by.items()):
        md.append(f"- {p} {c}（{len(v)}）：" + "；".join(v))
    if L["transit_via_non_member"]:
        md.append(f"- 经非成员国过境而按端口规则保留的链路 {len(L['transit_via_non_member'])} 条：" + "、".join(sorted({f"{t['carrier']}（经 {t['via_country']}）" for t in L["transit_via_non_member"]})))
    md.append("")
with open(out_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n"); w.writeheader()
    for r in rows:
        w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})
out_md.write_text("\n".join(md) + "\n")
for r in rows:
    print(r["coalition"], r["buses"], r["links"], r["R2_boundary"], r["retained_stock"], r["boundary_by_carrier"])
