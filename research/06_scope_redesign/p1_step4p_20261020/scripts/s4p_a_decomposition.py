"""S4P analysis A: per-country channel decomposition of (disconnected - integrated) and (NZE - integrated) from the
three COUNTRY_COST_LEDGER_DETAIL.csv exports (S4N pilot integrated, S4O-6 disconnected, S4O-6 integrated NZE).
Read-only. Outputs: A_CHANNEL_LONG.csv (entity x subject x carrier x run), A_CHANNEL_BY_COUNTRY.csv (channel groups),
A_CHANNEL_DECOMPOSITION.md (per-entity tables in the format of the reviewer's VN decomposition), A_SUMMARY.json."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4p_paths import BN_, ENTITIES, OUT, dump_json, ledger_detail, ledger_total, md_table  # noqa: E402

CHANNEL = {
    "capex_new": "投资（新建）",
    "fom_existing": "存量固定运维",
    "variable_cost": "可变成本（燃料、运维）",
    "network_trade_AC": "网络贸易：交流电",
    "network_trade_DC": "网络贸易：直流电",
    "network_trade_H2 pipeline": "网络贸易：氢管道",
    "network_trade_gas pipeline": "网络贸易：气管道",
    "network_trade_CO2 pipeline": "网络贸易：CO2 管道",
    "xb_share_congestion_rent": "拥塞租分摊（五五）",
    "xb_share_infrastructure_cost": "跨境设施成本分摊（五五）",
    "liquid_pool_oil": "液体池：油",
    "liquid_pool_oil non-fossil": "液体池：非化石油品",
    "liquid_pool_methanol": "液体池：甲醇",
    "liquid_pool_ammonia": "液体池：氨",
    "co2_storage_service": "CO2 封存服务结算",
    "co2_ship_freight": "CO2 船运运费",
    "co2_transit_freight": "CO2 过境（老挝）",
    "co2_transit_rail_freight": "CO2 过境铁路",
    "co2_transit_ship_freight": "CO2 过境船运",
}
DIRECT = {"capex_new", "fom_existing", "variable_cost"}
SETTLEMENT_TRADE = {k for k in CHANNEL if k.startswith("network_trade")}
XB = {"xb_share_congestion_rent", "xb_share_infrastructure_cost"}
POOLS = {k for k in CHANNEL if k.startswith("liquid_pool")}
CO2 = {k for k in CHANNEL if k.startswith("co2_")}

RUNS = ["integrated", "disconnected", "integrated_nze"]


def main():
    L = pd.concat([ledger_detail(r) for r in RUNS], ignore_index=True)
    wide = L.pivot_table(index=["entity", "subject", "carrier"], columns="run", values="eur", aggfunc="sum").fillna(0.0)
    for r in RUNS:
        if r not in wide:
            wide[r] = 0.0
    wide = wide[RUNS]
    wide["dis_minus_int"] = wide["disconnected"] - wide["integrated"]
    wide["nze_minus_int"] = wide["integrated_nze"] - wide["integrated"]
    wide = wide.reset_index()
    wide.to_csv(OUT / "A_CHANNEL_LONG.csv", index=False, float_format="%.6f")

    # ---- totals and identity check against COUNTRY_COST_LEDGER.csv
    tot = {r: ledger_total(r) for r in RUNS}
    check = []
    for e in ENTITIES:
        row = {"entity": e}
        for r in RUNS:
            s_detail = float(wide.loc[wide.entity == e, r].sum())
            s_total = float(tot[r].at[e, "total"]) if e in tot[r].index else np.nan
            row[f"{r}_detail"] = s_detail
            row[f"{r}_ledger_total"] = s_total
            row[f"{r}_absdiff"] = abs(s_detail - s_total)
        check.append(row)
    check = pd.DataFrame(check)
    b6_detail = float(wide.loc[wide.entity.isin(ENTITIES), "dis_minus_int"].sum())
    nze_detail = float(wide.loc[wide.entity.isin(ENTITIES), "nze_minus_int"].sum())
    obj = {r: float(tot[r]["total"].sum()) for r in RUNS}

    # ---- channel groups
    wide["channel"] = wide.subject.map(CHANNEL).fillna(wide.subject)
    g = wide.groupby(["entity", "subject"])[RUNS + ["dis_minus_int", "nze_minus_int"]].sum().reset_index()
    g["channel"] = g.subject.map(CHANNEL).fillna(g.subject)
    g.to_csv(OUT / "A_CHANNEL_BY_COUNTRY.csv", index=False, float_format="%.6f")

    # ---- markdown
    md = ["# S4P 分析 A：分国差额的通道分解（bn EUR；只读，来自三份账本明细）", "",
          "- 一体化 = S4N 试点（optimal）；不互联、NZE = S4O-6 整批（SUBOPTIMAL，C1 通过）。",
          f"- 目标函数（账本合计 = 11 国 + 燃料舱 + 共享池）：一体化 {obj['integrated']/BN_:.3f}，不互联 {obj['disconnected']/BN_:.3f}，NZE {obj['integrated_nze']/BN_:.3f} bn。",
          f"- 明细加总 B6（不互联 − 一体化）= {b6_detail/BN_:.4f} bn；NZE − 一体化 = {nze_detail/BN_:.4f} bn。",
          "- 正值 = 该国支出；负值 = 收入（结算）或节省。差额列：不互联 − 一体化、NZE − 一体化。", ""]
    md.append("## 加总核对（明细 vs 账本总表，EUR）")
    md.append(md_table(check[["entity"] + [f"{r}_absdiff" for r in RUNS]], "{:,.2f}"))
    md.append("")
    md.append("## 各实体差额总览（bn EUR）")
    ov = g.groupby("entity")[RUNS + ["dis_minus_int", "nze_minus_int"]].sum().reindex(ENTITIES) / BN_
    ov = ov.reset_index()
    md.append(md_table(ov))
    md.append("")

    summary = {"objective_bn": {k: v / BN_ for k, v in obj.items()}, "b6_detail_bn": b6_detail / BN_, "nze_minus_int_detail_bn": nze_detail / BN_,
               "identity_max_absdiff_eur": float(check[[f"{r}_absdiff" for r in RUNS]].max().max()), "entities": {}}
    for e in ENTITIES:
        sub = g[g.entity == e].copy()
        sub = sub.sort_values("dis_minus_int", key=lambda s: s.abs(), ascending=False)
        t = sub[["channel", "integrated", "disconnected", "integrated_nze", "dis_minus_int", "nze_minus_int"]].copy()
        for c in RUNS + ["dis_minus_int", "nze_minus_int"]:
            t[c] = t[c] / BN_
        t.columns = ["通道", "一体化", "不互联", "NZE", "不互联−一体化", "NZE−一体化"]
        md.append(f"## {e}")
        md.append(f"合计（bn）：一体化 {ov.loc[ov.entity==e,'integrated'].iat[0]:.3f}，不互联 {ov.loc[ov.entity==e,'disconnected'].iat[0]:.3f}，NZE {ov.loc[ov.entity==e,'integrated_nze'].iat[0]:.3f}；差额 不互联−一体化 **{ov.loc[ov.entity==e,'dis_minus_int'].iat[0]:.3f}**，NZE−一体化 **{ov.loc[ov.entity==e,'nze_minus_int'].iat[0]:.3f}**")
        md.append("")
        md.append(md_table(t))
        md.append("")
        # top carriers inside the direct channels, by |dis - int| and |nze - int|
        det = wide[(wide.entity == e)].copy()
        det["abs1"] = det.dis_minus_int.abs(); det["abs2"] = det.nze_minus_int.abs()
        top1 = det.sort_values("abs1", ascending=False).head(18)
        top2 = det.sort_values("abs2", ascending=False).head(12)
        for title, top in (("明细前 18 项（按 |不互联−一体化|）", top1), ("明细前 12 项（按 |NZE−一体化|）", top2)):
            tt = top[["subject", "carrier", "integrated", "disconnected", "integrated_nze", "dis_minus_int", "nze_minus_int"]].copy()
            for c in RUNS + ["dis_minus_int", "nze_minus_int"]:
                tt[c] = tt[c] / BN_
            tt.columns = ["科目", "载体", "一体化", "不互联", "NZE", "不互联−一体化", "NZE−一体化"]
            md.append(f"### {e}：{title}")
            md.append(md_table(tt))
            md.append("")
        summary["entities"][e] = {
            "total_bn": {r: float(ov.loc[ov.entity == e, r].iat[0]) for r in RUNS},
            "dis_minus_int_bn": float(ov.loc[ov.entity == e, "dis_minus_int"].iat[0]),
            "nze_minus_int_bn": float(ov.loc[ov.entity == e, "nze_minus_int"].iat[0]),
            "channels_bn": {row.subject: {"integrated": row.integrated / BN_, "disconnected": row.disconnected / BN_, "integrated_nze": row.integrated_nze / BN_,
                                          "dis_minus_int": row.dis_minus_int / BN_, "nze_minus_int": row.nze_minus_int / BN_} for row in sub.itertuples()},
            "top_items_dis_minus_int_bn": [{"subject": r.subject, "carrier": r.carrier, "integrated": r.integrated / BN_, "disconnected": r.disconnected / BN_,
                                            "dis_minus_int": r.dis_minus_int / BN_} for r in top1.itertuples()],
            "top_items_nze_minus_int_bn": [{"subject": r.subject, "carrier": r.carrier, "integrated": r.integrated / BN_, "integrated_nze": r.integrated_nze / BN_,
                                            "nze_minus_int": r.nze_minus_int / BN_} for r in top2.itertuples()],
        }
    # aggregated channel classes per country (direct / trade / xb / pools / co2)
    cls = {}
    for s in g.subject.unique():
        cls[s] = "direct" if s in DIRECT else "network_trade" if s in SETTLEMENT_TRADE else "xb_share" if s in XB else "liquid_pool" if s in POOLS else "co2" if s in CO2 else "other"
    g["cls"] = g.subject.map(cls)
    cl = g.groupby(["entity", "cls"])[["dis_minus_int", "nze_minus_int"]].sum().reset_index()
    piv = cl.pivot_table(index="entity", columns="cls", values="dis_minus_int").reindex(ENTITIES).fillna(0.0) / BN_
    piv2 = cl.pivot_table(index="entity", columns="cls", values="nze_minus_int").reindex(ENTITIES).fillna(0.0) / BN_
    md.insert(12, "## 按五大类的差额（bn EUR）：direct = 投资 + 存量固定运维 + 可变成本；network_trade = 节点电价结算的网络贸易；xb_share = 走廊拥塞租与设施分摊；liquid_pool = 区域液体池结算；co2 = CO2 服务与运费\n\n### 不互联 − 一体化\n" + md_table(piv.reset_index()) + "\n\n### NZE − 一体化\n" + md_table(piv2.reset_index()) + "\n")
    summary["class_dis_minus_int_bn"] = piv.to_dict(orient="index")
    summary["class_nze_minus_int_bn"] = piv2.to_dict(orient="index")
    (OUT / "A_CHANNEL_DECOMPOSITION.md").write_text("\n".join(md), encoding="utf-8")
    dump_json(summary, OUT / "A_SUMMARY.json")
    print("B6 detail bn", b6_detail / BN_, "NZE-int bn", nze_detail / BN_, "max identity absdiff EUR", summary["identity_max_absdiff_eur"])
    print(piv.round(3))


if __name__ == "__main__":
    main()
