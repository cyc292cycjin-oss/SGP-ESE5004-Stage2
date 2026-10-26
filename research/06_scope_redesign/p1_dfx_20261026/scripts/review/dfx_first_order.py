"""DFX F5.4: first-order (envelope-theorem) prediction of the v2 - v1 demand change with the third-batch 365x24h duals (DMD dmd_d5_duals.py method;
read-only, no solve). Registered in RUN_PLAN_DFX.md BEFORE any v2 solve.

  * load values of R1 (integrated) / R2 (disconnected) and R3 / R4 (optimal 1e-6 robustness): MV = sum_t w_t x lambda_bus(t) x p_set(t); average price per
    (country, account, carrier) = MV / annual MWh;
  * dD = v2 - v1 annual MWh per (country, account, carrier) from the DFX D1 tables (DEMAND_BY_COUNTRY_SECTOR_CARRIER_v1 / v2.csv; network loads);
  * dC_int = sum lambda_int x dD, dC_dis = sum lambda_dis x dD, dB6 = dC_dis - dC_int; per country: Owen-share change lambda_int x dD_i, stand-alone change
    lambda_dis x dD_i, benefit change = difference; a load class absent in v1 (e.g. MY ammonia) takes the (country, carrier) average price, then the
    carrier average of all countries (regional ammonia bus: the same price everywhere);
  * decomposition by change class (F1 transport / buildings / agriculture / industry multiplier, F2 ammonia / NEU gas, F3 HVC oil, NEU other).
This is a linear extrapolation of a large change (INFERENCE): directions and orders of magnitude only.
Output: evidence/DFX_FIRST_ORDER.json, DFX_FIRST_ORDER.md
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

EXP = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10_20261022/cloud_results/20261023T174135Z_halted/full/unpacked/export")
RUNS = {"R1": EXP / "R1/integrated_BATCH3_365X24H_solved.nc", "R2": EXP / "R2/disconnected_BATCH3_365X24H_solved.nc",
        "R3": EXP / "R3/integrated_BATCH3_365X24H_solved.nc", "R4": EXP / "R4/disconnected_BATCH3_365X24H_solved.nc"}
PAIRS = {"main (R1 / R2)": ("R1", "R2"), "robustness (R3 / R4, optimal 1e-6)": ("R3", "R4")}
OUT = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026")
C11 = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
EUR_TO_USD = 1.139954
B6_REF_BN = 11.300   # third batch R2 - R1 (bn EUR), stage report


def load_values(path: Path):
    n = pypsa.Network(str(path))
    w = n.snapshot_weightings.objective; lam = n.buses_t.marginal_price; p = n.get_switchable_as_dense("Load", "p_set")
    L = n.loads[["bus", "carrier", "account", "country"]].copy()
    L["country"] = L.country.fillna("").astype(str); L["account"] = L.account.fillna("").astype(str)
    L["mwh"] = p.mul(n.snapshot_weightings.generators, axis=0).sum().reindex(L.index).values
    L["mv_eur"] = (p * lam[L.bus].values).mul(w, axis=0).sum().reindex(L.index).values
    return L, float(n.objective)


def change_class(sector, account, carrier):
    if sector == "NonEnergyUse":
        return "F2 NEU gas (ammonia feedstock deduction)" if carrier == "gas feedstock" else ("F3 NEU oil (HVC scope) + F1 multiplier" if carrier == "oil feedstock" else "F1 NEU multiplier (coal)")
    if account == "IndustryAmmonia":
        return "F2 ammonia (production rule)"
    if sector == "Industry":
        return "F1 industry multiplier (RAS)"
    if sector == "Transport":
        return "F1 transport anchor (RAS)"
    if sector in ("Residential", "Commercial"):
        return "F1 buildings anchors (RAS)"
    if sector == "AgricultureOthers":
        return "F1 agriculture anchor (RAS)"
    return "other"


def main():
    vals, obj = {}, {}
    for rid, p in RUNS.items():
        vals[rid], obj[rid] = load_values(p)
    key = ["country", "account", "carrier"]
    price = {}
    for rid, L in vals.items():
        g = L.groupby(key)[["mwh", "mv_eur"]].sum(); price[rid] = (g.mv_eur / g.mwh.replace(0, np.nan)).rename(rid)
    P = pd.concat(price.values(), axis=1); P["mwh"] = vals["R1"].groupby(key).mwh.sum()
    Pr = P.reset_index()
    d1 = pd.read_csv(OUT / "DEMAND_BY_COUNTRY_SECTOR_CARRIER_v1.csv", keep_default_na=False); d2 = pd.read_csv(OUT / "DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv", keep_default_na=False)
    k2 = ["country", "sector", "network_account", "carrier"]
    a = d1[d1.network_account != "memo"].groupby(k2, as_index=False).twh.sum().rename(columns={"twh": "v1"}); b = d2[d2.network_account != "memo"].groupby(k2, as_index=False).twh.sum().rename(columns={"twh": "v2"})
    m = a.merge(b, on=k2, how="outer").fillna(0.0); m["dD_mwh"] = (m.v2 - m.v1) * 1e6
    m = m[m.dD_mwh.abs() > 1e-6].copy(); m["cls"] = [change_class(s, acc, car) for s, acc, car in zip(m.sector, m.network_account, m.carrier)]
    fallback_log = []

    def pr(rid, c, acc, car):
        v = P[rid].get((c, acc, car), np.nan)
        if np.isnan(v):
            sub = Pr[(Pr.country == c) & (Pr.carrier == car)]
            if len(sub) and sub.mwh.sum() > 0 and sub[rid].notna().any():
                v = float(np.average(sub[rid].fillna(0), weights=sub.mwh)); fallback_log.append((rid, c, acc, car, "country x carrier average"))
            else:
                sub = Pr[Pr.carrier == car]
                if len(sub) and sub.mwh.sum() > 0 and sub[rid].notna().any():
                    v = float(np.average(sub[rid].fillna(0), weights=sub.mwh)); fallback_log.append((rid, c, acc, car, "carrier average (all countries)"))
        return v
    res = dict(objective_eur=obj, b6_reference_bn=B6_REF_BN, pairs={}, note="first-order extrapolation of a large change (INFERENCE); prices = 365x24h third-batch duals; dD from the v2 - v1 network loads")
    for pname, (ri, rd) in PAIRS.items():
        rows = []
        for r in m.itertuples():
            pi, pdd = pr(ri, r.country, r.network_account, r.carrier), pr(rd, r.country, r.network_account, r.carrier)
            if np.isnan(pi) or np.isnan(pdd):
                rows.append(dict(country=r.country, sector=r.sector, account=r.network_account, carrier=r.carrier, cls=r.cls, dD_twh=r.dD_mwh / 1e6, price_int=None, price_dis=None, dC_int=0.0, dC_dis=0.0, priced=False)); continue
            rows.append(dict(country=r.country, sector=r.sector, account=r.network_account, carrier=r.carrier, cls=r.cls, dD_twh=r.dD_mwh / 1e6, price_int=pi, price_dis=pdd, dC_int=pi * r.dD_mwh, dC_dis=pdd * r.dD_mwh, priced=True))
        df = pd.DataFrame(rows)
        tot = dict(d_demand_twh=float(df.dD_twh.sum()), d_demand_unpriced_twh=float(df[~df.priced].dD_twh.sum()), d_cost_integrated_bn_eur=float(df.dC_int.sum()) / 1e9, d_cost_disconnected_bn_eur=float(df.dC_dis.sum()) / 1e9)
        tot["d_b6_bn_eur"] = tot["d_cost_disconnected_bn_eur"] - tot["d_cost_integrated_bn_eur"]; tot["d_b6_bn_usd"] = tot["d_b6_bn_eur"] * EUR_TO_USD
        tot["predicted_b6_bn_eur"] = B6_REF_BN + tot["d_b6_bn_eur"]
        byc = df.groupby("country")[["dD_twh", "dC_int", "dC_dis"]].sum()
        by_country = {c: dict(d_demand_twh=float(v.dD_twh), d_owen_share_bn=float(v.dC_int) / 1e9, d_standalone_bn=float(v.dC_dis) / 1e9, d_benefit_bn=float(v.dC_dis - v.dC_int) / 1e9) for c, v in byc.iterrows()}
        bycls = df.groupby("cls")[["dD_twh", "dC_int", "dC_dis"]].sum()
        by_class = {k: dict(d_demand_twh=float(v.dD_twh), d_cost_integrated_bn=float(v.dC_int) / 1e9, d_cost_disconnected_bn=float(v.dC_dis) / 1e9, d_b6_bn=float(v.dC_dis - v.dC_int) / 1e9) for k, v in bycls.iterrows()}
        res["pairs"][pname] = dict(totals=tot, by_country=by_country, by_class=by_class, unpriced_rows=df[~df.priced][["country", "account", "carrier", "dD_twh"]].to_dict("records"))
        df.to_csv(OUT / "evidence" / f"DFX_FIRST_ORDER_ROWS_{ri}_{rd}.csv", index=False, float_format="%.6f")
    res["price_fallbacks"] = [dict(run=r, country=c, account=a_, carrier=car, how=h) for r, c, a_, car, h in sorted(set(fallback_log))]
    (OUT / "evidence/DFX_FIRST_ORDER.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    L = ["# DFX 一阶预测（v2 − v1，第三批 365×24h 对偶价格；INFERENCE，大变动外推）", ""]
    for pname, r in res["pairs"].items():
        t = r["totals"]
        L += [f"## {pname}", "", f"- ΔD = {t['d_demand_twh']:+.1f} TWh（未定价 {t['d_demand_unpriced_twh']:+.2f} TWh）；ΔC_一体化 = {t['d_cost_integrated_bn_eur']:+.3f} bn EUR；ΔC_不互联 = {t['d_cost_disconnected_bn_eur']:+.3f} bn EUR；"
              f"**ΔB6 = {t['d_b6_bn_eur']:+.3f} bn EUR（{t['d_b6_bn_usd']:+.3f} bn USD）**；预测 B6 ≈ {B6_REF_BN:.3f} + ΔB6 = {t['predicted_b6_bn_eur']:.3f} bn EUR", "",
              "| 变动类别 | ΔD TWh | ΔC_int bn | ΔC_dis bn | ΔB6 bn |", "|---|---|---|---|---|"]
        L += [f"| {k} | {v['d_demand_twh']:+.1f} | {v['d_cost_integrated_bn']:+.3f} | {v['d_cost_disconnected_bn']:+.3f} | {v['d_b6_bn']:+.3f} |" for k, v in sorted(r["by_class"].items())]
        L += ["", "| 国 | ΔD TWh | Δ Owen 份额 bn | Δ 单干成本 bn | Δ 受益 bn |", "|---|---|---|---|---|"]
        L += [f"| {c} | {v['d_demand_twh']:+.1f} | {v['d_owen_share_bn']:+.3f} | {v['d_standalone_bn']:+.3f} | {v['d_benefit_bn']:+.3f} |" for c, v in r["by_country"].items() if c in C11]
        L.append("")
    L += ["价格回退（v1 中不存在的负荷类）：" + ("; ".join(f"{f['run']} {f['country']} {f['account']} {f['carrier']}: {f['how']}" for f in res["price_fallbacks"]) or "无"), ""]
    (OUT / "DFX_FIRST_ORDER.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
