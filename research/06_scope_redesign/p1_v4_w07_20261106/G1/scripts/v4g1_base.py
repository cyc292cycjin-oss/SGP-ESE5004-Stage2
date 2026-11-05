"""V4 W07 G1 steps 0-1 (Malaysia): reproduction of the repository MY row in a scratch copy of the data chain, and the national statistics base.

    PYTHONHASHSEED=0 python scripts/v4g1_base.py        (WSL pypsa-earth python)

0  Scratch copy /home/jin/v4w07_g1/chain (research_inputs + scripts_project of the worktree). The unmodified copy must reproduce the repository MY
   heat-band summary row (T_v2 carriers) and the v3 'other' bucket of INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv to 0 MWh; the cement patch without its
   environment variable must give the same row. Otherwise STOP (A1).
1  UNSD 2019 Malaysia, every industry / transformation / own-use / non-energy flow of the UNdata export used by the model (2025-05-02) next to the
   UNSD SDMX response of this session (G1/sdmx, CONVERSION_FACTOR per observation), with the frozen upstream conversion of the model; series
   2005-2022 of the rows that make the MY industry base, with year-on-year jumps flagged; the Malaysian National Energy Balance 2019 (Energy
   Commission; PDF on disk, text from the W11 extraction, page numbers = PDF pages): table 29 balance rows, table 7 gas by region, table 9 coal by
   region, table 10 co-generation and self-generation capacity, table 17 electricity by region.
Outputs tables/MY_UNSD_2019_ROWS.csv, MY_SERIES.csv, MY_NEB_2019_VALUES.csv, tables/_base_evidence.json. Nothing is solved; the repository is not written.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g1_common as cm   # noqa: E402

OUT = cm.G1 / "tables"
FLOWS_2019 = ("consumption by", "industr", "autoproducer", "transformation", "own use", "non-energy", "production", "total net installed")


def twh(commodity: str, unit: str, q: float, conv: dict) -> float:
    """Model conversion (reconstruct_base_accounts.py): TJ / 3.6 (natural gas x 0.90), GWh / 1000, physical units x frozen TWh/kt."""
    c = commodity.lower()
    if "terajoule" in unit.lower():
        return q / 3.6 / 1e3 * (0.9 if c.startswith("natural gas") else 1.0)
    if "kilowatt-hours" in unit.lower():
        return q / 1e3
    for k, v in conv.items():
        if k.lower() == c or (k.lower() == "hard coal" and c in ("hard coal", "hrad coal")):
            return q * float(v)
    return np.nan


def reproduce(ev):
    v3 = cm.import_v3(); fut = v3.future_vectors(); ne = v3.nickel_unit_energy()
    nf = v3.nonferrous(fut, "main", ne)[0].get(cm.CC, {})
    ch = cm.Chain(); ch.copy()
    row, ob, pz = ch.run()
    repo_row = pd.read_csv(cm.REPO / "research_inputs/demand_v5" / cm.SUMMARY).set_index("country").loc[cm.CC]
    dev = max(abs(float(row[v3.col(x)]) - float(repo_row[v3.col(x)])) for x in v3.CARRIERS)
    L = cm.v3_layer(v3, row, fut, nf)
    sub = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
    sub = sub[(sub.case == "main") & (sub.country == cm.CC)]
    so = sub[sub.subsector == "other"].set_index("carrier").mwh_2050
    dev3 = max(abs(L["other"].get(k, 0.0) - float(so.get(k, 0.0))) for k in set(L["other"]) | set(so.index))
    ch.patch(); row_p, _, _ = ch.run()
    dev_p = max(abs(float(row_p[v3.col(x)]) - float(row[v3.col(x)])) for x in v3.CARRIERS)
    ch.unpatch(); ch.restore()
    rep = dict(max_abs_dev_T_carriers_mwh=dev, max_abs_dev_v3_other_mwh=dev3, max_abs_dev_patched_no_env_mwh=dev_p, T_v2_twh=L["T"] / 1e6,
               other_twh=L["other_total"] / 1e6, other_share=L["other_total"] / L["T"], explicit_twh=L["explicit"] / 1e6,
               by_sub_twh={k: v / 1e6 for k, v in L["by_sub"].items()}, other_2019_v2_twh=float(ob.other_2019_mwh) / 1e6,
               industry_2019_twh=float(ob.industry_2019_mwh) / 1e6, multiplier=float(ob.industry_multiplier))
    if dev > 1e-3 or dev3 > 1e-3 or dev_p > 1e-3:
        raise SystemExit(f"STOP: the unmodified scratch copy does not reproduce the repository MY row ({rep})")
    for k, v in rep.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                ev.put(f"reproduction.by_sub.{kk}", vv, "TWh", "scratch chain v3 layer (= INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv main)", "EXACT", "C")
        else:
            ev.put(f"reproduction.{k}", v, "MWh" if k.endswith("mwh") else ("-" if k in ("other_share", "multiplier") else "TWh"),
                   "scratch copy /home/jin/v4w07_g1/chain vs repository worktree", "EXACT", "-")
    pzs = pz.groupby("subsector").mwh_2019.sum() / 1e6
    for k, v in pzs.items():
        ev.put(f"s3_0_2019.{k}", v, "TWh", "s3_0 INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv mwh_2019 (MY)", "EXACT", "C")
    for c in cm.CARS19:
        ev.put(f"other_2019_v2.{c}", float(ob[f"other_2019_{c}_mwh"]) / 1e6, "TWh", "INDUSTRY_2050_OTHER_BUCKET.csv (aeo8_ats_anchor, MY)", "EXACT", "B")
    return rep


def unsd_rows(ev):
    conv = cm.frozen_conv()
    U, notes = cm.unsd_export()
    y = U[U.y == 2019].copy()
    t = y.transaction.str.lower()
    y = y[t.str.contains("|".join(FLOWS_2019))].copy()
    y["twh_model_conversion"] = [twh(c, u, q, conv) for c, u, q in zip(y.commodity, y.Unit, y.q)]
    y["source"] = "UNdata export 2025-05-02 (" + y.file + ")"
    E = y[["commodity", "transaction", "Unit", "q", "twh_model_conversion", "footnote", "source"]].rename(columns={"Unit": "unit", "q": "quantity"})
    S = pd.read_csv(cm.G1 / "sdmx/MY_SDMX_OBS.csv", dtype={"commodity_code": str, "transaction_code": str})
    S = S[(S.year == 2019) & (S.file == "MY_2019_all.xml")].copy()
    sel = S.transaction.fillna("").str.lower().str.contains("|".join(FLOWS_2019 + ("blast", "chp")))
    S = S[sel].copy()
    S["source"] = "UNSD SDMX DF_UNDATA_ENERGY (G1/sdmx/MY_2019_all.xml, " + json.loads((cm.G1 / "sdmx/MY_2019_all.xml.receipt.json").read_text())["utc"][:10] + ")"
    S["energy_tj_sdmx"] = np.where(S.unit.eq("TJ"), S.value, np.where(S.unit.eq("GWHR"), S.value * 3.6, S.value * S.conversion_factor))
    S2 = S[["commodity", "transaction", "unit", "value", "obs_status", "conversion_factor", "energy_tj_sdmx", "source"]].rename(columns={"value": "quantity", "obs_status": "footnote"})
    R = pd.concat([E.assign(dataset="export"), S2.assign(dataset="sdmx")], ignore_index=True)
    R.to_csv(OUT / "MY_UNSD_2019_ROWS.csv", index=False, float_format="%.12g")
    # ---- key rows (export = model) and export vs SDMX differences
    def q_e(com, tr):
        z = E[(E.commodity.str.lower() == com.lower()) & (E.transaction.str.lower() == tr.lower())]
        return float(z.quantity.iloc[0]) if len(z) else np.nan

    def q_s(com, tr_code):
        z = pd.read_csv(cm.G1 / "sdmx/MY_SDMX_OBS.csv", dtype={"commodity_code": str, "transaction_code": str})
        z = z[(z.year == 2019) & (z.file == "MY_2019_all.xml") & (z.commodity == com) & (z.transaction_code == tr_code)]
        return float(z.value.iloc[0]) if len(z) else np.nan
    keys = [("Natural gas (including LNG)", "consumption by manufacturing, construction and non-fuel industry", "Natural Gas (including LNG)", "121", "TJ"),
            ("Natural gas (including LNG)", "non-energy uses", "Natural Gas (including LNG)", "11", "TJ"),
            ("Natural Gas (including LNG)", "transformation in electricity plants - autoproducers", "Natural Gas (including LNG)", "08812", "TJ"),
            ("Electricity", "Consumption by manufacturing, construction and non-fuel industry", "Total Electricity", "121", "GWh"),
            ("Hard coal", "consumption by non-metallic minerals industry", "Hard Coal", "1214H", "kt"),
            ("Blast Furnace Gas", "Consumption by iron and steel", "Blast Furnace Gas", "1211", "TJ"),
            ("Coke-oven coke", "transformation in blast furnaces", "Coke Oven Coke", "082", "kt"),
            ("Gas Oil/ Diesel Oil", "Consumption by manufacturing, construction and non-fuel mining industry", "Gas Oil/ Diesel Oil", "121", "kt"),
            ("Fuel oil", "Consumption by manufacturing, construction and non-fuel industry", "Fuel Oil", "121", "kt"),
            ("Liquefied petroleum gas (LPG)", "consumption by manufacturing, construction and non-fuel mining industry", "Liquified Petroleum Gas", "121", "kt"),
            ("Motor Gasoline", "Consumption by manufacturing, construction and non-fuel mining industry", "Motor Gasoline", "121", "kt"),
            ("Bagasse", "Consumption by manufacturing, construction and non-fuel industry", "Bagasse", "121", "kt")]
    for ce, te, cs, ts, unit in keys:
        a = q_e(ce, te)
        ev.put(f"unsd2019.export.{ce}.{te}", a, unit, "UNdata export 2025-05-02 (model source)", "VERIFIED", "B")
    # SDMX-only items in industry (coverage of the export, W11 / W12 item 4)
    Sx = pd.read_csv(cm.G1 / "sdmx/MY_SDMX_OBS.csv", dtype={"commodity_code": str, "transaction_code": str})
    Sx = Sx[(Sx.year == 2019) & (Sx.file == "MY_2019_all.xml") & (Sx.transaction_code == "121")]
    diffs = []
    for r in Sx.itertuples():
        ce = {"Natural Gas (including LNG)": "Natural gas (including LNG)", "Total Electricity": "Electricity", "Hard Coal": "Hard coal",
              "Liquified Petroleum Gas": "Liquefied petroleum gas (LPG)", "Fuel Oil": "Fuel oil"}.get(r.commodity, r.commodity)
        z = E[(E.commodity.str.lower() == ce.lower()) & E.transaction.str.lower().str.startswith("consumption by manufacturing")]
        qe = float(z.quantity.iloc[0]) if len(z) else 0.0
        tj = r.value * (r.conversion_factor if r.unit == "TN" else (3.6 if r.unit == "GWHR" else 1.0))
        diffs.append(dict(commodity=r.commodity, unit=r.unit, sdmx=r.value, export=qe, diff=r.value - qe, conversion_factor=r.conversion_factor, diff_tj=(r.value - qe) * (r.conversion_factor if r.unit == "TN" else (3.6 if r.unit == "GWHR" else 1.0))))
    Dd = pd.DataFrame(diffs)
    Dd.to_csv(OUT / "MY_UNSD_EXPORT_VS_SDMX_INDUSTRY_2019.csv", index=False, float_format="%.12g")
    for r in Dd.itertuples():
        ev.put(f"unsd2019.industry_sdmx_minus_export.{r.commodity}", r.diff, r.unit, "SDMX 2019 (this session) minus UNdata export 2025-05-02, flow 121 manufacturing/construction/non-fuel industry", "VERIFIED", "B")
        ev.put(f"unsd2019.industry_sdmx_minus_export_twh.{r.commodity}", r.diff_tj / 3600.0, "TWh", "same, x SDMX conversion factor", "EXACT", "B")
    ev.extra["footnote_legend"] = notes
    return U, E, Dd


def series_rows(U, ev):
    conv = cm.frozen_conv()
    spec = [("gas industry n.e.s.", "Natural gas (including LNG)", ["consumption by manufacturing, construction and non-fuel industry", "consumption by industries not elsewhere specified"]),
            ("gas non-energy", "Natural gas (including LNG)", ["non-energy uses"]),
            ("electricity industry", "Electricity", ["Consumption by manufacturing, construction and non-fuel industry"]),
            ("hard coal non-metallic minerals", "Hard coal", ["consumption by non-metallic minerals industry"]),
            ("hard coal industry total", "Hard coal", ["consumption by manufacturing, construction and non-fuel mining industry", "consumption by manufacturing, construction and non-fuel industry"]),
            ("blast furnace gas iron and steel", "Blast Furnace Gas", ["Consumption by iron and steel"]),
            ("coke into blast furnaces", "Coke-oven coke", ["transformation in blast furnaces"]),
            ("diesel industry", "Gas Oil/ Diesel Oil", ["Consumption by manufacturing, construction and non-fuel mining industry"]),
            ("fuel oil industry", "Fuel oil", ["Consumption by manufacturing, construction and non-fuel industry"]),
            ("bagasse industry", "Bagasse", ["Consumption by manufacturing, construction and non-fuel industry"]),
            ("fuelwood households", "Fuelwood", ["Consumption by households"]),
            ("autoproducer electricity", "Electricity", ["total production, autoproducer"]),
            ("autoproducer gas", "Natural Gas (including LNG)", ["transformation in electricity plants - autoproducers"])]
    rows = []
    for label, com, trs in spec:
        z = U[(U.commodity.str.lower() == com.lower()) & U.transaction.str.lower().isin([t.lower() for t in trs]) & U.y.between(2005, 2022)]
        z = z.sort_values(["y"]).drop_duplicates(subset=["y"], keep="first")
        for r in z.itertuples():
            rows.append(dict(series=label, commodity=r.commodity, transaction=r.transaction, year=r.y, quantity=r.q, unit=r.Unit, footnote=r.footnote,
                             twh_model_conversion=twh(r.commodity, r.Unit, r.q, conv)))
    S = pd.DataFrame(rows).sort_values(["series", "year"])
    S["yoy_change"] = S.groupby("series").quantity.pct_change()
    S["jump_flag"] = S.yoy_change.abs() > 0.3
    S.to_csv(OUT / "MY_SERIES.csv", index=False, float_format="%.10g")
    for r in S[S.jump_flag].itertuples():
        ev.put(f"series.jump.{r.series}.{r.year}", r.yoy_change, "-", "UNdata export: year-on-year change > 30 %", "VERIFIED", "B")
    return S


def neb(ev):
    if cm.sha256(cm.NEB_PDF) != cm.NEB_PDF_SHA:
        raise ValueError("NEB 2019 PDF SHA256 differs from the W11 text index")
    V = []

    def put(table, page, item, col, val, unit):
        V.append(dict(table=table, pdf_page=page, item=item, column=col, value=val, unit=unit))
    # ---- table 29 energy balance (ktoe), PDF page 72
    cols29 = ["natural gas", "LNG", "crude oil", "others", "total petroleum products", "petrol", "diesel", "fuel oil", "LPG", "kerosene", "ATF & AV gas",
              "non-energy", "refinery gas", "coal & coke", "hydropower", "solar", "biomass", "biogas", "biodiesel", "electricity", "total"]
    txt = cm.neb_page(72)
    pats = {"17. Industry": "industry", "21. Non-Energy Use": "non-energy use", "11.3 Self-Generation (5/)": "self-generation",
            "11.2 Thermal Stations": "thermal stations", "22.  Total Final Use": "total final use"}
    for ln in txt.splitlines():
        for p, lab in pats.items():
            if ln.strip().startswith(p):
                nums = cm.neb_numbers(ln.strip()[len(p):])
                if len(nums) != 21:
                    raise ValueError(f"table 29 {lab}: {len(nums)} numbers")
                for c, v in zip(cols29, nums):
                    put("29 energy balance 2019", 72, lab, c, v, "ktoe")
    gl = [ln for ln in txt.splitlines() if ln.startswith("GWh ")]
    if len(gl) != 2:
        raise ValueError("table 29: gross generation lines")
    for lab, ln in zip(("main activity gross generation", "autoproducer gross generation"), gl):
        nums = cm.neb_numbers(ln[4:])
        if len(nums) != 21:
            raise ValueError(f"table 29 {lab}: {len(nums)}")
        for c, v in zip(cols29, nums):
            put("29 energy balance 2019", 72, lab, c, v, "GWh")
    # ---- table 7 natural gas consumption by sector and region (MMscf), PDF page 40
    txt = cm.neb_page(40)
    for sec in ("Residential", "Commercial", "Industry", "Non-Energy", "Transport", "Power Stations", "Co-Generation", "Total"):
        ln = [x for x in txt.splitlines() if x.startswith(sec + " ")][0]
        nums = cm.neb_numbers(ln[len(sec):])
        if len(nums) != 4:
            raise ValueError(f"table 7 {sec}: {nums}")
        for c, v in zip(("Peninsular Malaysia", "Sabah", "Sarawak", "Malaysia"), nums):
            put("7 natural gas consumption 2019", 40, sec.lower(), c, v, "MMscf")
    # ---- table 9 coal consumption by region (t), PDF page 46
    txt = cm.neb_page(46)
    for sec in ("Industry", "Power Stations"):
        ln = [x for x in txt.splitlines() if x.startswith(sec + " ")][0]
        nums = cm.neb_numbers(ln[len(sec):])
        for c, v in zip(("Peninsular Malaysia", "Sabah", "Sarawak", "Malaysia"), nums):
            put("9 coal consumption 2019", 46, sec.lower(), c, v, "t")
    # ---- table 10 installed capacity 31 Dec 2019 (MW), PDF page 50: co-generation and self-generation by region
    cols10 = ["hydro", "natural gas", "coal", "diesel", "biomass", "solar", "biogas", "others", "total"]
    txt = cm.neb_page(50).splitlines(); region = None
    for ln in txt:
        s = ln.strip()
        if s in ("PENINSULAR MALAYSIA", "SABAH", "SARAWAK"):
            region = s.title()
        for sec in ("Co-Generation", "Self-Generation"):
            if s.startswith(sec + " ") and region:
                nums = cm.neb_numbers(s[len(sec):])
                if len(nums) != 9:
                    raise ValueError(f"table 10 {region} {sec}: {nums}")
                for c, v in zip(cols10, nums):
                    put("10 installed capacity 2019", 50, f"{sec.lower()} {region}", c, v, "MW")
    # ---- table 17 electricity consumption by sector and region (GWh), PDF page 57
    txt = cm.neb_page(57)
    m = re.search(r"PENINSULAR\s+MALAYSIA\s+([\d,]+)\s+[\d.]+\s+([\d,]+)\s+[\d.]+\s+([\d,]+)", txt)
    for reg, pat in (("Peninsular Malaysia", r"PENINSULAR\s+MALAYSIA\s+([\d,]+)"), ("Sarawak", r"SARAWAK\s+([\d,]+)"), ("Sabah", r"SABAH\s+([\d,]+)"), ("Malaysia", r"TOTAL\s+([\d,]+)\s+100\.0")):
        mm = re.search(pat, txt)
        put("17 electricity consumption 2019", 57, "industry", reg, float(mm.group(1).replace(",", "")), "GWh")
    # ---- table 29 imports row (coal & coke) and figure 25 industry coal series 1990-2019 (ktoe), PDF pages 72 and 48
    ln = [x for x in cm.neb_page(72).splitlines() if x.startswith("3. Imports")][0]
    for c, v in zip(cols29, cm.neb_numbers(ln[len("3. Imports"):])):
        put("29 energy balance 2019", 72, "imports", c, v, "ktoe")
    f25 = [x for x in cm.neb_page(48).splitlines() if x.startswith("513 599 672")]
    if len(f25) != 1:
        raise ValueError("figure 25 industry series not found")
    for y, v in zip(range(1990, 2020), cm.neb_numbers(f25[0])):
        put("figure 25 coal consumption by sectors", 48, "industry", str(y), v, "ktoe")
    N = pd.DataFrame(V)
    N.to_csv(OUT / "MY_NEB_2019_VALUES.csv", index=False, float_format="%.10g")
    g = lambda t, i, c: float(N[(N.table.str.startswith(t)) & (N["item"] == i) & (N.column == c)].value.iloc[0])
    # ---- checks against the UNSD / D1 base
    d1 = pd.read_csv(cm.REPO / cm.D1_REL); d1 = d1[(d1.country == cm.CC) & (d1.sector == "Industry")].set_index("carrier").base_2019_mwh.astype(float) / 1e6
    chk = dict(industry_gas_twh=g("29", "industry", "natural gas") * cm.MWH_PER_TOE / 1e3, industry_electricity_twh=g("29", "industry", "electricity") * cm.MWH_PER_TOE / 1e3,
               industry_petroleum_twh=g("29", "industry", "total petroleum products") * cm.MWH_PER_TOE / 1e3, industry_coal_coke_twh=g("29", "industry", "coal & coke") * cm.MWH_PER_TOE / 1e3,
               industry_total_twh=g("29", "industry", "total") * cm.MWH_PER_TOE / 1e3, industry_biomass_ktoe=g("29", "industry", "biomass"),
               selfgen_gas_input_twh=-g("29", "self-generation", "natural gas") * cm.MWH_PER_TOE / 1e3, selfgen_biomass_input_twh=-g("29", "self-generation", "biomass") * cm.MWH_PER_TOE / 1e3,
               selfgen_biogas_input_twh=-g("29", "self-generation", "biogas") * cm.MWH_PER_TOE / 1e3, selfgen_diesel_input_twh=-g("29", "self-generation", "diesel") * cm.MWH_PER_TOE / 1e3,
               selfgen_output_gwh=g("29", "autoproducer gross generation", "total"), selfgen_gas_output_gwh=g("29", "autoproducer gross generation", "natural gas"),
               selfgen_biomass_output_gwh=g("29", "autoproducer gross generation", "biomass"), neu_gas_twh=g("29", "non-energy use", "natural gas") * cm.MWH_PER_TOE / 1e3)
    chk.update(d1_gas_twh=float(d1["gas"]), d1_electricity_twh=float(d1["electricity"]), d1_oil_twh=float(d1["oil"]), d1_coal_twh=float(d1["coal"]), d1_biomass_twh=float(d1["biomass"]))
    gas_t = g("7", "industry", "Malaysia")
    for reg in ("Peninsular Malaysia", "Sabah", "Sarawak"):
        chk[f"industry_gas_share_{reg}"] = g("7", "industry", reg) / gas_t
        chk[f"industry_gas_twh_{reg}"] = g("7", "industry", reg) / gas_t * chk["industry_gas_twh"]
        chk[f"neu_gas_twh_{reg}"] = g("7", "non-energy", reg) / g("7", "non-energy", "Malaysia") * chk["neu_gas_twh"]
        chk[f"cogeneration_gas_mmscf_{reg}"] = g("7", "co-generation", reg)
        chk[f"industry_electricity_share_{reg}"] = g("17", "industry", reg) / g("17", "industry", "Malaysia")
        chk[f"industry_coal_t_{reg}"] = g("9", "industry", reg)
    chk["industry_coal_t_minus_unsd_nmm_coal_and_bf_coke_t"] = g("9", "industry", "Malaysia") - 1232691 - 1474024
    # NEB coal & coke imports (ktoe) against UNSD imports of hard coal and coke at the SDMX factors: does the NEB industry coal include the BF coke?
    TOE = 41.868
    chk["neb_imports_coal_coke_ktoe"] = g("29", "imports", "coal & coke")
    chk["unsd_imports_hard_coal_plus_coke_ktoe_at_sdmx_ncv"] = (29655.4 * 26.394 + 1474.024 * 26.377) / TOE
    chk["unsd_imports_hard_coal_only_ktoe_at_sdmx_ncv"] = 29655.4 * 26.394 / TOE
    chk["neb_industry_coal_coke_ktoe_minus_2706669t_at_26394"] = g("29", "industry", "coal & coke") - 2706.669 * 26.394 / TOE
    U = cm.unsd_export()[0]
    nmm = U[(U.commodity.str.lower() == "hard coal") & (U.transaction.str.lower() == "consumption by non-metallic minerals industry")].drop_duplicates("y").set_index("y").q
    for y in range(2012, 2020):
        f25v = float(N[(N.table.str.startswith("figure 25")) & (N.column == str(y))].value.iloc[0])
        chk[f"neb_fig25_industry_coal_{y}_kt_at_26394"] = f25v * TOE / 26.394
        chk[f"unsd_nmm_hard_coal_{y}_kt"] = float(nmm.get(y, np.nan))
    chk["cogeneration_gas_mw"] = sum(g("10", f"co-generation {r}", "natural gas") for r in ("Peninsular Malaysia", "Sabah", "Sarawak"))
    chk["selfgeneration_biomass_mw"] = sum(g("10", f"self-generation {r}", "biomass") for r in ("Peninsular Malaysia", "Sabah", "Sarawak"))
    chk["cogeneration_biomass_mw"] = sum(g("10", f"co-generation {r}", "biomass") for r in ("Peninsular Malaysia", "Sabah", "Sarawak"))
    for k, v in chk.items():
        st = "VERIFIED" if k.startswith(("d1_", "industry_coal_t_P", "industry_coal_t_S", "cogeneration_gas_mmscf")) or k.endswith(("_ktoe", "_gwh")) else "EXACT"
        ev.put(f"neb2019.{k}", v, "-" if "share" in k else ("TWh" if k.endswith("twh") else ("t" if "_t_" in k or k.endswith("_t") else ("MW" if k.endswith("_mw") else ("GWh" if k.endswith("gwh") else ("ktoe" if k.endswith("ktoe") else "MMscf"))))),
               "Energy Commission, National Energy Balance 2019 (PDF pages 40, 46, 50, 57, 72; ktoe x 11.63 MWh)" + (" / repository D1 table" if k.startswith("d1_") else ""), st, "A" if not k.startswith("d1_") else "B")
    return N, chk


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ev = cm.Ev("base")
    rep = reproduce(ev)
    U, E, Dd = unsd_rows(ev)
    S = series_rows(U, ev)
    N, chk = neb(ev)
    ev.extra.update(reproduction=rep, neb_checks=chk)
    ev.write(OUT / "_base_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    print(json.dumps(rep, indent=1)); print(json.dumps(chk, indent=1))
    print(Dd.round(3).to_string())
    print(S[S.jump_flag][["series", "year", "quantity", "yoy_change", "footnote"]].to_string())


if __name__ == "__main__":
    main()
