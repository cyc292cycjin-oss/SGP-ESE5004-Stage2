"""V4 S1 section 1 (items 1-7): captive coal power in the Indonesian 2019 'other' bucket.

    PYTHONHASHSEED=0 python scripts/v4s1_captive.py --work <work dir> --repo /home/jin/wt_v4_data      (WSL pypsa-earth python)

1. Base: which UNSD 2019 transactions and coal commodities make the ID industry coal of v3 (pypsa-asean UNdata export 2025-05-02 and the
   conversion factors of pypsa-asean _helpers.get_conv_factors), why S0 section 7.7 says 269 TWh and the UNSD-row table says 241.36 TWh.
2. UNSD 2019 autoproducer rows (transformation input, production, capacity).
3. HEESI 2025 (v4s1_common.heesi_values): coal sales by user, captive / own-use (IUPTLS) capacity and generation, non-PLN industrial use.
4. GEM GIPT 2026-09 (repository source table): captive coal units from the 'Captive Industry Type' field, 2019 operating status from the
   start / retired year; keyword screen of the remaining units for manual checking.
5. 2019 captive coal = capacity x hours x specific coal use, three levels, every parameter from a source on disk (see LEVELS).
6. Cross-checks: HEESI coal sales by user, HEESI non-PLN industrial electricity, UNSD autoproducer production, BPS IBS 2019 table 5.1
   self-generation, v3 nickel electricity (USGS x Wei 2020) and nickel process coal against HEESI metallurgy sales.
7. Overlap with the v3 explicit sub-sectors (nickel, primary aluminium, alumina, cement, steel).
Outputs in s1/: ID_CAPTIVE_BASE_TRACE.csv, HEESI_2025_VALUES_USED.csv, ID_CAPTIVE_UNITS_GIPT.csv, ID_CAPTIVE_COAL_2019.csv,
ID_CAPTIVE_CROSSCHECK.csv, ID_CAPTIVE_V3_OVERLAP.csv, _captive_evidence.json. Read-only on the repository; nothing is solved.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s1_common as cm   # noqa: E402

PLANTS_POWER_COMPANY = ("Cikarang Babelan power station", "PT Krakatau Posco Energy power station", "Merak power station")
GROUP = {   # GEM 'Captive Industry Type' -> (instruction group, v3 explicit sub-sector, HEESI 6.1.4 sales category), INFERENCE for the last two
    "nickel": ("金属冶炼", "nickel", "Iron, Steel & Metallurgy"),
    "aluminum, nickel": ("金属冶炼", "nickel", "Iron, Steel & Metallurgy"),
    "aluminum": ("金属冶炼", "alumina", "Iron, Steel & Metallurgy"),
    "iron & steel": ("金属冶炼", "steel", "Iron, Steel & Metallurgy"),
    "pulp & paper": ("造纸", None, "Pulp & Paper"),
    "cement & building": ("水泥", "cement", "Cement, Textile, Fertilizer"),
    "chemicals": ("化工", None, "Cement, Textile, Fertilizer"),
    "textiles": ("其他", None, "Cement, Textile, Fertilizer"),
    "industrial park": ("其他", None, "Others"),
    "other metals & mining": ("其他", None, "Others"),
}
SPLIT = {"chemicals, iron & steel": [("iron & steel", 0.5), ("chemicals", 0.5)]}   # Krakatau Posco Energy: half steel, half chemicals (INFERENCE)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); ap.add_argument("--repo", type=Path, default=cm.REPO)
    a = ap.parse_args()
    out = a.work / "s1"; out.mkdir(exist_ok=True)
    R = a.repo / "research_inputs"
    ev = {}
    cf = cm.conv_factors()
    H = cm.heesi_values(a.work); H.to_csv(out / "HEESI_2025_VALUES_USED.csv", index=False)
    BOE = cm.boe_gj(H)
    u = cm.unsd()

    # ---- 1. base trace ------------------------------------------------------------------------------------------------------
    tr = pd.read_csv(cm.PYPSA_ASEAN / "data/unsd_transactions.csv", sep=";")
    keep = dict(zip(tr.Transaction.str.strip().str.lower(), tr.clean_name))
    coalish = ["Hard coal", "Hrad coal", "Coke-oven coke", "Coke oven coke", "Coke Oven Coke", "Brown coal briquettes", "Brown Coal Briquettes",
               "Lignite", "Sub-bituminous coal", "Other bituminous coal", "Coking coal", "Anthracite"]
    z = u[u.commodity.isin(coalish)].copy()
    z["branch"] = z.transaction.str.strip().str.lower().map(keep)
    z["factor_twh_per_kt"] = z.commodity.map(cf)
    z["twh"] = z.q * z.factor_twh_per_kt
    z["in_v3_industry"] = z.branch.notna() & (z.commodity != "Other bituminous coal")
    base = z[z.in_v3_industry].groupby("branch").twh.sum()
    cache = json.loads((R / "assembly_v1/sources/industry_cache.json").read_text())
    crow = {r["carrier"]: r for r in cache["records"] if r["country"] == "ID"}["coal"]
    for b, v in base.items():
        if abs(float(crow[b]) / 1e6 - v) > 1e-6:
            raise ValueError(f"UNSD coal {b}: {v} TWh vs cache {float(crow[b]) / 1e6}")
    p = pd.read_csv(R / "demand_v5/INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")
    pid = p[p.country == "ID"]
    cem19 = pid[(pid.subsector == "cement")].set_index("carrier").mwh_2019.astype(float)
    st19 = pid[(pid.subsector == "iron and steel")].set_index("carrier").mwh_2019.astype(float)
    ob = pd.read_csv(R / "demand_v5/INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[(ob["mode"] == "aeo8_ats_anchor") & (ob.country == "ID")].iloc[0]
    other_raw = float(crow["other"]) / 1e6
    other19_coal = float(ob.other_2019_coal_mwh) / 1e6
    if abs(other_raw - cem19["coal"] / 1e6 - other19_coal) > 1e-6:
        raise ValueError("other coal after the cement deduction not reproduced")
    v3ev = json.loads((R / "industry_v3/INDUSTRY_V3_EVIDENCE.json").read_text())
    oscale = float(v3ev["cases"]["main"]["by_country"]["ID"]["other_scale"])
    dem = pd.read_csv(R / "demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False)
    did = dem[(dem.country == "ID") & (dem.sector == "Industry")]
    mult = float(did.multiplier_total.astype(float).iloc[0])
    e19 = {r.carrier: float(r.base_2019_mwh) / 1e6 for r in did.itertuples()}
    man_kt = float(u[(u.commodity == "Hard coal") & (u.transaction == "consumption by manufacturing, construction and non-fuel mining industry")].q.iloc[0])
    heesi_ind_t = cm.hv(H, "Coal", 2019, "5.1.1")
    ncv = {"pypsa-asean / UNSD hard coal 0.007167 TWh/kt (25.80 GJ/t)": cf["Hard coal"] * 3.6e3,
           "HEESI Kalimantan coal 4.2 BOE/t (before 2023)": cm.hv(H, "Kalimantan Coal") * BOE,
           "HEESI average coal 3.4554 BOE/t (from 2023)": cm.hv(H, "Average Coal") * BOE}
    bt = [dict(block="unsd_row", item=f"{r.commodity} | {r.transaction}", value=r.q, unit="kt", factor_twh_per_kt=r.factor_twh_per_kt, twh=r.twh,
               v3_branch=(r.branch if r.in_v3_industry else "not in v3 industry"), note="") for r in z.sort_values(["in_v3_industry", "branch", "commodity"], ascending=[False, True, True]).itertuples()]
    bt += [dict(block="reconcile", item="cache other coal (UNSD n.e.s. industry: hard coal 37,514.237 kt + coke-oven coke 57.8 kt) = S0 section 7.7 '269 TWh'", value=other_raw, unit="TWh", note="EXACT: equals industry_cache.json ID coal 'other'"),
           dict(block="reconcile", item="minus v3 2019 cement energy taken from other, coal part (EDGAR clinker x PyPSA-Eur Cement ratio, spread over the other-row fuels)", value=-float(cem19["coal"]) / 1e6, unit="TWh", note="INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"),
           dict(block="reconcile", item="minus steel energy above the UNSD iron-and-steel row taken from other", value=0.0, unit="TWh", note="ID: UNSD row 37.79 TWh used as is, no excess"),
           dict(block="reconcile", item="= other 2019 coal after deductions (v2 basis) = V3_OTHER_BUCKET_UNSD_ROWS '241.36'", value=other19_coal, unit="TWh", note="INDUSTRY_2050_OTHER_BUCKET.csv other_2019_coal_mwh"),
           dict(block="reconcile", item="x v3 other-bucket scale (non-ferrous explicit, D163-6 a) = v3-equivalent 2019 coal", value=other19_coal * oscale, unit="TWh", note=f"scale {oscale:.6f}"),
           dict(block="reconcile", item="other 2019 total after deductions (v2 basis; the instruction calls it 'v3 等效 633.14')", value=float(ob.other_2019_mwh) / 1e6, unit="TWh", note="v3-equivalent = x scale"),
           dict(block="reconcile", item="other 2019 total v3-equivalent", value=float(ob.other_2019_mwh) / 1e6 * oscale, unit="TWh", note="S0 table 2.1 '604.43'"),
           dict(block="reconcile", item="ID industry coal 2019, D1 base (all UNSD industry rows)", value=e19["coal"], unit="TWh", note="DEMAND_2050_..._ATS_ANCHOR base_2019_mwh")]
    for k, v in ncv.items():
        bt.append(dict(block="ncv", item=f"UNSD manufacturing hard coal {man_kt:,.0f} kt at {k}", value=man_kt * v / 3.6e3, unit="TWh", note=f"{v:.3f} GJ/t"))
        bt.append(dict(block="ncv", item=f"HEESI 5.1.1 industrial coal {heesi_ind_t / 1e3:,.0f} kt at {k}", value=heesi_ind_t * v / 3.6e6, unit="TWh", note=f"{v:.3f} GJ/t"))
    bt.append(dict(block="ncv", item="HEESI 5.1.2 industrial coal 2019 in BOE x derived BOE size", value=cm.hv(H, "Coal", 2019, "5.1.2") * BOE / 3.6e6, unit="TWh",
                   note=f"BOE = 3.6 GJ / 0.6130 = {BOE:.4f} GJ (Annex 03 electric power factor), INFERENCE"))
    BT = pd.DataFrame(bt); BT.to_csv(out / "ID_CAPTIVE_BASE_TRACE.csv", index=False, float_format="%.6f")
    ev["base"] = dict(other_raw_twh=other_raw, cement_coal_2019_twh=float(cem19["coal"]) / 1e6, other19_coal_v2_twh=other19_coal, other19_coal_v3eq_twh=other19_coal * oscale,
                      other19_total_v2_twh=float(ob.other_2019_mwh) / 1e6, other19_total_v3eq_twh=float(ob.other_2019_mwh) / 1e6 * oscale, other_scale=oscale, multiplier=mult,
                      e19_twh=e19, hard_coal_nes_kt=float(z[(z.commodity == "Hard coal") & (z.branch == "other")].q.sum()), manufacturing_hard_coal_kt=man_kt,
                      ncv_gj_per_t=ncv, boe_gj=BOE, heesi_industrial_coal_t=heesi_ind_t)

    # ---- 2. UNSD autoproducer rows -------------------------------------------------------------------------------------------
    ap_rows = u[u.transaction.str.contains("autoproducer|self-producer", case=False) | ((u.commodity == "Electricity") & u.transaction.str.contains("total production"))]
    A_kt = float(u[(u.commodity == "Hard coal") & (u.transaction == "transformation in electricity plants - autoproducers")].q.iloc[0])
    gas_tj = float(u[u.transaction.str.lower().eq("transformation in electricity plants - autoproducers") & u.commodity.str.lower().str.startswith("natural gas")].q.sum())
    dsl_kt = float(u[(u.commodity == "Gas Oil/ Diesel Oil") & (u.transaction == "Transformation in electricity plants - autoproducers")].q.iloc[0])
    ap_prod = float(u[(u.commodity == "Electricity") & (u.transaction == "total production, autoproducer")].q.iloc[0])
    ap_cap = float(u[(u.commodity == "Electricity") & (u.transaction == "total net installed capacity of electric power plants, autoproducer")].q.iloc[0])
    fuel_in = dict(coal_twh=A_kt * cf["Hard coal"], gas_twh=gas_tj / 3.6e3, diesel_twh=dsl_kt * cf["Gas Oil/ Diesel Oil"])
    ev["unsd_autoproducer"] = dict(rows=[dict(commodity=r.commodity, transaction=r.transaction, unit=r.Unit, q=r.q) for r in ap_rows.itertuples()],
                                   coal_kt=A_kt, gas_tj=gas_tj, diesel_kt=dsl_kt, production_gwh=ap_prod, capacity_mw=ap_cap, fuel_input_twh=fuel_in,
                                   fuel_input_total_twh=sum(fuel_in.values()), main_activity_coal_kt=float(u[(u.commodity == "Hard coal") & (u.transaction == "transformation in electricity plants - main activity producers")].q.iloc[0]))

    # ---- 4. GIPT captive units -------------------------------------------------------------------------------------------------
    g = pd.read_csv(a.repo / cm.GIPT, low_memory=False)
    sub_col = [k for k in g.columns if k.startswith("Subnational")][0]
    c = g[g.iso.eq("ID") & g.Type.eq("coal")].copy()
    c["sy"] = pd.to_numeric(c["Start year"], errors="coerce"); c["ry"] = pd.to_numeric(c["Retired year"], errors="coerce")
    was_op = c.Status.isin(["operating", "retired", "mothballed"])
    c["op_2019_yearend"] = was_op & (c.sy <= 2019) & ~(c.ry <= 2019)
    c["w_2019_avg"] = np.where(c.op_2019_yearend, np.where(c.sy == 2019, 0.5, 1.0), 0.0)
    cap = c[c["Captive Industry Type"].notna()].copy()
    cap["basis"] = "GIPT field 'Captive Industry Type'"
    rest = c[c["Captive Industry Type"].isna() & c.op_2019_yearend]
    own = rest["Owner(s)"].fillna("") + " | " + rest["Parent(s)"].fillna("")
    utility = re.compile(r"PLN|Pembangkitan|Indonesia Power|Power|Energi|Energy|Listrik|Daya|Tenaga|Paiton|Jawa|Bhimasena|Cirebon|Adaro|Bukit Asam|Electric", re.I)
    cand = rest[~own.str.contains(utility)].copy()
    cand["basis"] = "candidate for manual check: no captive field, owner name is not a utility / IPP keyword (not counted)"
    U = pd.concat([cap, cand])
    U["group"] = U["Captive Industry Type"].map(lambda t: "钢/化工（按 1:1 拆分）" if t in SPLIT else (GROUP[t][0] if t in GROUP else ""))
    U["v3_subsector"] = U["Captive Industry Type"].map(lambda t: "steel (half)" if t in SPLIT else (GROUP[t][1] if t in GROUP else None))
    U["heesi_sales_category"] = U["Captive Industry Type"].map(lambda t: "Iron, Steel & Metallurgy / Cement, Textile, Fertilizer (half each)" if t in SPLIT else (GROUP[t][2] if t in GROUP else None))
    U["power_company_plant"] = U["Plant / Project name"].isin(PLANTS_POWER_COMPANY)
    cols = ["GEM unit/phase ID", "GEM location ID", "Plant / Project name", "Unit / Phase name", "Capacity (MW)", "Status", "Start year", "Retired year", "Technology", "CHP",
            "Captive Industry Type", "Captive Industry Use", "Owner(s)", "Parent(s)", sub_col, "Latitude", "Longitude", "Location accuracy",
            "op_2019_yearend", "w_2019_avg", "group", "v3_subsector", "heesi_sales_category", "power_company_plant", "basis"]
    UO = U[cols].rename(columns={sub_col: "Subnational unit"}).assign(source="GEM Global Integrated Power Tracker 2026-09 (research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv)")
    UO.sort_values(["basis", "op_2019_yearend", "Captive Industry Type", "Plant / Project name", "Unit / Phase name"], ascending=[True, False, True, True, True]).to_csv(out / "ID_CAPTIVE_UNITS_GIPT.csv", index=False)

    # allocation rows (Krakatau Posco Energy split)
    al = []
    for r in cap[cap.op_2019_yearend].itertuples():
        t = r._asdict()["_" + str(list(cap.columns).index("Captive Industry Type") + 1)] if False else getattr(r, "_" + str(list(cap.columns).index("Captive Industry Type") + 1))
        parts = SPLIT.get(t, [(t, 1.0)])
        for tt, sh in parts:
            al.append(dict(plant=getattr(r, "_" + str(list(cap.columns).index("Plant / Project name") + 1)), gem_type=t, alloc_type=tt, share=sh,
                           mw_end=float(getattr(r, "_" + str(list(cap.columns).index("Capacity (MW)") + 1))) * sh, mw_avg=float(getattr(r, "_" + str(list(cap.columns).index("Capacity (MW)") + 1))) * sh * r.w_2019_avg))
    AL = pd.DataFrame(al)
    AL["group"] = AL.alloc_type.map(lambda t: GROUP[t][0]); AL["v3_subsector"] = AL.alloc_type.map(lambda t: GROUP[t][1]); AL["heesi_cat"] = AL.alloc_type.map(lambda t: GROUP[t][2])
    AL["power_company_plant"] = AL.plant.isin(PLANTS_POWER_COMPANY)
    ev["gipt"] = dict(captive_units_all_status=int(len(cap)), captive_operating_2026_mw=float(cap[cap.Status == "operating"]["Capacity (MW)"].sum()),
                      captive_2019_yearend_mw=float(AL.mw_end.sum()), captive_2019_avg_mw=float(AL.mw_avg.sum()), units_2019=int(cap.op_2019_yearend.sum()),
                      start_2019_mw=float(cap[cap.op_2019_yearend & (cap.sy == 2019)]["Capacity (MW)"].sum()),
                      by_type_2019_yearend_mw=cap[cap.op_2019_yearend].groupby("Captive Industry Type")["Capacity (MW)"].sum().to_dict(),
                      candidates=cand[["Plant / Project name", "Unit / Phase name", "Capacity (MW)", "Owner(s)"]].astype(str).values.tolist(),
                      all_coal_operating_2026_mw=float(c[c.Status == "operating"]["Capacity (MW)"].sum()))

    # ---- 5. levels ------------------------------------------------------------------------------------------------------------
    pln_t = {int(r.year): r.value for r in H[(H.column == "Coal") & H.table.str.startswith("6.4.7")].itertuples()}
    pln_g = {int(r.year): r.value for r in H[(H.column == "Steam PP Coal") & ((H.table == "6.4.2") | H.table.str.startswith("6.4.2 "))].itertuples()}
    spec = {y: pln_t[y] / (pln_g[y] * 1e3) for y in range(2015, 2025)}   # t per MWh
    h_low = ap_prod / ap_cap * 1e3   # GWh / MW -> h
    steam_gwh = cm.hv(H, "Steam PP Total", 2019, "6.4.2 ") + cm.hv(H, "Steam PP Total", 2019, "6.4.2A")
    h_mid = steam_gwh / cm.hv(H, "Steam PP", 2019, "6.4.1A") * 1e3
    iup_mw = cm.hv(H, "IUPTLS Steam", 2025) + cm.hv(H, "PPU Steam", 2025) + cm.hv(H, "IUPTLS Coal Gasification", 2025) + cm.hv(H, "PPU Coal Gasification", 2025)
    h_high = cm.hv(H, "IUPTLS & PPU Steam PP", 2025) / iup_mw * 1e3
    LEVELS = {
        "low": dict(cap="avg", h=h_low, h_src=f"UNSD 2019 autoproducer production {ap_prod:,.2f} GWh / autoproducer capacity {ap_cap:,.2f} MW (all fuels)", h_grade="B (C as coal proxy)",
                    s=min(spec.values()), s_src=f"HEESI 6.4.7 / 6.4.2: PLN coal t per MWh, minimum of 2015-2024 ({min(spec, key=spec.get)})", s_grade="B (C as captive proxy)", A=A_kt),
        "mid": dict(cap="avg", h=h_mid, h_src=f"HEESI 2019 on-grid steam PP (PLN {cm.hv(H, 'Steam PP Total', 2019, '6.4.2 '):,.0f} + purchased {cm.hv(H, 'Steam PP Total', 2019, '6.4.2A'):,.0f} GWh) / steam capacity {cm.hv(H, 'Steam PP', 2019, '6.4.1A'):,.2f} MW (6.4.1A)",
                    h_grade="B (C as captive proxy)", s=spec[2019], s_src="HEESI 6.4.7 / 6.4.2: PLN 2019 coal 67,008,829 t / PLN coal generation 119,520 GWh", s_grade="B (C as captive proxy)", A=A_kt),
        "high": dict(cap="end", h=h_high, h_src=f"HEESI 2025 IUPTLS & PPU steam generation {cm.hv(H, 'IUPTLS & PPU Steam PP', 2025):,.0f} GWh (6.4.2B, incl. coal gasification) / IUPTLS + PPU steam and coal-gasification capacity {iup_mw:,.2f} MW (6.4.1B)",
                     h_grade="B for 2025 own-use plants, C for 2019", s=max(spec.values()), s_src=f"HEESI 6.4.7 / 6.4.2: PLN coal t per MWh, maximum of 2015-2024 ({max(spec, key=spec.get)})", s_grade="B (C as captive proxy)", A=0.0),
    }
    rows, frames = [], {}
    MWH_PER_T = cf["Hard coal"] * 1e3   # model basis: MWh per t (UNSD hard coal factor)
    for lv, L in list(LEVELS.items()) + [("central", None)]:
        if lv == "central":   # PROPOSED after the cross-checks: nickel at mid, every other sector at low
            x = pd.concat([frames["mid"][frames["mid"].v3_subsector == "nickel"], frames["low"][frames["low"].v3_subsector != "nickel"]])
            L = dict(cap="avg", h=np.nan, s=np.nan, A=A_kt, h_src="nickel: mid; other sectors: low (cross-checks: P&P sales, BPS paper self-generation, national top-down residual)",
                     h_grade="PROPOSED", s_src="as the level of each sector", s_grade="PROPOSED")
        else:
            x = AL.copy()
            x["mw"] = x.mw_avg if L["cap"] == "avg" else x.mw_end
            x["h"], x["s"] = L["h"], L["s"]
            x["gen_gwh"] = x.mw * L["h"] / 1e3
            x["coal_kt"] = x.gen_gwh * L["s"]   # GWh x t/MWh = kt
            pc = x[x.power_company_plant].coal_kt.sum()
            take = min(L["A"], pc)
            x["A_kt"] = np.where(x.power_company_plant, x.coal_kt / pc * take if pc > 0 else 0.0, 0.0)
            left = L["A"] - take
            if left > 1e-9:
                x["A_kt"] += x.coal_kt / x.coal_kt.sum() * left
            x["coal_ind_kt"] = x.coal_kt - x.A_kt
            frames[lv] = x
        for (grp, sub, hc), gg in list(x.groupby(["group", "v3_subsector", "heesi_cat"], dropna=False)) + [(("合计", None, None), x)]:
            rows.append(dict(level=lv, group=grp, v3_subsector=sub, heesi_sales_category=hc, capacity_basis=("2019 年均（2019 投产计半年）" if L["cap"] == "avg" else "2019 年末"),
                             mw=float(gg.mw.sum()), hours=float(gg.gen_gwh.sum() / gg.mw.sum() * 1e3) if gg.mw.sum() else np.nan, gen_gwh=float(gg.gen_gwh.sum()),
                             spec_t_per_mwh=float(gg.coal_kt.sum() / gg.gen_gwh.sum()) if gg.gen_gwh.sum() else np.nan, coal_kt=float(gg.coal_kt.sum()),
                             unsd_autoproducer_kt_assigned=float(gg.A_kt.sum()), coal_in_industry_kt=float(gg.coal_ind_kt.sum()),
                             coal_in_industry_twh_model=float(gg.coal_ind_kt.sum()) * MWH_PER_T / 1e3,
                             coal_in_industry_twh_heesi_kalimantan=float(gg.coal_ind_kt.sum()) * ncv["HEESI Kalimantan coal 4.2 BOE/t (before 2023)"] / 3.6,
                             gen_in_industry_gwh=float((gg.coal_ind_kt / gg.s).sum()),
                             eta_model=float((gg.coal_ind_kt / gg.s).sum() / (gg.coal_ind_kt.sum() * MWH_PER_T)) if gg.coal_ind_kt.sum() else np.nan,
                             share_of_nes_coal_row=float(gg.coal_ind_kt.sum()) * MWH_PER_T / 1e3 / other_raw,
                             share_of_heesi_industrial_coal_t=float(gg.coal_ind_kt.sum()) * 1e3 / heesi_ind_t,
                             hours_source=L["h_src"], hours_grade=L["h_grade"], spec_source=L["s_src"], spec_grade=L["s_grade"],
                             note=("UNSD 2019 autoproducer coal 1,694 kt (already in transformation, not in the industry row) assigned to Cikarang Babelan, Krakatau Posco Energy, Merak (separate power companies, INFERENCE)"
                                   if L["A"] else "UNSD autoproducer coal not deducted (upper bound)")))
    E = pd.DataFrame(rows)
    LEVELS["central"] = dict(cap="avg", h=np.nan, s=np.nan, A=A_kt, h_src="nickel at mid, other sectors at low", h_grade="PROPOSED", s_src="", s_grade="PROPOSED")
    E.to_csv(out / "ID_CAPTIVE_COAL_2019.csv", index=False, float_format="%.6g")
    ev["levels"] = {k: {kk: (vv if not isinstance(vv, float) else float(vv)) for kk, vv in v.items()} for k, v in LEVELS.items()}
    ev["pln_spec_t_per_mwh"] = spec
    ev["estimate_total"] = E[E.group == "合计"].set_index("level")[["mw", "gen_gwh", "coal_kt", "coal_in_industry_kt", "coal_in_industry_twh_model", "gen_in_industry_gwh", "eta_model",
                                                                    "share_of_nes_coal_row", "share_of_heesi_industrial_coal_t"]].to_dict("index")

    # ---- 6. cross-checks ----------------------------------------------------------------------------------------------------
    cc = []
    mid = E[(E.level == "mid") & (E.group != "合计")]
    sales = {k: cm.hv(H, k, 2019, "6.1.4") for k in ["Iron, Steel & Metallurgy", "Pulp & Paper", "Cement, Textile, Fertilizer", "Others"]}
    for k, v in sales.items():
        for lv in LEVELS:
            e = E[(E.level == lv) & (E.group != "合计")]
            cat = e[e.heesi_sales_category == k].coal_kt.sum()
            cc.append(dict(check="HEESI 6.1.4 coal sales 2019 by user vs GIPT-based captive coal (before the UNSD autoproducer deduction)", item=k, level=lv,
                           reference=v / 1e3, estimate=float(cat), unit="kt", ratio=float(cat) / (v / 1e3),
                           note="sales include process coal (kilns, boilers); a ratio above 1 means the level is not consistent with the sales category"))
    np_ind = cm.hv(H, "Non PLN consumption Industry", 2019)
    offgrid = cm.hv(H, "Off-grid Total", 2019)
    td = pd.read_csv(R / "cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv")
    eff = {t: float(td[(td.technology == t) & (td.parameter == "efficiency")].value.iloc[0]) for t in ("OCGT", "CCGT", "oil")}
    for eg in ("OCGT", "CCGT"):
        gd = fuel_in["gas_twh"] * eff[eg] * 1e3 + fuel_in["diesel_twh"] * eff["oil"] * 1e3
        cc.append(dict(check="top-down 2019 captive coal generation = HEESI non-PLN industrial electricity - HEESI off-grid generation - UNSD autoproducer gas and diesel x technology-data efficiency",
                       item=f"gas at {eg} {eff[eg]:.2f}, diesel at oil {eff['oil']:.2f}", level="", reference=np.nan, estimate=np_ind - offgrid - gd, unit="GWh", ratio=np.nan,
                       note=f"{np_ind:,.0f} - {offgrid:,.0f} - {gd:,.0f}; technology-data v0.15.0 2050 efficiencies (upper bound for 2019 plants -> residual is a lower bound); HEESI non-PLN is consumption (net of station own use)"))
    ev["topdown"] = dict(eff_technology_data=eff, non_pln=np_ind, offgrid=offgrid,
                         residual_gwh={eg: np_ind - offgrid - (fuel_in["gas_twh"] * eff[eg] + fuel_in["diesel_twh"] * eff["oil"]) * 1e3 for eg in ("OCGT", "CCGT")})
    for lv in LEVELS:
        e = E[(E.level == lv) & (E.group == "合计")].iloc[0]
        cc.append(dict(check="HEESI 6.4.4 non-PLN industrial electricity 2019 minus HEESI 6.4.2A off-grid generation (hydro, biomass, biogas ...) vs captive coal generation",
                       item="captive coal generation", level=lv, reference=np_ind - offgrid, estimate=float(e.gen_gwh), unit="GWh", ratio=float(e.gen_gwh) / (np_ind - offgrid),
                       note=f"non-PLN {np_ind:,.0f} GWh - off-grid {offgrid:,.0f} GWh; the remainder still contains gas and diesel autoproducers (UNSD fuel input {fuel_in['gas_twh'] + fuel_in['diesel_twh']:.2f} TWh)"))
        cc.append(dict(check="UNSD 2019 autoproducer production (all fuels) vs captive coal generation", item="captive coal generation", level=lv, reference=ap_prod,
                       estimate=float(e.gen_gwh), unit="GWh", ratio=float(e.gen_gwh) / ap_prod, note=""))
    cc.append(dict(check="UNSD 2019 autoproducer: reported fuel input energy (coal + gas + diesel) vs autoproducer production", item="fuel input energy", level="",
                   reference=ap_prod, estimate=sum(fuel_in.values()) * 1e3, unit="GWh", ratio=sum(fuel_in.values()) * 1e3 / ap_prod,
                   note="EXACT: reported inputs cannot produce the reported output even at 100 % efficiency -> most autoproducer fuel is recorded elsewhere (final consumption), INFERENCE"))
    B = cm.bps_raw(a.work)
    b51 = B[(B.table == "5.1") & (B.line == "total")].set_index("code")
    for code, lab in [("Total", "IBS total"), ("24", "24 basic metals"), ("2420", "2420 basic precious and non-ferrous metals (incl. nickel)"), ("2410", "2410 basic iron and steel"),
                      ("17", "17 paper"), ("23", "23 non-metallic minerals"), ("2394", "2394 cement"), ("20", "20 chemicals"), ("13", "13 textiles")]:
        gen = float(b51.at[code, "el_generated_kwh"]) / 1e6
        cc.append(dict(check="BPS IBS 2019 table 5.1 self-generated electricity (all fuels) vs GIPT-based captive coal generation (mid)", item=lab, level="mid", reference=gen,
                       estimate=float(mid[mid.group == {"24": "金属冶炼", "2420": "金属冶炼", "2410": "金属冶炼", "17": "造纸", "23": "水泥", "2394": "水泥", "20": "化工"}.get(code, "__")].gen_gwh.sum()) if code not in ("Total", "13") else (float(E[(E.level == 'mid') & (E.group == '合计')].gen_gwh.iloc[0]) if code == "Total" else np.nan),
                       unit="GWh", ratio=np.nan, note=f"coal equivalent of the IBS self-generation at {spec[2019]:.4f} t/MWh = {gen * spec[2019]:,.0f} kt (upper bound: IBS does not split by fuel); sold {float(b51.at[code, 'el_sold_kwh']) / 1e6:,.1f} GWh"))
    nf = pd.read_csv(R / "industry_v3/NONFERROUS_PRODUCTION_V3.csv")
    q19 = float(nf[nf.route == "nickel"].q_2019_t.sum())
    ne = v3ev["nickel_unit_energy"]
    ni_el = q19 * ne["electricity_mwh_per_t_ni"] / 1e3; ni_fuel = q19 * ne["fuel_mwh_per_t_ni"] / 1e6   # GWh; TWh
    for lv in LEVELS:
        e = E[(E.level == lv) & (E.v3_subsector == "nickel")]
        cc.append(dict(check="v3 nickel electricity 2019 (USGS Ni content x Wei 2020 23.77 MWh/t) vs GIPT nickel captive generation", item="nickel", level=lv, reference=ni_el,
                       estimate=float(e.gen_gwh.sum()), unit="GWh", ratio=float(e.gen_gwh.sum()) / ni_el, note=f"Ni content 2019 {q19:,.0f} t"))
        tot_kt = float(e.coal_kt.sum()) + ni_fuel * 1e6 / MWH_PER_T / 1e3
        cc.append(dict(check="nickel coal 2019 = captive coal (GIPT) + process fuel (Wei 2020 37.54 MWh/t at the model coal factor) vs HEESI 6.1.4 Iron, Steel & Metallurgy sales",
                       item="nickel", level=lv, reference=sales["Iron, Steel & Metallurgy"] / 1e3, estimate=tot_kt, unit="kt", ratio=tot_kt / (sales["Iron, Steel & Metallurgy"] / 1e3),
                       note=f"process fuel {ni_fuel:.2f} TWh = {ni_fuel * 1e3 / MWH_PER_T:,.0f} kt at the model coal factor; the category also holds steel and other metallurgy"))
    CC = pd.DataFrame(cc); CC.to_csv(out / "ID_CAPTIVE_CROSSCHECK.csv", index=False, float_format="%.6g")
    ev["crosscheck"] = dict(heesi_sales_2019_t=sales, heesi_non_pln_industry_gwh=np_ind, heesi_offgrid_gwh=offgrid, nickel_q2019_t=q19, nickel_el_2019_gwh=ni_el, nickel_fuel_2019_twh=ni_fuel,
                            bps_selfgen_gwh={k: float(b51.at[k, "el_generated_kwh"]) / 1e6 for k in ("Total", "24", "2420", "17", "23", "2394", "20", "13")},
                            bps_sold_gwh={k: float(b51.at[k, "el_sold_kwh"]) / 1e6 for k in ("Total", "24", "2420")})

    # ---- 7. overlap with the v3 explicit sub-sectors ---------------------------------------------------------------------------
    sub = pd.read_csv(R / "industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv"); sub = sub[(sub.case == "main") & (sub.country == "ID")]
    el50 = sub[sub.carrier == "electricity"].groupby("subsector").mwh_2050.sum() / 1e6
    gf = v3ev["cases"]["main"]["nonferrous"]["ID:nonferrous_nickel"]["growth_factor"]
    hb = pd.read_csv(R / "demand_v5/INDUSTRY_HEAT_BANDS_JRC_IDEES_OIS.csv").set_index("carrier")
    coal_heat = float(sum(hb.at["coal", f"share_{b}"] for b in ("low", "medium_a", "medium_b", "high"))) * 0.90
    gipt_hydro = g[g.iso.eq("ID") & g.Type.eq("hydropower") & g["Owner(s)"].fillna("").str.contains("INALUM|Asahan Alum", case=False)]
    ov = []
    ref19 = {"nickel": (ni_el / 1e3, "USGS 2019 Ni content x Wei 2020 23.77 MWh/t (v3 explicit, grid-supplied in the model)"),
             "aluminium_primary": (float(el50.get("nonferrous_aluminium_primary", 0.0)) / gf, "v3 2050 electricity / growth factor (2019 output x PyPSA-Eur 2050 ratio)"),
             "alumina": (float(el50.get("nonferrous_alumina", 0.0)) / gf, "v3 2050 electricity / growth factor (2019 output x PyPSA-Eur 2050 ratio)"),
             "cement": (float(cem19["electricity"]) / 1e6, "v3 2019 cement electricity taken from other (EDGAR clinker x PyPSA-Eur Cement ratio)"),
             "steel": (float(st19["electricity"]) / 1e6, "UNSD 2019 iron-and-steel row electricity (v3 2019 steel energy)")}
    key50 = {"nickel": "nonferrous_nickel", "aluminium_primary": "nonferrous_aluminium_primary", "alumina": "nonferrous_alumina", "cement": "cement", "steel": "steel"}
    for s, (r19, src) in ref19.items():
        for lv in LEVELS:
            e = E[(E.level == lv) & (E.v3_subsector == s)]
            cind = float(e.coal_in_industry_twh_model.sum())
            ov.append(dict(v3_subsector=s, level=lv, captive_mw=float(e.mw.sum()), captive_gen_twh=float(e.gen_gwh.sum()) / 1e3, captive_coal_in_industry_twh=cind,
                           v3_electricity_2019eq_twh=r19, v3_electricity_2019eq_source=src, captive_gen_share_of_v3_el=(float(e.gen_gwh.sum()) / 1e3 / r19 if r19 else np.nan),
                           v3_electricity_2050_twh=float(el50.get(key50[s], 0.0)),
                           double_count_2050_twh=cind * mult * coal_heat * oscale,
                           note=("2019 primary aluminium (Inalum Kuala Tanjung) ran on the Asahan hydro plants, GIPT hydro owned by Inalum: "
                                 + "; ".join(f"{r['Plant / Project name']} {r['Capacity (MW)']:.0f} MW" for _, r in gipt_hydro.iterrows())) if s == "aluminium_primary" else
                                ("Krakatau Posco Energy counted half (INFERENCE)" if s == "steel" else "")))
    OV = pd.DataFrame(ov); OV.to_csv(out / "ID_CAPTIVE_V3_OVERLAP.csv", index=False, float_format="%.6g")
    ev["overlap"] = dict(coal_to_useful_heat=coal_heat, other_scale=oscale, multiplier=mult, nickel_growth_factor=gf,
                         rows=OV.drop(columns=["v3_electricity_2019eq_source", "note"]).to_dict("records"))
    (out / "_captive_evidence.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
    print(BT[BT.block != "unsd_row"][["item", "value", "unit"]].to_string())
    print(json.dumps(ev["unsd_autoproducer"]["fuel_input_twh"]), ap_prod, ap_cap)
    print({k: round(v["h"], 1) for k, v in LEVELS.items()}, {k: round(v["s"], 4) for k, v in LEVELS.items()}, ev["topdown"])
    print(E[["level", "group", "v3_subsector", "mw", "gen_gwh", "coal_kt", "coal_in_industry_kt", "coal_in_industry_twh_model", "share_of_nes_coal_row"]].round(3).to_string())
    print(CC[["check", "item", "level", "reference", "estimate", "ratio"]].round(3).to_string(max_colwidth=60))
    print(OV.drop(columns=["v3_electricity_2019eq_source", "note"]).round(3).to_string())


if __name__ == "__main__":
    main()
