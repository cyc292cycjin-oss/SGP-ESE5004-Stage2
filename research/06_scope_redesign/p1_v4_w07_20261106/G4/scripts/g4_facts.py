"""G4 facts (V4 W07 section B-G4; method template steps 1-8 of S2 s2/V4_METHOD_TEMPLATE.csv) for MM, KH, LA, BN, TL. Read only.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python -I scripts/g4_facts.py        (WSL)

1  national statistics: UNSD 2019 rows of the UNdata export used by the model (2025-05-02) and the SDMX values (A5 query, g4_sdmx.py) side by side;
2  captive power: S2 screen rows, GEM GIPT units (coal or captive, operating in 2019 by the S1 rule), MM captive coal low / mid / high (S1 method);
3  coal NCV per country (decision 207): v3, UNSD SDMX CONVERSION_FACTOR, national, IPCC, physical evidence, proposed; chain edits for every scheme;
4  cement: USGS MYB 2023 T22 2019-2023, USGS MYB 2017-18 AP T3 2018, EDGAR 2.A.1, implied clinker ratio, GEM plants (clinker / grinding);
5  biomass: UNSD series (export and SDMX), FAOSTAT wood fuel, 5140 / 5150 reporting, candidate main / sensitivity values;
6  products: FAOSTAT paper / pulp (MM, LA), USGS AP T3 copper / ammonia / potash, GEM chemicals (BN difference table, MM ammonia);
7  chain inputs for g4_chain.py (evidence/_chain_inputs.json).
Outputs evidence/*.csv, <CC>_NCV.csv, evidence/_facts_evidence.json, evidence/_chain_inputs.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g4_common as cm   # noqa: E402

EV = cm.Ev("facts")
OUT = cm.G4 / "evidence"
TJ = 1 / 3600.0   # TWh per TJ


# ------------------------------------------------------------------ 1 national statistics -----------------------------------------------------
def twh_row(com, unit, q, cf):
    if pd.isna(q):
        return np.nan
    if "Terajoules" in unit:
        return q * TJ
    if "Kilowatt-hours" in unit:
        return q / 1e3
    key = {"Hrad coal": "Hard coal", "Lignite": "Brown coal", "Sub-bituminous coal": "Brown coal", "Anthracite": "Hard coal",
           "Petroleum Coke": "Petroleum coke", "Liquified Petroleum Gas (LPG)": "Liquefied petroleum gas (LPG)"}.get(com, com)
    return q * cf[key] if key in cf else np.nan


def national(u, sd, cf):
    z = u[u.year == 2019].copy()
    z["twh_v3_factor"] = [twh_row(r.commodity, r.Unit, r.q, cf) for r in z.itertuples()]
    keep = z.transaction.str.contains("industr|manufactur|mining|construction|iron|chemic|non-metal|food|paper|textile|wood|machin|transport equip|non-ferrous|"
                                      "autoproducer|main activity|Transformation|household|commerce|Production|production|import|export|Final", case=False, regex=True)
    z = z[keep].sort_values(["iso", "commodity", "transaction"])
    z[["iso", "commodity", "transaction", "Unit", "q", "footnote", "twh_v3_factor"]].to_csv(OUT / "UNSD_2019_ROWS_G4.csv", index=False, float_format="%.6g")
    # SDMX (current UNSD database) against the export (model input), 2019, same commodity and transaction label
    s19 = sd[sd.year == 2019].copy()
    norm = lambda x: re.sub(r"[^a-z]", "", str(x).lower().replace("hrad", "hard"))
    z["k"] = z.commodity.map(norm) + "|" + z.transaction.map(norm)
    s19["k"] = s19.commodity.map(norm) + "|" + s19.transaction.map(norm)
    ex = z.groupby(["iso", "k"]).q.first()
    u19 = u[u.year == 2019].copy(); u19["cn"] = u19.commodity.map(norm)
    rows = []
    for r in s19.itertuples():
        e = ex.get((r.iso, r.k), np.nan)
        same_com = u19[(u19.iso == r.iso) & (u19.cn == norm(r.commodity))]
        if pd.notna(e):
            note = "equal" if abs(e - r.value) <= 1e-6 * max(1, abs(e)) else "differs (data vintage)"
        elif same_com.empty:
            note = "commodity not in the UNdata export used by the model"
        elif (same_com.q - r.value).abs().min() <= 1e-6 * max(1, abs(r.value)):
            note = "equal value under another transaction label"
            e = r.value
        else:
            note = "transaction label not matched; no equal value in the export"
        rows.append(dict(iso=r.iso, commodity=r.commodity, transaction_code=r.transaction_code, transaction=r.transaction, unit=r.unit, sdmx_2019=r.value,
                         sdmx_obs_status=r.obs_status, sdmx_conversion_factor=r.conversion_factor, export_2019=e, note=note))
    C = pd.DataFrame(rows)
    C.to_csv(OUT / "UNSD_SDMX_VS_EXPORT_2019_G4.csv", index=False, float_format="%.6g")
    for r in C[~C.note.str.startswith("equal")].itertuples():
        EV.put(f"sdmx_vs_export.{r.iso}.{r.commodity}.{r.transaction_code}", r.sdmx_2019, r.unit, f"UNSD SDMX 2019 ({r.sdmx_obs_status}); export {r.export_2019}: {r.note}", "VERIFIED", "B")
    return z, C


# ------------------------------------------------------------------ 2 captive power ------------------------------------------------------------
def captive(u):
    scr = pd.read_csv(cm.S2W / "s2/ASEAN11_CAPTIVE_SCREEN.csv").set_index("iso").loc[cm.C5]
    g = cm.gipt()
    z = g[g.iso.isin(cm.C5) & (g.Type.eq("coal") | g["Captive Industry Type"].notna()) & g.Status.isin(["operating", "mothballed", "retired"])]
    cols = ["iso", "Plant / Project name", "Unit / Phase name", "Owner(s)", "Capacity (MW)", "Status", "Start year", "Retired year", "Type", "Technology",
            "Captive Industry Type", "Captive Industry Use", "Latitude", "Longitude", "op19", "GEM unit/phase ID"]
    z[cols].sort_values(["iso", "Plant / Project name", "Unit / Phase name"]).to_csv(OUT / "GIPT_UNITS_COAL_OR_CAPTIVE_G4.csv", index=False)
    for iso in cm.C5:
        gi = z[(z.iso == iso)]
        c19 = gi[gi.op19 & gi["Captive Industry Type"].notna() & gi.Type.eq("coal")]
        EV.put(f"gipt.{iso}.captive_coal_mw_2019", float(c19["Capacity (MW)"].sum()), "MW", "GEM GIPT 2026-09 'Captive Industry Type', S1 operating rule", "VERIFIED", "B")
    # UNSD rows that locate the captive coal of BN and MM (export 2025-05-02; SDMX in UNSD_SDMX_VS_EXPORT_2019_G4.csv)
    v = lambda iso, com, tr: float(u[(u.iso == iso) & (u.year == 2019) & (u.commodity == com) & (u.transaction == tr)].q.sum())
    f = dict(
        BN_autoproducer_brown_coal_kt=v("BN", "Brown coal", "Transformation in autoproducer electricity plants"),
        BN_industry_coal_kt=0.0,
        BN_autoproducer_output_gwh=v("BN", "Electricity", "total production, autoproducer"),
        BN_chemicals_electricity_gwh=v("BN", "Electricity", "Consumption by chemical and petrochemical"),
        MM_main_activity_coal_kt=v("MM", "Hard coal", "transformation in electricity plants - main activity producers"),
        MM_industry_coal_kt=v("MM", "Hard coal", "consumption by manufacturing, construction and non-fuel mining industry"),
        MM_nmm_coal_kt=v("MM", "Hard coal", "consumption by non-metallic minerals industry"),
        MM_steel_coal_kt=v("MM", "Hrad coal", "consumption by iron and steel industry"),
        MM_autoproducer_output_gwh=v("MM", "Electricity", "total production, autoproducer"),
        MM_autoproducer_capacity_mw=v("MM", "Electricity", "total net installed capacity of electric power plants, autoproducer"),
        MM_autoproducer_gas_tj=v("MM", "Natural Gas (including LNG)", "transformation in electricity plants - autoproducers"))
    for k, x in f.items():
        EV.put(f"captive.unsd.{k}", x, k.split("_")[-1], "UNdata export 2025-05-02 (model input), 2019", "VERIFIED", "B")
    # MM: S1 method, C = MW x hours x heat rate; tonnes with the UNSD MM NCV (23.26 GJ/t SDMX), energy per NCV scheme
    s1 = json.loads((cm.S2W / "V4_S1_EVIDENCE.json").read_text()) if (cm.S2W / "V4_S1_EVIDENCE.json").exists() else {}
    hr_ref = dict(low=0.540, mid=0.5607, high=0.628)   # PLN t/MWh (HEESI 2025 6.4.7 / 6.4.2; S1 section 1.5)
    ncv_id_unsd = 24.480                                # W11 UNSD 2019 ID coal NCV (VERIFIED), converts PLN tonnes to GJ
    hours = dict(low=f["MM_autoproducer_output_gwh"] / f["MM_autoproducer_capacity_mw"] * 1e3, mid=5141.0, high=5868.0)
    mw = dict(low=30.0, mid=70.0, high=70.0)            # low: Myainggalay 30 MW (operating 2018); mid / high: + Mawlamyine 40 MW (2017, status mothballed)
    ncv_mm = 23.26
    rows = []
    for lv in ("low", "mid", "high"):
        gen = mw[lv] * hours[lv] / 1e6   # TWh
        hr_gj = hr_ref[lv] * ncv_id_unsd   # GJ per MWh
        t_kt = gen * 1e6 * hr_gj / ncv_mm / 1e3
        rows.append(dict(level=lv, mw=mw[lv], hours=hours[lv], gen_twh=gen, heat_rate_gj_per_mwh=hr_gj, eta=3.6 / hr_gj, coal_kt=t_kt,
                         share_of_nmm_coal=t_kt / f["MM_nmm_coal_kt"], c_twh_v3=t_kt * 25.801 / 3.6 / 1e3, c_twh_207=t_kt * ncv_mm / 3.6 / 1e3,
                         hours_source={"low": "UNSD 2019 MM autoproducer production 14,415.17 GWh / autoproducer capacity 3,719 MW (B, proxy C)",
                                       "mid": "S1: HEESI 2019 on-grid steam PP generation / capacity (ID analogue, C)",
                                       "high": "S1: HEESI 2025 IUPTLS + PPU steam PP generation / capacity (ID analogue, C)"}[lv],
                         heat_rate_source=f"PLN {hr_ref[lv]} t/MWh (HEESI 2025, S1 section 1.5) x UNSD ID NCV 24.48 GJ/t (W11) (ID analogue, C)",
                         mw_source={"low": "GIPT: Myainggalay Cement 30 MW operating since 2018 (Mawlamyine 40 MW mothballed, date unknown: excluded)",
                                    "mid": "GIPT: Myainggalay 30 + Mawlamyine 40 MW (S1 operating rule counts mothballed)", "high": "as mid"}[lv]))
    M = pd.DataFrame(rows)
    # cross-check: v3 already logs the UNSD NMM row below the activity-based cement energy (EDGAR clinker x PyPSA-Eur Cement ratio)
    gp = pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_2050_GAPS.csv")
    short = float(gp[(gp["mode"] == "aeo8_ats_anchor") & (gp.country == "MM") & gp.item.str.startswith("UNSD NMM row below")].mwh.sum()) / 1e6
    M["kiln_fuel_shortfall_v3_twh"] = short
    M["kiln_fuel_shortfall_if_captive_twh"] = short + M.c_twh_v3
    M.to_csv(OUT / "MM_CAPTIVE_COAL_2019.csv", index=False, float_format="%.6g")
    for r in M.itertuples():
        for k in ("mw", "hours", "gen_twh", "heat_rate_gj_per_mwh", "coal_kt", "share_of_nmm_coal", "c_twh_v3", "c_twh_207", "kiln_fuel_shortfall_if_captive_twh"):
            EV.put(f"captive.MM.{r.level}.{k}", getattr(r, k), k.split("_")[-1], f"{r.hours_source}; {r.heat_rate_source}; {r.mw_source}",
                   "VERIFIED" if k == "mw" else "INFERENCE", "B" if k == "mw" else "C")
    EV.put("captive.MM.v3_kiln_fuel_shortfall_twh", short, "TWh", "INDUSTRY_2050_GAPS.csv: 'UNSD NMM row below EDGAR clinker x PyPSA-Eur Cement ratio'", "VERIFIED", "C")
    # Tigyit (120 MW, GIPT 'iron & steel'): its coal sits in electricity-plant transformation, not in industry; plausibility of 1,382 kt
    tig_max_twh = 120 * 8760 / 1e6
    fuel_twh = f["MM_main_activity_coal_kt"] * 23.26 / 3.6 / 1e3
    EV.put("captive.MM.tigyit_max_gen_twh", tig_max_twh, "TWh", "GIPT 2 x 60 MW at 8,760 h", "EXACT", "B")
    EV.put("captive.MM.transformation_coal_fuel_twh", fuel_twh, "TWh", "UNSD 1,382 kt x 23.26 GJ/t (SDMX)", "EXACT", "B")
    EV.put("captive.MM.implied_max_efficiency_if_tigyit", tig_max_twh / fuel_twh, "-", "upper bound if all 1,382 kt fed Tigyit at 8,760 h", "INFERENCE", "C")
    return scr, M, f


# ------------------------------------------------------------------ 3 NCV -------------------------------------------------------------------
def ncv_tables(sd):
    cf19 = sd[(sd.year == 2019)].dropna(subset=["conversion_factor"])
    get = lambda iso, code, trs: sorted(set(cf19[(cf19.iso == iso) & (cf19.commodity_code == code) & cf19.transaction_code.isin(trs)].conversion_factor))
    ref = pd.read_csv(cm.NCVW / "ncv/NCV_FACTOR_SCHEMES.csv")
    us = pd.read_csv(cm.G4 / "evidence/USGS_AP_2018_T3_G4.csv")
    out = {}
    T = {  # (commodity, v3, sdmx, national, ipcc, physical, proposed main, sensitivity)
        "MM": [dict(commodity="Hard coal (UNSD; industry: steel 121 kt, non-metallic minerals 387 kt)", v3=25.801, unsd_country=get("MM", "0100", ["1211", "1214B", "121"]),
                    national="none on disk (ADB 2016 energy assessment: 'generally low-quality lignite and subbituminous', no value)",
                    ipcc="sub-bituminous 18.9 (11.5-26.0); lignite 11.9", physical_evidence="USGS MYB 2017-18 AP table 3: Burma 2018 coal output is lignite 1,201 kt "
                    "(no anthracite / bituminous); ADB 2016 rank description; both are rank classifications, no measured NCV",
                    proposed="main 23.26 (UNSD SDMX, decision 207 default); sensitivity 18.9 (IPCC sub-bituminous, W11 d)", main=23.26, sens=18.9)],
        "KH": [dict(commodity="Brown coal parent (industry: non-metallic minerals 252.8 kt = sub-bituminous imports; n.e.s. 77 kt = domestic lignite)", v3=14.0,
                    unsd_country=get("KH", "0200", ["1214B", "1214O", "121"]), national="Cambodia energy statistics (local copy): no coal NCV (W11 2.2)",
                    ipcc="sub-bituminous 18.9; lignite 11.9", physical_evidence="UNSD's own child rows: sub-bituminous 18.9 (imports, NMM) and lignite 11.9 "
                    "(production, n.e.s.) in the same SDMX response (parent 19.853 used for the consumption flows); GIPT KH coal rank unknown; no second independent source",
                    proposed="main 19.853 (UNSD SDMX parent, 2019 consumption flows); sensitivity children 18.9 / 11.9 (= W11 d)", main=19.853, sens="children")],
        "LA": [dict(commodity="Hard coal parent (anthracite child; industry n.e.s. 147.576 kt)", v3=25.801, unsd_country=get("LA", "0100", ["1214O", "121", "01"]),
                    national="none on disk", ipcc="anthracite 26.7", physical_evidence="USGS AP T3: Laos 2018 anthracite 143 kt (rank consistent with UNSD); no NCV",
                    proposed="main 25.121 (UNSD SDMX; = W11 inferred value, now VERIFIED); sensitivity 26.7 (child anthracite, W11 d)", main=25.121, sens=26.7),
               dict(commodity="Brown coal parent (lignite child; industry n.e.s. 160 kt, Estimate; other consumers 250 kt)", v3=14.0, unsd_country=get("LA", "0200", ["1214O", "121", "01", "08811"]),
                    national="none on disk", ipcc="lignite 11.9", physical_evidence="GIPT: all LA coal plants lignite (Hongsa); USGS AP T3 lignite 15,903 kt 2018; rank consistent, no NCV",
                    proposed="main 9.63 (UNSD SDMX; = W11 inferred value, now VERIFIED); sensitivity 11.9 (child lignite, W11 d)", main=9.63, sens=11.9)],
        "BN": [dict(commodity="Brown coal parent (lignite child): only in autoproducer transformation (Hengyi PMB), no industry coal", v3=14.0, unsd_country=get("BN", "0200", ["08812", "03"]),
                    national="none on disk; APEC 2022 sub-bituminous 22.666 (TRANSCRIBED, W11)", ipcc="sub-bituminous 18.9", physical_evidence="no industry use: no effect on T_v2",
                    proposed="no change to T_v2 (record SDMX 18.841 for W08 power-sector use)", main=None, sens=None)],
        "TL": [dict(commodity="no coal in UNSD 2019", v3=None, unsd_country=[], national="-", ipcc="-", physical_evidence="-", proposed="no coal: nothing to change", main=None, sens=None)]}
    for iso, rows in T.items():
        d = pd.DataFrame(rows)
        d["unsd_country"] = d.unsd_country.map(lambda x: ";".join(f"{v:g}" for v in x) if isinstance(x, list) else x)
        d["w11_scheme_b"] = [", ".join(f"{r.commodity}:{r.b}" for r in ref[(ref.country == iso)].itertuples() if pd.notna(r.b)) if "b" in ref.columns else "" for _ in range(len(d))]
        d.drop(columns=["main", "sens"]).to_csv(cm.G4 / f"{iso}_NCV.csv", index=False)
        out[iso] = rows
        for i, r in enumerate(rows):
            EV.put(f"ncv.{iso}.{i}.unsd_sdmx", d.unsd_country.iloc[i], "GJ/t", "UNSD SDMX CONVERSION_FACTOR 2019 (sdmx/*.xml)", "VERIFIED", "B")
            EV.put(f"ncv.{iso}.{i}.proposed", r["proposed"], "-", "decision 207 rule (A3 item 7)", "PROPOSED", "-")
    EV.put("ncv.MM.usgs_2018_lignite_kt", float(us[(us.iso == "MM") & (us.column == "lignite")].value.iloc[0]), "kt", "USGS MYB 2017-18 AP table 3, PDF p.10", "VERIFIED", "B")
    return out


def ncv_edits(u, cf):
    """Chain edits per scheme: ATS industry coal delta (MWh) and cache cell ratios (within-carrier shares), parent rows only (as the research chain)."""
    z = u[(u.year == 2019)]
    q = lambda iso, com, tr: float(z[(z.iso == iso) & (z.commodity == com) & (z.transaction == tr)].q.sum())
    K = 1e3 / 3.6   # MWh per kt per GJ/t
    rows = {
        "MM": [("iron and steel", "Hrad coal", "consumption by iron and steel industry", 25.801, {"207": 23.26, "sens_ipcc": 18.9}),
               ("non-metallic minerals", "Hard coal", "consumption by non-metallic minerals industry", 25.801, {"207": 23.26, "sens_ipcc": 18.9})],
        "KH": [("non-metallic minerals", "Brown coal", "Consumption by non-metallic minerals industry", 14.0, {"207": 19.853, "sens_child": 18.9}),
               ("other", "Brown coal", "Consumption not elsewhere specified (industry)", 14.0, {"207": 19.853, "sens_child": 11.9})],
        "LA": [("other", "Hard coal", "consumption not elsewhere specified (industry)", 25.801, {"207": 25.121, "sens_child": 26.7}),
               ("other", "Brown coal", "Consumption not elsewhere specified (industry)", 14.0, {"207": 9.63, "sens_child": 11.9})]}
    v3f = {"Hard coal": cf["Hard coal"] * 3600, "Hrad coal": cf["Hard coal"] * 3600, "Brown coal": cf["Brown coal"] * 3600}   # GJ/t of the frozen dictionary
    ed, tab = {}, []
    for scheme in ("207", "sens_ipcc", "sens_child"):
        ed[scheme] = {}
        for iso, rr in rows.items():
            e = {"ats": {"coal": 0.0}, "cache": {}}; by_sub = {}
            for sub, com, tr, _, nf in rr:
                qq = q(iso, com, tr); v3e = qq * v3f[com] * K; f = nf.get(scheme, nf["207"] if scheme != "sens_ipcc" or iso != "MM" else None)
                if scheme == "sens_ipcc" and iso != "MM":
                    f = nf["207"]
                if scheme == "sens_child" and iso == "MM":
                    f = nf["207"]
                ne = qq * f * K
                e["ats"]["coal"] += ne - v3e
                by_sub.setdefault(sub, [0.0, 0.0]); by_sub[sub][0] += v3e; by_sub[sub][1] += ne
                tab.append(dict(scheme=scheme, iso=iso, cache_subsector=sub, commodity=com, transaction=tr, kt=qq, v3_gj_per_t=v3f[com], scheme_gj_per_t=f,
                                v3_mwh=v3e, scheme_mwh=ne, delta_mwh=ne - v3e))
            e["cache"] = {("coal", s): b / a for s, (a, b) in by_sub.items()}
            ed[scheme][iso] = e
    T = pd.DataFrame(tab); T.to_csv(OUT / "NCV_EDITS_G4.csv", index=False, float_format="%.9g")
    for r in T[T.scheme == "207"].itertuples():
        EV.put(f"ncv.edit.{r.iso}.{r.cache_subsector}.{r.commodity}.delta_2019", r.delta_mwh / 1e6, "TWh", f"{r.kt} kt x ({r.scheme_gj_per_t} - {r.v3_gj_per_t:.3f}) GJ/t", "EXACT", "B")
    return {s: {iso: {"ats": e["ats"], "cache": {f"{k[0]}|{k[1]}": v for k, v in e["cache"].items()}} for iso, e in d.items()} for s, d in ed.items()}


# ------------------------------------------------------------------ 4 cement ---------------------------------------------------------------
def cement():
    p = cm.G4.parents[1] / "p1_s4r_downloads_20261020/R1_demand/myb1-2023-cemen-ERT.xlsx"
    t22 = pd.read_excel(p, sheet_name="T22", header=None, dtype=str)
    lab = {"Brunei": "BN", "Burma4": "MM", "Cambodia": "KH", "Laos": "LA"}
    us = {}
    for _, r in t22.iterrows():
        k = str(r[0]).strip()
        if k in lab:
            us[lab[k]] = {y: (float(str(r[c]).replace(",", "")), (str(r[c + 1]) if str(r[c + 1]) != "nan" else "")) for y, c in zip(range(2019, 2024), (2, 4, 6, 8, 10))}
    ed = pd.read_csv(cm.REPO / cm.EDGAR_REL); ed = ed[ed.ipcc_code_2006_for_standard_report == "2.A.1"].set_index("iso")
    ap = pd.read_csv(cm.G4 / "evidence/USGS_AP_2018_T3_G4.csv"); ap = ap[ap.column == "cement_hydraulic"].set_index("iso")
    X = cm.S2W / "extracted/02_gem_cement/gem-download (2)/Plant-level data - Global Cement and Concrete Tracker - July 2026 - Standard Copy V1.xlsx"
    g = pd.read_excel(X, sheet_name="Final data")
    iso2 = {"Brunei": "BN", "Brunei Darussalam": "BN", "Cambodia": "KH", "Laos": "LA", "Lao PDR": "LA", "Lao People's Democratic Republic": "LA", "Myanmar": "MM", "Timor-Leste": "TL"}
    g["iso"] = g["Country/area"].map(iso2); g = g[g.iso.notna()].copy()
    num = lambda s: pd.to_numeric(s.astype(str).str.replace(">", "").str.replace("<", ""), errors="coerce")
    g["cem"] = num(g["Cement capacity (million metric tonnes per annum)"]); g["clk"] = num(g["Clinker capacity (million metric tonnes per annum)"])
    keep = [c for c in g.columns if c in ("GEM plant ID", "GEM Plant ID", "Plant name (English)", "iso", "Operating status", "Plant type", "Start date", "cem", "clk", "Coordinates",
                                           "Clinker production method", "Owner name (English)")]
    g[keep].to_csv(OUT / "GEM_CEMENT_PLANTS_G4.csv", index=False)
    op = g[g["Operating status"].isin(["operating", "operating pre-retirement"])]
    ratio = 1 / 0.656; EF = 0.52
    rows = []
    for iso in cm.C5:
        e19 = float(ed.at[iso, "kt_CO2_2019"]) if iso in ed.index else 0.0; e24 = float(ed.at[iso, "kt_CO2_2024"]) if iso in ed.index else 0.0
        clk19 = e19 / EF; o = op[op.iso == iso]
        u19 = us.get(iso, {}).get(2019, (np.nan, ""))
        rows.append(dict(iso=iso, usgs_cement_2019_kt=u19[0], usgs_flag_2019=u19[1], usgs_cement_2023_kt=us.get(iso, {}).get(2023, (np.nan, ""))[0],
                         usgs_flag_2023=us.get(iso, {}).get(2023, (np.nan, ""))[1], usgs_ap_cement_2018_kt=float(ap.at[iso, "value"]) if iso in ap.index else np.nan,
                         edgar_2A1_2019_ktco2=e19, edgar_2A1_2024_ktco2=e24, clinker_2019_edgar_kt=clk19,
                         implied_clinker_ratio_2019=(clk19 / u19[0] if u19[0] and u19[0] == u19[0] else np.nan),
                         implied_clinker_ratio_2024_2023=((e24 / EF) / us[iso][2023][0] if iso in us else np.nan),
                         v3_cement_eq_2019_kt=clk19 * ratio, v3_cement_eq_over_usgs=(clk19 * ratio / u19[0] if iso in us else np.nan),
                         gem_operating_plants=int(len(o)), gem_integrated=int((o["Plant type"].astype(str).str.lower().str.contains("integrated")).sum()),
                         gem_grinding=int((o["Plant type"].astype(str).str.lower().str.contains("grinding")).sum()), gem_cement_cap_mt=float(o.cem.sum()),
                         gem_clinker_cap_mt=float(o.clk.sum()), gem_plants_with_clinker_cap=int(o.clk.notna().sum())))
    C = pd.DataFrame(rows)
    C.to_csv(OUT / "CEMENT_CLINKER_G4.csv", index=False, float_format="%.6g")
    for r in C.itertuples():
        for k in ("usgs_cement_2019_kt", "usgs_cement_2023_kt", "edgar_2A1_2019_ktco2", "clinker_2019_edgar_kt", "implied_clinker_ratio_2019", "v3_cement_eq_2019_kt",
                  "gem_operating_plants", "gem_grinding", "gem_cement_cap_mt", "gem_clinker_cap_mt"):
            x = getattr(r, k)
            if pd.notna(x):
                EV.put(f"cement.{r.iso}.{k}", x, k.split("_")[-1], {"usgs": "USGS MYB 2023 Cement T22 (myb1-2023-cemen-ERT.xlsx)", "edgar": "EDGAR 2025 2.A.1 (registry source)",
                                                                  "clinker": "EDGAR 2.A.1 / 0.52 (s3_0)", "implied": "EDGAR clinker / USGS cement", "v3": "EDGAR clinker / 0.656 (s3_0)",
                                                                  "gem": "GEM GCCT 2026-07 operating plants"}[k.split("_")[0]],
                       "VERIFIED" if k.startswith(("usgs", "edgar", "gem")) else "EXACT", "C" if (k.startswith("usgs") and "e" in str(r.usgs_flag_2019)) else "B")
    return C


# ------------------------------------------------------------------ 5 biomass ---------------------------------------------------------------
def biomass(u, sd, cf):
    fo = cm.fao("FO")
    rows = []
    keys = [("Fuelwood", "Consumption by manufacturing, construction and non-fuel industry", "121"), ("Fuelwood", "Consumption by households", "1231"),
            ("Fuelwood", "Consumption by commerce and public services", "1235"), ("Fuelwood", "Production", "01"), ("Fuelwood", "Transformation in charcoal plants", "085CH"),
            ("Bagasse", "Consumption by manufacturing, construction and non-fuel industry", "121"), ("Bagasse", "Production", "01"),
            ("Charcoal", "Production", "01"), ("Other vegetal material and residues", "Consumption by manufacturing, construction and non-fuel industry", "121"),
            ("Other vegetal material and residues", "Production", "01")]
    for iso in cm.C5:
        for com, tr, code in keys:
            se = u[(u.iso == iso) & (u.commodity == com) & (u.transaction == tr)].set_index("year")
            ss = sd[(sd.iso == iso) & (sd.commodity == com) & (sd.transaction_code == code)].set_index("year")
            if se.empty and ss.empty:
                continue
            for y in range(2005, 2023):
                rows.append(dict(iso=iso, commodity=com, transaction=tr, year=y, export_q=float(se.q.get(y, np.nan)) if not se.empty else np.nan,
                                 export_footnote=(se.footnote.get(y, "") if not se.empty else ""), sdmx_q=float(ss.value.get(y, np.nan)) if not ss.empty else np.nan,
                                 sdmx_status=(ss.obs_status.get(y, "") if not ss.empty else "")))
        f = cm.fao_series(fo, iso, "Wood fuel, non-coniferous")
        for r in f.itertuples():
            rows.append(dict(iso=iso, commodity="FAOSTAT Wood fuel, non-coniferous", transaction="Production", year=int(r.year), export_q=np.nan, export_footnote="",
                             sdmx_q=float(r.value) / 1e3, sdmx_status=f"FAO {r.flag}"))
    S = pd.DataFrame(rows); S.to_csv(OUT / "BIOMASS_SERIES_G4.csv", index=False, float_format="%.6g")
    fw = cf["Fuelwood"]; bg = cf["Bagasse"]
    g = lambda iso, com, tr, y, col="export_q": float(S[(S.iso == iso) & (S.commodity == com) & (S.transaction == tr) & (S.year == y)][col].sum())
    ind = "Consumption by manufacturing, construction and non-fuel industry"
    mm_eq = int(((S[(S.iso == "MM") & (S.commodity == "Fuelwood") & (S.transaction == ind)].set_index("year").export_q -
                  S[(S.iso == "MM") & (S.commodity == "Fuelwood") & (S.transaction == "Consumption by commerce and public services")].set_index("year").export_q).abs() < 1e-6).sum())
    facts = dict(
        MM_fuelwood_industry_2019_km3=g("MM", "Fuelwood", ind, 2019), MM_fuelwood_industry_eq_commerce_years=mm_eq,
        MM_fuelwood_industry_2022_export_km3=g("MM", "Fuelwood", ind, 2022), MM_fuelwood_industry_2022_sdmx_km3=g("MM", "Fuelwood", ind, 2022, "sdmx_q"),
        MM_fuelwood_production_2019_km3=g("MM", "Fuelwood", "Production", 2019), MM_fao_wood_fuel_2019_km3=g("MM", "FAOSTAT Wood fuel, non-coniferous", "Production", 2019, "sdmx_q"),
        MM_bagasse_industry_2019_export_kt=g("MM", "Bagasse", ind, 2019), MM_bagasse_industry_2019_sdmx_kt=g("MM", "Bagasse", ind, 2019, "sdmx_q"),
        MM_ovr_industry_2019_sdmx_tj=g("MM", "Other vegetal material and residues", ind, 2019, "sdmx_q"),
        KH_fuelwood_industry_2019_km3=g("KH", "Fuelwood", ind, 2019), KH_fuelwood_industry_2020_2022_mean_km3=np.mean([g("KH", "Fuelwood", ind, y) for y in (2020, 2021, 2022)]),
        KH_fao_wood_fuel_2019_km3=g("KH", "FAOSTAT Wood fuel, non-coniferous", "Production", 2019, "sdmx_q"), KH_fuelwood_production_2019_km3=g("KH", "Fuelwood", "Production", 2019),
        LA_fuelwood_industry_2019_km3=g("LA", "Fuelwood", ind, 2019), LA_bagasse_industry_2019_kt=g("LA", "Bagasse", ind, 2019),
        LA_fao_wood_fuel_2019_km3=g("LA", "FAOSTAT Wood fuel, non-coniferous", "Production", 2019, "sdmx_q"), LA_fuelwood_production_2019_km3=g("LA", "Fuelwood", "Production", 2019),
        BN_fuelwood_households_2019_km3=g("BN", "Fuelwood", "Consumption by households", 2019), TL_fuelwood_households_2019_km3=g("TL", "Fuelwood", "Consumption by households", 2019),
        fuelwood_twh_per_km3=fw, bagasse_twh_per_kt=bg)
    for k, x in facts.items():
        EV.put(f"biomass.{k}", x, k.split("_")[-1], "UNdata export 2025-05-02 / UNSD SDMX / FAOSTAT FO (2026-11-06 download)", "VERIFIED", "B")
    # candidate sensitivities (2019 TWh moved, 'other' bucket of the cache)
    sens = dict(
        MM_bagasse_closed_loop=("MM", "other", "biomass", facts["MM_bagasse_industry_2019_export_kt"] * bg),
        LA_bagasse_closed_loop=("LA", "other", "biomass", facts["LA_bagasse_industry_2019_kt"] * bg),
        MM_bagasse_sdmx_vintage=("MM", "other", "biomass", (facts["MM_bagasse_industry_2019_export_kt"] - facts["MM_bagasse_industry_2019_sdmx_kt"]) * bg),
        MM_ovr_5150_added=("MM", "other", "biomass", -facts["MM_ovr_industry_2019_sdmx_tj"] * TJ),
        MM_fuelwood_2022_sdmx_level=("MM", "other", "biomass", (facts["MM_fuelwood_industry_2019_km3"] - facts["MM_fuelwood_industry_2022_sdmx_km3"]) * fw),
        KH_fuelwood_2020_2022_mean=("KH", "other", "biomass", (facts["KH_fuelwood_industry_2019_km3"] - facts["KH_fuelwood_industry_2020_2022_mean_km3"]) * fw))
    for k, (iso, sub, car, d) in sens.items():
        EV.put(f"biomass.sens.{k}.d_2019_twh", d, "TWh", "2019 energy leaving (positive) or entering (negative) the 'other' biomass of the cache", "PROPOSED", "C")
    return S, facts, {k: dict(iso=v[0], sub=v[1], carrier=v[2], d_mwh=v[3] * 1e6) for k, v in sens.items()}


# ------------------------------------------------------------------ 6 products ------------------------------------------------------------
PULP_ITEMS = ["Chemical wood pulp", "Dissolving wood pulp", "Mechanical and semi-chemical wood pulp", "Pulp from fibres other than wood"]
PAPER_LEAVES = ["Newsprint", "Printing and writing papers, coated", "Printing and writing papers, uncoated, woodfree", "Printing and writing papers, uncoated, mechanical",
                "Household and sanitary papers", "Case materials", "Cartonboard", "Wrapping papers", "Other papers mainly for packaging",
                "Other paper and paperboard, not elsewhere specified"]   # = S2 v4s2_products.py


def products():
    fo = cm.fao("FO"); rows = []
    for iso in ("MM", "LA", "KH", "BN"):
        for grp, items in (("pulp", PULP_ITEMS), ("paper", PAPER_LEAVES)):
            for it in items:
                s = cm.fao_series(fo, iso, it)
                if not len(s) or s.value.dropna().empty or s.value.fillna(0).abs().sum() == 0:
                    continue
                la = cm.latest_actual(s); s19 = s[s.year == 2019]
                q19 = float(s19.value.iloc[0]) if len(s19) and pd.notna(s19.value.iloc[0]) else 0.0; f19 = str(s19.flag.iloc[0]) if len(s19) else ""
                rows.append(dict(iso=iso, group=grp, item=it, q_2019_t=q19, flag_2019=f19, base_year=la["base_year"], q_base_t=la["value"], flag_base=la["flag"], grade_base=la["grade"],
                                 latest_year=la["latest_year"], q_latest_t=la["latest_value"], growth_base=cm.growth(la["base_year"], iso),
                                 q_2050_t=la["value"] * cm.growth(la["base_year"], iso), series=";".join(f"{int(y)}:{v:.0f}{f}" for y, v, f in zip(s.year, s.value, s.flag))))
    P = pd.DataFrame(rows); P.to_csv(OUT / "PULP_PAPER_FAOSTAT_G4.csv", index=False, float_format="%.6g")
    ap = pd.read_csv(cm.G4 / "evidence/USGS_AP_2018_T3_G4.csv")
    apv = lambda iso, c: float(ap[(ap.iso == iso) & (ap.column == c)].value.sum())
    # copper: refined primary (SX-EW cathode) 2018, base year 2018 (no later value on disk), 2019 by R3, 2050 by R2; PyPSA-Eur 'Other non-ferrous metals' (v3 rule for ID copper)
    cu = {iso: dict(q2018_t=apv(iso, "copper_refined_primary") * 1e3, mine_t=apv(iso, "copper_mine_Cu") * 1e3) for iso in ("MM", "LA")}
    for iso, d in cu.items():
        d["q2019_t"] = d["q2018_t"] * cm.growth(2018, iso, 2019); d["q2050_t"] = d["q2018_t"] * cm.growth(2018, iso)
        d["e2019"] = cm.today_vec("Other non-ferrous metals", d["q2019_t"]); d["v2050"] = cm.vec2050("Other non-ferrous metals", d["q2050_t"])
    # BN chemicals (decision 202 item 4: not counted, difference table), MM ammonia, LA potash
    f = cm.S2W / "downloads/03_gem_chemicals/Plant-level-data-Global-Chemicals-Tracker-November-2026-V1.xlsx"
    pdat = pd.read_excel(f, sheet_name="Plant Data"); cap = pd.read_excel(f, sheet_name="Chemical Capacities")
    pdat["iso"] = pdat["ISO3 Code"].map({"BRN": "BN", "MMR": "MM", "LAO": "LA", "KHM": "KH", "TLS": "TL"})
    a = pdat[pdat.iso.notna()][["GEM Plant ID", "Plant Name (English)", "iso", "Operating Status", "Start Date | Year", "Primary Products", "Feedstock", "Coordinates"]]
    c = cap.merge(a, on="GEM Plant ID"); c["cap"] = pd.to_numeric(c["Capacity (ttpa)"], errors="coerce")
    c.to_csv(OUT / "GEM_CHEMICALS_G4.csv", index=False)
    rm = pd.read_csv(cm.S2W / "V4_PRODUCT_ROUTE_MAP.csv").set_index("product")
    bat = {"methanol": "methanol", "ammonia": "ammonia", "olefins": "olefins (ethylene, propylene)", "aromatics": "aromatics"}
    U = 0.85   # explicit utilisation assumption (as S2 ethylene central), grade C
    B = c[(c.iso == "BN") & c["Capacity Status"].eq("operating") & c.cap.notna()].copy()
    B["start_year"] = pd.to_numeric(B["Start Date | Year"], errors="coerce")
    B["bat_energy_gj_per_t"] = [float(rm.at[bat[g_], "bat_electricity_gj_per_t"]) + float(rm.at[bat[g_], "bat_fuel_or_heat_gj_per_t"]) for g_ in B["Product Group"]]
    B["bat_feedstock_gj_per_t"] = [float(rm.at[bat[g_], "bat_feedstock_gj_per_t"]) for g_ in B["Product Group"]]
    B["operating_2019"] = B.start_year <= 2019
    B["energy_use_2019_twh"] = np.where(B.operating_2019, B.cap * 1e3 * U * B.bat_energy_gj_per_t / 3.6 / 1e6, 0.0)
    B["energy_use_at_capacity_u085_twh"] = B.cap * 1e3 * U * B.bat_energy_gj_per_t / 3.6 / 1e6
    B["feedstock_at_capacity_u085_twh"] = B.cap * 1e3 * U * B.bat_feedstock_gj_per_t / 3.6 / 1e6
    B.to_csv(OUT / "BN_CHEMICALS_DIFFERENCE_G4.csv", index=False, float_format="%.6g")
    mm_nh3 = apv("MM", "nitrogen_N_content_of_ammonia") * 1e3 * 17 / 14   # t NH3 (2018)
    la_k2o = apv("LA", "potash_K2O") * 1e3
    for iso, d in cu.items():
        for k in ("q2018_t", "mine_t", "q2019_t", "q2050_t"):
            EV.put(f"products.copper.{iso}.{k}", d[k], "t", "USGS MYB 2017-18 AP T3 (PDF p.6) refined primary copper; R3 / R2 growth", "VERIFIED" if k in ("q2018_t", "mine_t") else "INFERENCE", "B" if k in ("q2018_t", "mine_t") else "C")
    EV.put("products.MM.ammonia_2018_t", mm_nh3, "t NH3", "USGS AP T3 (PDF p.10) N content of ammonia 53 kt x 17/14", "VERIFIED", "B")
    EV.put("products.LA.potash_2018_t_K2O", la_k2o, "t K2O", "USGS AP T3 (PDF p.10)", "VERIFIED", "B")
    EV.put("products.BN.chem_energy_use_2019_twh", float(B.energy_use_2019_twh.sum()), "TWh", "GEM capacity x 0.85 x ETSAP BAT energy (start year <= 2019)", "INFERENCE", "C")
    EV.put("products.BN.chem_energy_use_at_capacity_twh", float(B.energy_use_at_capacity_u085_twh.sum()), "TWh", "GEM operating capacity x 0.85 x ETSAP BAT energy", "INFERENCE", "C")
    return P, cu, B, mm_nh3, la_k2o


def product_inputs(P, cu):
    """2019 deductions (S1 / S2 today convention) and 2050 vectors (PyPSA-Eur 2050) of the explicit products of the main case; closed-loop rule
    (decision 206 item 3): pulp and paper count only the electricity and heat of the PyPSA-Eur structure, the biomass part is listed separately."""
    res = {}

    def pp(iso, grp, case):
        z = P[(P.iso == iso) & (P.group == grp)]
        q19 = float(z.q_2019_t.sum()); q50 = float(z.q_2050_t.sum()) if case == "base_rule" else 0.0
        sec = "Pulp production" if grp == "pulp" else "Paper production"
        e19 = cm.today_vec(sec, q19); v50 = cm.vec2050(sec, q50)
        return dict(q2019_t=q19, q2050_t=q50, sector=sec, e2019=e19, v2050=v50)
    res["MM_paper"] = pp("MM", "paper", "base_rule"); res["MM_pulp"] = pp("MM", "pulp", "base_rule")
    res["LA_pulp"] = pp("LA", "pulp", "base_rule")
    z = P[(P.iso == "LA") & (P.group == "paper")]
    q50 = float(z.q_2050_t.sum())
    res["LA_paper_R4"] = dict(q2019_t=0.0, q2050_t=q50, sector="Paper production", e2019=cm.today_vec("Paper production", 0.0), v2050=cm.vec2050("Paper production", q50))
    for iso in ("MM", "LA"):
        res[f"{iso}_copper"] = dict(q2019_t=cu[iso]["q2019_t"], q2050_t=cu[iso]["q2050_t"], sector="Other non-ferrous metals", e2019=cu[iso]["e2019"], v2050=cu[iso]["v2050"])
    for k, d in res.items():
        closed = "pulp" in k or "paper" in k
        d["closed_loop"] = closed
        d["e2019_purchased_el"] = d["e2019"]["elec"]
        d["e2019_purchased_fuel"] = sum(v for c_, v in d["e2019"].items() if c_ not in ("elec",) and not (closed and c_ == "biomass"))
        d["e2019_closed_loop_biomass"] = d["e2019"]["biomass"] if closed else 0.0
        d["v2050_counted"] = {c_: (0.0 if (closed and c_ == "biomass") else v) for c_, v in d["v2050"].items()}
        d["v2050_closed_loop_biomass"] = d["v2050"]["biomass"] if closed else 0.0
        for kk in ("q2019_t", "q2050_t", "e2019_purchased_el", "e2019_purchased_fuel", "e2019_closed_loop_biomass", "v2050_closed_loop_biomass"):
            EV.put(f"products.{k}.{kk}", d[kk] / (1e6 if kk.startswith(("e", "v")) else 1.0), "TWh" if kk.startswith(("e", "v")) else "t",
                   f"{d['sector']}: JRC-IDEES EU27 2019 today total x PyPSA-Eur structure (2019); PyPSA-Eur 2050 ratio (2050)", "INFERENCE", "C")
        EV.put(f"products.{k}.v2050_counted_twh", sum(d["v2050_counted"].values()) / 1e6, "TWh", "PyPSA-Eur 2050 ratio, closed-loop biomass excluded", "PROPOSED", "C")
    return res


def main():
    cf = cm.conv_factors()
    u = cm.unsd_export(); sd = cm.sdmx()
    z, C = national(u, sd, cf)
    scr, M, capf = captive(u)
    ncv = ncv_tables(sd); ned = ncv_edits(u, cf)
    cem = cement()
    S, bfacts, bsens = biomass(u, sd, cf)
    P, cu, B, mm_nh3, la_k2o = products()
    prod = product_inputs(P, cu)
    cem_t19 = {r.iso: r.usgs_cement_2019_kt * 1e3 for r in cem.itertuples() if pd.notna(r.usgs_cement_2019_kt)}
    ci = dict(ncv=ned, captive_MM={r.level: dict(C_kt=r.coal_kt, E_mwh=r.gen_twh * 1e6, C_mwh_v3=r.c_twh_v3 * 1e6, C_mwh_207=r.c_twh_207 * 1e6) for r in M.itertuples()},
              cement_usgs_2019_t=cem_t19, biomass_sens=bsens,
              products={k: {kk: v for kk, v in d.items() if kk in ("q2019_t", "q2050_t", "sector", "closed_loop", "e2019_purchased_el", "e2019_purchased_fuel",
                                                                    "e2019_closed_loop_biomass", "v2050_counted", "v2050_closed_loop_biomass")} for k, d in prod.items()},
              mm_ammonia_2018_t=mm_nh3, la_potash_2018_t_k2o=la_k2o)
    cm.jdump(ci, OUT / "_chain_inputs.json")
    EV.write(OUT / "_facts_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(C[~C.note.str.startswith("equal")].drop(columns=["transaction"]).to_string(index=False)[:6000])
    print(M.drop(columns=["hours_source", "heat_rate_source", "mw_source"]).round(4).to_string(index=False))
    print(cem.round(3).T.to_string())
    print(P[["iso", "group", "item", "q_2019_t", "flag_2019", "base_year", "q_base_t", "flag_base", "q_2050_t"]].to_string(index=False))
    print({k: (round(v["q2019_t"]), round(v["q2050_t"]), round(v["e2019_purchased_el"] / 1e6, 4), round(v["e2019_purchased_fuel"] / 1e6, 4),
               round(sum(v["v2050_counted"].values()) / 1e6, 4), round(v["v2050_closed_loop_biomass"] / 1e6, 4)) for k, v in prod.items()})
    print(B[["Plant Name (English)", "Product Group", "Product", "cap", "start_year", "operating_2019", "energy_use_2019_twh", "energy_use_at_capacity_u085_twh"]].to_string(index=False))
    print({k: round(v, 4) for k, v in bfacts.items()})
    print({k: round(v["d_mwh"] / 1e6, 4) for k, v in bsens.items()})
    print(json.dumps(ned["207"], indent=0)[:1500])


if __name__ == "__main__":
    main()
