"""V4 S0 section 2: v3 status in the network-bound basis - the 'other' bucket per country (2019 input-energy basis and 2050 route basis),
its carrier structure, node allocation and time profile; the explicit sub-sectors; the UNSD rows other / construction / mining inside the bucket.

    PYTHONHASHSEED=0 python scripts/v4s0_v3_status.py --repo /home/jin/wt_v4_data --chain-dir /home/jin/v4s0/vn_chain \
        --network <integrated_2920_3h_unsolved.nc> --out <work dir>/evidence

Read-only on the repository: the VN chain of v3 (APEC 2022 shares) is re-run by v3_industry.run_vn_chain in a scratch copy outside the repo
(it copies research_inputs + scripts_project and runs s3_0_industry.py there); nothing is solved, no network is built.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

FUELS = ("coal", "oil", "gas", "biomass")
CARS = ("coal", "oil", "gas", "biomass", "electricity")
BANDS = ("low", "medium_a", "medium_b", "high")
OUT = ("electricity", "heat_low", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass")
UNSD_ROWS = ("other", "construction", "mining and quarrying")
HEAT_EFF = 0.90
ASEAN = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")


def transform(x19: dict, mult: float, band: dict) -> dict:
    """2050 useful_heat_bands transform of one 2019 carrier vector (s3_0_industry.py lines 309-323): electricity x mult; fuel x mult split into
    useful heat x 0.90 in four bands and mechanical fuel."""
    y = {k: 0.0 for k in OUT}
    y["electricity"] = x19.get("electricity", 0.0) * mult
    for f in FUELS:
        e = x19.get(f, 0.0) * mult
        for b in BANDS:
            y[f"heat_{b}"] += e * band[f][b] * HEAT_EFF
        y[f] += e * band[f]["mechanical"]
    return y


def cache_rows(cache: dict, c: str, e19: dict) -> dict:
    """{UNSD row: {carrier: MWh 2019}} = D1 2019 carrier total x the cache share of the row (s3_0_industry.py lines 156-161)."""
    recs = {r["carrier"]: r for r in cache["records"] if r["country"] == c}
    subs = [k for k in (cache["records"][0].keys()) if k not in ("country", "carrier")]
    out = {s: {} for s in subs}
    for car in CARS:
        r = recs.get(car)
        tot = sum(float(r[s]) for s in subs) if r else 0.0
        for s in subs:
            out[s][car] = e19[car] * (float(r[s]) / tot if (r and tot > 0) else (1.0 if s == "other" else 0.0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--chain-dir", type=Path, required=True)
    ap.add_argument("--network", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import v3_industry   # noqa: E402  (ROOT = a.repo)
    R = a.repo / "research_inputs"
    dem = pd.read_csv(R / "demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False)
    ob_v2 = pd.read_csv(R / "demand_v5/INDUSTRY_2050_OTHER_BUCKET.csv"); ob_v2 = ob_v2[ob_v2["mode"] == "aeo8_ats_anchor"].set_index("country")
    v2sum = pd.read_csv(R / "demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country")
    v3sum = pd.read_csv(R / "industry_v3/INDUSTRY_2050_SUMMARY_V3.csv").set_index("country")
    sub = pd.read_csv(R / "industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv"); sub = sub[sub["case"] == "main"]
    ev = json.loads((R / "industry_v3/INDUSTRY_V3_EVIDENCE.json").read_text())["cases"]["main"]
    hb = pd.read_csv(R / "demand_v5/INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv").set_index("carrier")
    band = {f: {b: float(hb.at[f, f"share_{b}"]) for b in BANDS + ("mechanical",)} for f in FUELS}
    cache_v2 = json.loads((R / "assembly_v1/sources/industry_cache.json").read_text())
    shares = pd.read_csv(R / "industry_v3/INDUSTRY_NODE_SHARES_V3.csv")
    fse = json.loads((R / "industry_v3/FACILITY_SHARES_V3_EVIDENCE.json").read_text())

    # ---- VN: scratch chain with the APEC 2022 matrix (v3 D163-1) -------------------------------------------------
    vn_row = v3_industry.run_vn_chain(a.chain_dir)
    cR = a.chain_dir / "research_inputs"
    ob_vn = pd.read_csv(cR / "demand_v5/INDUSTRY_2050_OTHER_BUCKET.csv"); ob_vn = ob_vn[ob_vn["mode"] == "aeo8_ats_anchor"].set_index("country")
    cache_vn = json.loads((cR / "assembly_v1/sources/industry_cache.json").read_text())
    pe_vn = pd.read_csv(cR / "demand_v5/INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")
    pe_v2 = pd.read_csv(R / "demand_v5/INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")

    rows, rows_unsd, rows_sub, rows_disp, checks = [], [], [], [], {}
    for c in ASEAN:
        d = dem[(dem.country == c) & (dem.sector == "Industry")]
        e19 = {car: float(d[d.carrier == car].base_2019_mwh.astype(float).sum()) for car in CARS}
        mult = float(d.multiplier_total.astype(float).iloc[0]) if len(d) else 0.0
        vn = c == "VN"
        ob = ob_vn if vn else ob_v2
        cache = cache_vn if vn else cache_v2
        other19 = {car: float(ob.at[c, f"other_2019_{car}_mwh"]) for car in CARS}
        ur = cache_rows(cache, c, e19)
        ur19 = {"construction": ur["construction"], "mining and quarrying": ur["mining and quarrying"]}
        ur19["other"] = {car: other19[car] - ur19["construction"][car] - ur19["mining and quarrying"][car] for car in CARS}
        neg = {car: v for car, v in ur19["other"].items() if v < -1e-3}
        if neg:
            raise ValueError(f"{c}: negative other row after construction / mining {neg}")
        s = sub[(sub.country == c)]
        v3_other = {k: 0.0 for k in OUT}
        for _, z in s[s.subsector == "other"].iterrows():
            key = {"heat": "heat_low", "heat_medium_a": "heat_medium_a", "heat_medium_b": "heat_medium_b", "heat_high": "heat_high"}.get(z.carrier, z.carrier)
            v3_other[key] += float(z.mwh_2050)
        base50 = transform(other19, mult, band)
        tot_b, tot_3 = sum(base50.values()), sum(v3_other.values())
        f = tot_3 / tot_b if tot_b > 0 else 1.0
        # the transform reproduces the v3 table carrier by carrier (after the one scale factor)
        dev = max((abs(base50[k] * f - v3_other[k]) for k in OUT), default=0.0)
        checks[c] = dict(other_scale_reproduced=f, other_scale_v3_evidence=float(ev["by_country"][c]["other_scale"]) if c in ev["by_country"] else None,
                         max_abs_carrier_dev_mwh=dev)
        T = float(sum(v2sum.at[c, v3_industry.col(x)] for x in v3_industry.CARRIERS)) if c in v2sum.index else 0.0
        v2o = v3_industry.decompose(v2sum.loc[c], v3_industry.future_vectors())["other"] if c in v2sum.index else {}
        v2_other50 = float(sum(v2o.values()))
        ind19 = sum(e19.values())
        o19_v2 = float(sum(float(ob_v2.at[c, f"other_2019_{car}_mwh"]) for car in CARS))
        o19_v3 = sum(other19.values()) * f
        rows.append(dict(country=c, industry_2019_twh=ind19 / 1e6, multiplier=mult,
                         other_2019_v2_twh=o19_v2 / 1e6, other_2019_v2_share=o19_v2 / ind19 if ind19 else 0.0,
                         other_2019_v3_twh=o19_v3 / 1e6, other_2019_v3_share=o19_v3 / ind19 if ind19 else 0.0,
                         industry_2050_bound_twh=T / 1e6, other_2050_v2_twh=v2_other50 / 1e6, other_2050_v2_share=v2_other50 / T if T else 0.0,
                         other_2050_v3_twh=tot_3 / 1e6, other_2050_v3_share=tot_3 / T if T else 0.0, other_scale_v3=f,
                         **{f"other_2050_v3_{k}_twh": v3_other[k] / 1e6 for k in OUT}))
        for r_, x in ur19.items():
            y = transform(x, mult, band)
            rows_unsd.append(dict(country=c, unsd_row=r_, basis=("APEC 2022 shares (v3 VN chain)" if vn else "UNSD 2019 shares (industry_cache.json)"),
                                  **{f"y2019_{car}_twh": x[car] / 1e6 for car in CARS}, y2019_total_twh=sum(x.values()) / 1e6,
                                  y2050_v3_total_twh=sum(y.values()) * f / 1e6, **{f"y2050_v3_{k}_twh": y[k] * f / 1e6 for k in OUT}))
        for k, g in s.groupby("subsector"):
            rows_sub.append(dict(country=c, subsector=k, twh_2050=float(g.mwh_2050.sum()) / 1e6,
                                 **{f"{car}_twh": float(g[g.carrier == car].mwh_2050.sum()) / 1e6 for car in sorted(set(sub.carrier))}))
        pe = pe_vn if vn else pe_v2
        p = pe[(pe.country == c) & (pe.carrier == "all (see mapping shares)") & ~pe.subsector.isin(UNSD_ROWS)].copy()
        p["pypsa_sector"] = p.method.str.extract(r"via (.+)$")[0]
        for (u, ps), g in p.groupby(["subsector", "pypsa_sector"]):
            rows_disp.append(dict(country=c, unsd_row=u, pypsa_eur_sector=ps, mwh_2019=float(g.mwh_2019.sum()), twh_2050=float(g.mwh_2050.sum()) / 1e6,
                                  basis=("APEC 2022 shares (v3 VN chain)" if vn else "UNSD 2019 shares")))
    T = pd.DataFrame(rows).set_index("country")
    tot = T.select_dtypes("number").sum()
    T.loc["ASEAN11"] = tot
    for k in ("other_2019_v2", "other_2019_v3"):
        T.at["ASEAN11", f"{k}_share"] = tot[f"{k}_twh"] / tot["industry_2019_twh"]
    for k in ("other_2050_v2", "other_2050_v3"):
        T.at["ASEAN11", f"{k}_share"] = tot[f"{k}_twh"] / tot["industry_2050_bound_twh"]
    T.at["ASEAN11", "multiplier"] = np.nan; T.at["ASEAN11", "other_scale_v3"] = np.nan
    a.out.mkdir(parents=True, exist_ok=True)
    T.reset_index().to_csv(a.out / "V3_OTHER_BUCKET_BY_COUNTRY.csv", index=False, float_format="%.6f")
    U = pd.DataFrame(rows_unsd); U.to_csv(a.out / "V3_OTHER_BUCKET_UNSD_ROWS.csv", index=False, float_format="%.6f")
    S = pd.DataFrame(rows_sub).fillna(0.0); S.to_csv(a.out / "V3_SUBSECTOR_2050_BY_COUNTRY.csv", index=False, float_format="%.6f")
    D = pd.DataFrame(rows_disp); D.to_csv(a.out / "V3_DISPERSED_BY_UNSD_ROW.csv", index=False, float_format="%.6f")

    # ---- node allocation of the other bucket ------------------------------------------------------------------------
    node = []
    for c in ASEAN:
        x = shares[(shares.country == c) & (shares.subsector == "other")]
        method = (f"DOSE V2.11 制造业产出（{fse['dose_year'][c]} 年）按 ADM1，ADM1 内按节点用电份额（D164-3 a、D164-4 b）" if len(x)
                  else "v2 规则：IndustryFinalEnergy 分配数组（节点用电份额）")
        top = x.sort_values("share", ascending=False).head(3)
        node.append(dict(country=c, method=method, nodes_with_share=int((x.share > 0).sum()) if len(x) else None,
                         top3=("; ".join(f"{n} {s:.1%}" for n, s in zip(top.node, top.share)) if len(x) else "")))
    pd.DataFrame(node).to_csv(a.out / "V3_OTHER_BUCKET_NODE_METHOD.csv", index=False)

    # ---- network check: F1 integrated 2920x3h (v3.1 package) --------------------------------------------------------
    ds = xr.open_dataset(a.network)
    L = pd.DataFrame({k[6:]: ds[k].values for k in ("loads_bus", "loads_carrier", "loads_p_set", "loads_sector", "loads_account", "loads_country")}, index=ds["loads_i"].values)
    ind = L[L.account.astype(str).str.startswith("Industry")].copy()
    ind["twh"] = ind.p_set.astype(float) * 8760.0 / 1e6
    tcols = [str(x) for x in ds["loads_t_p_set_i"].values] if "loads_t_p_set_i" in ds else []
    net = ind.groupby(["country", "carrier"]).twh.sum().unstack(fill_value=0.0)
    car_map = {"industry electricity": "pe_electricity_mwh", "industry heat": "pe_heat_mwh", "industry hydrogen": "pe_hydrogen_mwh", "industry ammonia": "pe_ammonia_mwh",
               "industry methanol": "pe_methanol_mwh", "gas final energy": "pe_gas_mwh", "oil final energy": "pe_oil_mwh"}
    cmp_ = []
    for c in v3sum.index:
        n_c = net.loc[c] if c in net.index else pd.Series(dtype=float)
        ov = ind[(ind.country == c) & (ind.account == "IndustryBiomassOverflowUsefulHeat")].twh.sum()
        for car, colname in car_map.items():
            cmp_.append(dict(country=c, item=car, network_twh=float(n_c.get(car, 0.0)), table_twh=float(v3sum.at[c, colname]) / 1e6))
        for b, colname in (("industry heat medium A", "pe_heat_medium_a_mwh"), ("industry heat medium B", "pe_heat_medium_b_mwh"), ("industry heat high", "pe_heat_high_mwh")):
            band_ov = ind[(ind.country == c) & (ind.account == "IndustryBiomassOverflowUsefulHeat") & (ind.carrier == b)].twh.sum()
            cmp_.append(dict(country=c, item=b + " (without overflow)", network_twh=float(n_c.get(b, 0.0)) - band_ov, table_twh=float(v3sum.at[c, colname]) / 1e6))
        bio_net = float(n_c.get("biomass final energy", 0.0)) + ov / HEAT_EFF
        cmp_.append(dict(country=c, item="biomass final energy + overflow heat / 0.90", network_twh=bio_net, table_twh=float(v3sum.at[c, "pe_biomass_before_overflow_mwh"]) / 1e6))
    C = pd.DataFrame(cmp_); C["abs_diff_twh"] = (C.network_twh - C.table_twh).abs()
    C.to_csv(a.out / "V3_NETWORK_VS_TABLE_F1.csv", index=False, float_format="%.9f")
    netcheck = dict(network=str(a.network.name), snapshots=int(ds.sizes["snapshots"]), weight_sum_h=float(ds["snapshots_generators"].values.sum()),
                    industry_loads=int(len(ind)), industry_loads_with_time_series=int(sum(1 for x in ind.index if str(x) in tcols)),
                    loads_t_p_set_columns=len(tcols), industry_network_total_twh=float(ind.twh.sum()),
                    industry_table_total_twh=float(sum(v3sum[v3_industry.col(x)].sum() for x in v3_industry.CARRIERS)) / 1e6,
                    overflow_heat_twh=float(ind[ind.account == "IndustryBiomassOverflowUsefulHeat"].twh.sum()),
                    max_abs_diff_twh=float(C.abs_diff_twh.max()), accounts=ind.groupby("account").twh.sum().round(6).to_dict())
    out = dict(script="v4s0_v3_status.py", repo=str(a.repo), chain_dir=str(a.chain_dir), reproduction=checks, network_check=netcheck,
               vn_chain_other19_twh=float(sum(float(ob_vn.at["VN", f"other_2019_{car}_mwh"]) for car in CARS)) / 1e6,
               vn_v2_other19_twh=float(sum(float(ob_v2.at["VN", f"other_2019_{car}_mwh"]) for car in CARS)) / 1e6,
               asean11=T.loc["ASEAN11"].round(6).to_dict())
    (a.out / "V3_STATUS_EVIDENCE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(T[["industry_2019_twh", "other_2019_v2_twh", "other_2019_v2_share", "other_2019_v3_twh", "other_2019_v3_share", "industry_2050_bound_twh",
             "other_2050_v2_twh", "other_2050_v2_share", "other_2050_v3_twh", "other_2050_v3_share", "other_scale_v3"]].round(4).to_string())
    print(json.dumps(checks, indent=0)[:1500])
    print(json.dumps(netcheck, indent=0, default=float)[:1500])


if __name__ == "__main__":
    main()
