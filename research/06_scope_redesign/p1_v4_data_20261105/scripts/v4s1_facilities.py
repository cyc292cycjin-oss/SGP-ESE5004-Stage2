"""V4 S1 section 2: Indonesian steel and cement at facility level (GEM GIST 2026-09, GEM GCCT 2026-07).

    PYTHONHASHSEED=0 python scripts/v4s1_facilities.py --work <work dir> --repo /home/jin/wt_v4_data \
        --main /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model --chain /home/jin/v4s1/chain_cement     (WSL pypsa-earth python)

1. Facility tables s1/ID_STEEL_FACILITIES.csv (one row per GEM capacity line) and s1/ID_CEMENT_FACILITIES.csv (one row per plant), operating in
   2019 / 2024 (2023 for cement) from status and start / retired / idled dates; every value with file, sheet, column and version.
2. Activity (decision 202 item 1): plant production where GEM reports it, else capacity x u, u calibrated to the national output; steel by BOF and
   EAF where a national process split exists (worldsteel 2019, repository source), cement on USGS. Base-year comparison on USGS 2019
   (raw steel 8,565 kt, cement 71,900 kt, MYB 2023 Indonesia table 1); 2050 by the v3 rule table (INDUSTRY_OUTPUT_2050_M08B.csv:
   worldsteel 2024 18.642 Mt, USGS 2023 66.924 Mt, R1-R4 of S0 section 3.3). u +-0.1 as sensitivity.
3. Unit energy (item 2): main (b) JRC-IDEES-2021 EU27 2019 final energy (today totals of INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv; carrier
   split from the PyPSA-Eur ratio table scaled to the today total, grade C); (c) national calibration where a national row exists (steel:
   UNSD 2019 iron-and-steel row / USGS 2019 raw steel); (a) ETSAP BAT x ODA (V4_PRODUCT_ROUTE_MAP.csv) as sensitivity, BF-BOF whole route and
   aligned to the final-energy boundary (coal of the route = BF reductant, injection and coke-oven input removed). Fuel input and the useful
   heat it gives (x 0.90, >400 C) are separate columns and never added. 2050 by the PyPSA-Eur 2050 ratios (v3 route rule).
4. Comparisons (S0 section 7.4): national 2019 (+-20 %), 2050 (+-5 %), node shares against INDUSTRY_NODE_SHARES_V3.csv (> 5 pp explained per
   plant), ETSAP and PyPSA-Eur per plant and per country (report only) -> s1/ID_S1_COMPARISON.csv.
5. Cement check (item 12): sources of the clinker ratio 0.656 and of the EDGAR 2.A.1 / 0.52 / 0.656 reconstruction; two PROPOSED corrections of the
   v3 2019 cement deduction, their effect on the 'other' bucket from a scratch copy of the data chain (s3_0_industry.py with the EDGAR row edited),
   outside the repository.
6. NPI / ferronickel / stainless in the GEM steel list (item 2.6).
Read-only on the repository; nothing is solved.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s1_common as cm   # noqa: E402

GEM_STEEL = "extracted/01_gem_steel/gem-download (2)/Plant-level data - Global Iron and Steel Tracker - September 2026 (V1).xlsx"
GEM_CEMENT = "extracted/02_gem_cement/gem-download (2)/Plant-level data - Global Cement and Concrete Tracker - July 2026 - Standard Copy V1.xlsx"
USGS_DIR = "extracted/usgs_myb3_2023_id/myb3-2023-indonesia"
HEAT_EFF = 0.90
OP = ("operating", "operating pre-retirement")


def year_of(x):
    s = str(x)
    m = re.match(r"^(\d{4})", s)
    return int(m.group(1)) if m else np.nan


def usgs_row(work: Path, label: str) -> list:
    """Numbers of a USGS MYB 2023 Indonesia table 1 line (2019 ... 2023), footnote letters dropped."""
    for p in sorted((work / USGS_DIR).glob("p00[6-7].txt")):
        for line in p.read_text(encoding="utf-8").splitlines():
            s = re.sub(r"\s+", " ", line).strip()
            if s.startswith(label):
                vals = re.findall(r"(?<![A-Za-z])(\d{1,3}(?:,\d{3})+|\d+)(?:\s?[re](?:,\s?e)?)?(?=\s|$)", s[len(label):])
                return [float(v.replace(",", "")) for v in vals][-5:]
    raise KeyError(label)


def coords(s):
    try:
        a, b = [float(x) for x in str(s).split(",")]
        return a, b
    except Exception:   # noqa: BLE001
        return np.nan, np.nan


def node_of(df: pd.DataFrame, regions) -> pd.Series:
    import geopandas as gpd
    g = gpd.GeoDataFrame(df[["lat", "lon"]].copy(), geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)
    r = regions[regions.country == "ID"]
    j = gpd.sjoin(g, r[["node", "geometry"]], how="left", predicate="within"); j = j[~j.index.duplicated()]
    out = j.node.copy(); how = pd.Series("point in region", index=j.index)
    for i in j[j.node.isna()].index:
        out.at[i] = r.node.iloc[int(np.argmin(r.geometry.distance(g.geometry.at[i]).values))]; how.at[i] = "nearest node (point outside the onshore regions)"
    return out, how


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); ap.add_argument("--repo", type=Path, default=cm.REPO)
    ap.add_argument("--main", type=Path, default=Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"))
    ap.add_argument("--chain", type=Path, default=Path("/home/jin/v4s1/chain_cement")); a = ap.parse_args()
    import geopandas as gpd
    out = a.work / "s1"; R = a.repo / "research_inputs"; ev = {}
    regions = gpd.read_file(a.main / "research_inputs/renewable_v5/regions_onshore.geojson")
    ratios = pd.read_csv(R / "registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)
    today = pd.read_csv(R / "registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")
    rule = pd.read_csv(R / "demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country").loc["ID"]
    ws = pd.read_csv(R / "registry_v5/sources/WORLDSTEEL_2019_ASEAN.csv").set_index("iso2").loc["ID"]
    rm = pd.read_csv(a.work / "V4_PRODUCT_ROUTE_MAP.csv").set_index("route")
    shares_v3 = pd.read_csv(R / "industry_v3/INDUSTRY_NODE_SHARES_V3.csv")
    u_steel = usgs_row(a.work, "Raw steel do."); u_cem = usgs_row(a.work, "Cement, hydraulic thousand metric tons")
    u_roll = usgs_row(a.work, "Products, semimanufactured, rolled do."); u_pig = usgs_row(a.work, "Pig iron do."); u_dri = usgs_row(a.work, "Direct-reduced iron do.")
    usgs = dict(raw_steel_kt=dict(zip(range(2019, 2024), u_steel)), cement_kt=dict(zip(range(2019, 2024), u_cem)), rolled_kt=dict(zip(range(2019, 2024), u_roll)),
                pig_iron_kt=dict(zip(range(2019, 2024), u_pig)), dri_kt=dict(zip(range(2019, 2024), u_dri)))
    if usgs["raw_steel_kt"][2019] != 8565 or usgs["cement_kt"][2019] != 71900 or usgs["cement_kt"][2023] != 66924:
        raise ValueError(f"USGS table 1 not read as expected {usgs}")
    ev["usgs"] = usgs
    carriers = ("elec", "coal", "coke", "methane", "biomass", "hydrogen", "heat")

    def b_vec(sector, t):   # today total, carrier structure of the PyPSA-Eur ratio column (grade C)
        col = ratios[sector]; tot_f = float(sum(col[c] for c in carriers)); T = float(today.at[sector, "today_total_mwh_per_t"])
        return {c: float(col[c]) / tot_f * T * t for c in carriers}

    def f_vec(sector, t):   # PyPSA-Eur 2050 ratio column
        return {c: float(ratios.at[c, sector]) * t for c in carriers}

    # ================= STEEL =================================================================================================
    xl = pd.read_excel(a.work / GEM_STEEL, sheet_name=None)
    pdata, cap, prod = xl["Plant data"], xl["Plant capacities and status"], xl["Plant production"]
    pdi = pdata[pdata["Country/area"].eq("Indonesia")].set_index("GEM plant ID")
    c = cap[cap["Country/area"].eq("Indonesia")].copy()
    num = lambda s: pd.to_numeric(s, errors="coerce")
    for k, col in (("crude", "Nominal crude steel capacity (ttpa)"), ("bof", "Nominal BOF steel capacity (ttpa)"), ("eaf", "Nominal EAF steel capacity (ttpa)"),
                   ("if_", "Nominal IF steel capacity (ttpa)"), ("oth", "Other/unspecified steel capacity (ttpa)"), ("bf", "Nominal BF capacity (ttpa)"), ("dri", "Nominal DRI capacity (ttpa)")):
        c[k] = num(c[col]).fillna(0.0)
    c["start_y"] = c["Start date"].map(year_of)
    c["retired_y"] = c["GEM plant ID"].map(lambda i: year_of(pdi.at[i, "Retired date"]))
    c["idled_y"] = c["GEM plant ID"].map(lambda i: year_of(pdi.at[i, "Idled date"]))
    c["process"] = np.where(c.bof > 0, "BOF", np.where(c.eaf + c.if_ > 0, "EAF", np.where(c.crude > 0, "other steel", "iron only")))

    def op_in(r, y):
        if r.Status in OP:
            ok = (np.isnan(r.start_y) or r.start_y <= y)
            return "yes" if ok else "no"
        if r.Status in ("mothballed",):
            return "uncertain (mothballed, idled date unknown)" if np.isnan(r.idled_y) else ("yes" if r.idled_y > y and (np.isnan(r.start_y) or r.start_y <= y) else "no")
        if r.Status == "retired":
            return "yes" if (not np.isnan(r.retired_y) and r.retired_y > y and (np.isnan(r.start_y) or r.start_y <= y)) else "no"
        return "no"
    c["op_2019"] = [op_in(r, 2019) for r in c.itertuples()]
    c["op_2024"] = [op_in(r, 2024) for r in c.itertuples()]
    pr = prod[prod["GEM plant ID"].isin(c["GEM plant ID"])]
    crude_p = pr[pr["Type of production"].eq("Crude steel production (ttpa)")].set_index("GEM plant ID")
    pp = {(i, y): float(num(pd.Series([crude_p.at[i, y]])).iloc[0]) for i in crude_p.index for y in (2019, 2024) if pd.notna(num(pd.Series([crude_p.at[i, y]])).iloc[0])}
    ev["gem_steel_production_used"] = {f"{i}:{y}": v for (i, y), v in pp.items()}
    rows_s = []
    nat19 = usgs["raw_steel_kt"][2019]; bof_sh19 = float(ws.bof_oxygen_kt) / float(ws.crude_steel_2019_kt)
    nat24 = float(rule.steel_base_mt) * 1e3
    for y, nat, split in ((2019, nat19, {"BOF": bof_sh19, "EAF": 1 - bof_sh19}), (2024, nat24, None)):
        col = f"op_{y}"
        z = c[(c[col] == "yes") & (c.crude > 0)].copy()
        z["prod_known"] = [pp.get((i, y), np.nan) for i in z["GEM plant ID"]]
        known_plants = set(z[z.prod_known.notna()]["GEM plant ID"])
        z["known"] = z["GEM plant ID"].isin(known_plants)
        # plant production covers the whole plant: spread it over its operating lines by capacity
        for i in known_plants:
            m = z["GEM plant ID"] == i
            z.loc[m, "prod_known"] = pp[(i, y)] * z.loc[m, "crude"] / z.loc[m, "crude"].sum()
        u = {}
        if split:
            for proc in ("BOF", "EAF"):
                m = z.process == proc
                target = nat * split[proc] - z.loc[m & z.known, "prod_known"].sum()
                capr = z.loc[m & ~z.known, "crude"].sum()
                u[proc] = target / capr
        else:
            target = nat - z.loc[z.known, "prod_known"].sum(); capr = z.loc[~z.known, "crude"].sum()
            u["BOF"] = u["EAF"] = target / capr
        z["u"] = z.process.map(u)
        z["activity_kt"] = np.where(z.known, z.prod_known, z.crude * z.u)
        z["activity_capped_kt"] = np.where(z.known, z.prod_known, z.crude * np.minimum(z.u, 1.0))
        z["activity_basis"] = np.where(z.known, f"GEM plant production {y} (crude steel), spread over the plant's operating lines by capacity",
                                       f"capacity x u, u calibrated to " + ("USGS 2019 raw steel x worldsteel 2019 BOF / EAF split" if split else "worldsteel 2024 (v3 base, no process split on disk: one u)"))
        for proc in ("BOF", "EAF"):
            ev.setdefault("steel_u", {})[f"{y}:{proc}"] = float(u[proc])
        ev.setdefault("steel_cal", {})[str(y)] = dict(national_kt=nat, known_kt=float(z.loc[z.known, "prod_known"].sum()), capacity_unknown_kt=float(z.loc[~z.known, "crude"].sum()),
                                                      capacity_operating_kt=float(z.crude.sum()), u=u, facility_total_capped_kt=float(z.activity_capped_kt.sum()),
                                                      uncovered_at_u1_kt=float(nat - z.activity_capped_kt.sum()))
        for r in z.itertuples():
            rows_s.append(dict(year=y, gem_plant_id=r._1, line_status=r.Status, process=r.process, crude_cap_kt=r.crude, u=r.u, activity_kt=r.activity_kt,
                               activity_capped_kt=r.activity_capped_kt, activity_basis=r.activity_basis))
    A = pd.DataFrame(rows_s)
    # facility table: one row per capacity line (all statuses), with the activity of 2019 / 2024
    plant_cols = {"Owner": "owner", "Parent (English)": "parent", "Subnational unit": "province", "Coordinates": "coordinates", "Coordinate accuracy": "coordinate_accuracy",
                  "Retired date": "plant_retired_date", "Idled date": "plant_idled_date", "Ferronickel capacity (ttpa)": "ferronickel_cap_ttpa",
                  "Steel products": "steel_products", "Power source": "power_source", "Main production equipment": "plant_equipment"}
    S = c[["GEM plant ID", "Plant name (English)", "Status", "Start date", "Main production equipment", "process", "crude", "bof", "eaf", "if_", "oth", "bf", "dri", "op_2019", "op_2024"]].copy()
    S.columns = ["gem_plant_id", "plant", "line_status", "line_start_date", "line_equipment", "process", "crude_cap_kt", "bof_cap_kt", "eaf_cap_kt", "if_cap_kt", "other_steel_cap_kt",
                 "bf_cap_kt", "dri_cap_kt", "operating_2019", "operating_2024"]
    for k, v in plant_cols.items():
        S[v] = S.gem_plant_id.map(pdi[k].to_dict())
    S["lat"], S["lon"] = zip(*S.coordinates.map(coords))
    S["node"], S["node_method"] = node_of(S, regions)
    S["line"] = S.groupby("gem_plant_id").cumcount()
    A["line"] = A.groupby(["year", "gem_plant_id"]).cumcount()   # same order as c (operating lines only) -> map by key
    for y in (2019, 2024):
        Ay = A[A.year == y].copy()
        key = c[(c[f"op_{y}"] == "yes") & (c.crude > 0)].reset_index(drop=True)
        Ay = Ay.reset_index(drop=True)
        idx = S.reset_index().merge(key.reset_index()[["GEM plant ID", "Status", "Start date", "crude", "index"]].rename(columns={"GEM plant ID": "gem_plant_id", "Status": "line_status",
                                    "Start date": "line_start_date", "crude": "crude_cap_kt", "index": "k"}), on=["gem_plant_id", "line_status", "line_start_date", "crude_cap_kt"], how="left")
        for col in ("u", "activity_kt", "activity_capped_kt", "activity_basis"):
            S[f"{col}_{y}"] = idx.k.map(lambda k: Ay.at[int(k), col] if pd.notna(k) else np.nan).values
        S[f"gem_production_{y}_kt"] = S.gem_plant_id.map(lambda i: pp.get((i, y), np.nan))
    fe = S.ferronickel_cap_ttpa.astype(str).str.strip()
    S["npi_ferronickel_stainless_flag"] = np.where((fe == ">0") | (pd.to_numeric(fe, errors="coerce") > 0), "ferronickel capacity field > 0",
                                          np.where(S.steel_products.astype(str).str.contains("stainless", case=False), "stainless products",
                                          np.where(S.province.astype(str).str.contains("Central Sulawesi|North Maluku|Southeast Sulawesi", case=False), "located in a nickel-smelter province", "")))
    # energy per line: (b) JRC-IDEES today, (c) national intensity, (a) ETSAP whole route and aligned; 2050 by rule
    unsd19 = 37.790662   # TWh, UNSD 2019 iron-and-steel row used by v3 (V3_OTHER_BUCKET / INDUSTRY_2050_PYPSA_EUR mwh_2019 sum), checked below
    p = pd.read_csv(R / "demand_v5/INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")
    st19 = p[(p.country == "ID") & (p.subsector == "iron and steel")].set_index("carrier").mwh_2019.astype(float) / 1e6
    unsd19 = float(st19.sum())
    cf = cm.conv_factors(); u = cm.unsd()
    coke_twh = float(u[(u.commodity == "Coke-oven coke") & (u.transaction == "consumption by iron and steel industry")].q.iloc[0]) * cf["Coke-oven coke"]
    coal_twh = float(u[(u.commodity == "Hrad coal") & (u.transaction == "consumption by iron and steel industry")].q.iloc[0]) * cf["Hrad coal"]
    c_int = unsd19 / (nat19 / 1e3)   # MWh/t, (c)
    bfbof, eafr = rm.loc["BF-BOF"], rm.loc["scrap EAF / IF"]
    a_whole = {"BOF": float(bfbof.base_electricity_mwh_per_t) + float(bfbof.base_fuel_mwh_per_t), "EAF": float(eafr.base_electricity_mwh_per_t) + float(eafr.base_fuel_mwh_per_t)}
    bat = pd.read_csv(a.work / "evidence/COVERAGE_ETSAP_BAT_SEC.csv")
    bof_coal_gj = float(bat[(bat.route == "steel_bf_bof") & (bat.item == "coal")].bat_gj_per_t.iloc[0])
    a_aligned_bof = a_whole["BOF"] - bof_coal_gj / 3.6 * float(bfbof.oda_ineff_fuel)
    a_al = {"BOF": a_aligned_bof, "EAF": a_whole["EAF"]}
    sec = {"BOF": "Integrated steelworks", "EAF": "Electric arc"}
    for y in (2019, 2024):
        act = S[f"activity_kt_{y}"].fillna(0.0) / 1e3   # Mt
        for proc in ("BOF", "EAF"):
            m = S.process == proc
            vb = {k: v for k, v in b_vec(sec[proc], 1.0).items()}
            for k, v in vb.items():
                S.loc[m, f"b_{y}_{k}_twh"] = act[m] * v
            S.loc[m, f"b_{y}_total_twh"] = act[m] * float(today.at[sec[proc], "today_total_mwh_per_t"])
            S.loc[m, f"a_whole_{y}_twh"] = act[m] * a_whole[proc]; S.loc[m, f"a_aligned_{y}_twh"] = act[m] * a_al[proc]
        S[f"c_{y}_twh"] = act * c_int
        fuel = sum(S[f"b_{y}_{k}_twh"].fillna(0.0) for k in ("coal", "coke", "methane", "biomass"))
        S[f"b_{y}_fuel_twh"] = fuel; S[f"b_{y}_useful_heat_gt400_memo_twh"] = fuel * HEAT_EFF
    # 2050: national v3 rule tonnes, distributed by the 2024 activity (calibrated u, i.e. the whole national output)
    t50 = float(rule.steel_2050_mt)
    w24 = S.activity_kt_2024.fillna(0.0); w24c = S.activity_capped_kt_2024.fillna(0.0)
    S["activity_2050_kt"] = t50 * 1e3 * w24 / w24.sum()
    v50 = {k: 0.3 * f_vec("DRI + Electric arc", 1.0)[k] + 0.7 * f_vec("Electric arc", 1.0)[k] for k in carriers}
    for k, v in v50.items():
        S[f"y2050_{k}_twh"] = S.activity_2050_kt / 1e3 * v
    S["y2050_total_twh"] = sum(S[f"y2050_{k}_twh"] for k in carriers)
    S["source"] = "GEM GIST September 2026 (V1): Plant data / Plant capacities and status / Plant production sheets; node: regions_onshore.geojson (v3 regions)"
    S.to_csv(out / "ID_STEEL_FACILITIES.csv", index=False, float_format="%.6g")
    ev["steel"] = dict(unsd19_twh=unsd19, unsd19_by_carrier=st19.to_dict(), coke_twh=coke_twh, coal_twh=coal_twh, c_intensity_mwh_per_t=c_int, a_whole=a_whole, a_aligned=a_al,
                       bof_coal_gj=bof_coal_gj, b_today={k: float(today.at[v, "today_total_mwh_per_t"]) for k, v in sec.items()}, v50_mwh_per_t=v50,
                       worldsteel_2019=dict(crude=float(ws.crude_steel_2019_kt), bof=float(ws.bof_oxygen_kt), eaf=float(ws.eaf_electric_kt)), t2050_mt=t50,
                       capped_share_2024=float(w24c.sum() / w24.sum()))

    # ================= CEMENT ================================================================================================
    cd = pd.read_excel(a.work / GEM_CEMENT, sheet_name="Final data")
    C = cd[cd["Country/area"].eq("Indonesia")].copy()
    C["cem"] = num(C["Cement capacity (million metric tonnes per annum)"]); C["clk"] = num(C["Clinker capacity (million metric tonnes per annum)"])
    C["gem_prod_2024_25"] = num(C["2024-2025 Cement production (million metric tonnes)"])
    C["start_y"] = C["Start date"].map(year_of)
    for y in (2019, 2023):
        C[f"op_{y}"] = np.where(C["Operating status"].isin(OP) & (C.start_y.isna() | (C.start_y <= y)), np.where(C.start_y.isna(), "yes (start date unknown)", "yes"), "no")
    ratio_v3 = float(pd.read_csv(R / "cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv").query("technology == 'cement finishing' and parameter == 'clinker-input'").value.iloc[0])
    integ = C["Plant type"].eq("integrated")
    rows_c = {}
    for y, nat in ((2019, usgs["cement_kt"][2019]), (2023, float(rule.cement_base_mt) * 1e3)):
        m = C[f"op_{y}"].str.startswith("yes")
        uu = nat / 1e3 / C.loc[m, "cem"].sum()
        C[f"u_{y}"] = np.where(m, uu, np.nan)
        C[f"cement_{y}_mt"] = np.where(m, C.cem * uu, 0.0)
        # clinker: national clinker = cement x ratio; at integrated plants by clinker capacity, else cement capacity x ratio (v3 weight rule)
        wk = np.where(m & integ, np.where(C.clk > 0, C.clk, C.cem * ratio_v3), 0.0)
        C[f"clinker_{y}_mt"] = nat / 1e3 * ratio_v3 * wk / wk.sum()
        rows_c[y] = dict(national_kt=nat, u=uu, capacity_mt=float(C.loc[m, "cem"].sum()), plants=int(m.sum()), start_unknown=int((m & C.start_y.isna()).sum()))
    ev["cement_cal"] = rows_c
    # energy (b): PyPSA-Eur Cement = JRC-IDEES today (efficiency factor 1.0); fuel at clinker sites, electricity split clinker / grinding by technology-data
    cvec = f_vec("Cement", 1.0)
    td = pd.read_csv(R / "cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv")
    ck_el = float(td.query("technology == 'cement dry clinker' and parameter == 'electricity-input'").value.iloc[0])
    cf_el = float(td.query("technology == 'cement finishing' and parameter == 'electricity-input'").value.iloc[0])
    el_kiln_share = ck_el * ratio_v3 / (ck_el * ratio_v3 + cf_el)
    fuel_per_t = cvec["methane"] + cvec["biomass"]
    for y in (2019, 2023):
        nat_mt = C[f"cement_{y}_mt"].sum()
        kiln = C[f"clinker_{y}_mt"] / C[f"clinker_{y}_mt"].sum(); grind = C[f"cement_{y}_mt"] / nat_mt
        C[f"b_{y}_fuel_twh"] = kiln * nat_mt * fuel_per_t
        C[f"b_{y}_methane_twh"] = kiln * nat_mt * cvec["methane"]; C[f"b_{y}_biomass_twh"] = kiln * nat_mt * cvec["biomass"]
        C[f"b_{y}_elec_twh"] = nat_mt * cvec["elec"] * (el_kiln_share * kiln + (1 - el_kiln_share) * grind)
        C[f"b_{y}_heat_twh"] = kiln * nat_mt * cvec["heat"]
        C[f"b_{y}_total_twh"] = C[f"b_{y}_fuel_twh"] + C[f"b_{y}_elec_twh"] + C[f"b_{y}_heat_twh"]
        C[f"b_{y}_useful_heat_gt400_memo_twh"] = C[f"b_{y}_fuel_twh"] * HEAT_EFF
        cr = rm.loc["dry kiln + finishing"]
        C[f"a_{y}_twh"] = (kiln * nat_mt * float(cr.base_fuel_mwh_per_t) + nat_mt * float(cr.base_electricity_mwh_per_t) * (el_kiln_share * kiln + (1 - el_kiln_share) * grind))
    t50c = float(rule.cement_2050_mt)
    k23 = C.clinker_2023_mt / C.clinker_2023_mt.sum(); g23 = C.cement_2023_mt / C.cement_2023_mt.sum()
    C["cement_2050_mt"] = t50c * g23
    for k in ("methane", "biomass", "heat"):
        C[f"y2050_{k}_twh"] = t50c * cvec[k] * k23
    C["y2050_elec_twh"] = t50c * cvec["elec"] * (el_kiln_share * k23 + (1 - el_kiln_share) * g23)
    C["y2050_total_twh"] = C[["y2050_methane_twh", "y2050_biomass_twh", "y2050_heat_twh", "y2050_elec_twh"]].sum(axis=1)
    C["lat"], C["lon"] = zip(*C.Coordinates.map(coords))
    C["node"], C["node_method"] = node_of(C, regions)
    keepc = ["GEM plant ID", "Plant name (English)", "Owner (English)", "Parent", "Subnational unit", "Coordinates", "Coordinate accuracy", "lat", "lon", "node", "node_method",
             "Operating status", "Start date", "Plant type", "cem", "clk", "gem_prod_2024_25", "Clinker production method", "Number of existing kilns", "Kiln technology - precalciner",
             "Kiln technology - waste heat recovery", "Clinker substitution rate", "Alternative fuel for kiln", "op_2019", "op_2023", "u_2019", "u_2023", "cement_2019_mt", "clinker_2019_mt",
             "cement_2023_mt", "clinker_2023_mt"] + [x for x in C.columns if x.startswith(("b_", "a_2", "y2050_"))] + ["cement_2050_mt"]
    CO = C[keepc].rename(columns={"cem": "cement_cap_mtpa", "clk": "clinker_cap_mtpa", "gem_prod_2024_25": "gem_cement_production_2024_25_mt"})
    CO["source"] = "GEM GCCT July 2026 Standard Copy V1, sheet 'Final data'; national: USGS MYB 2023 Indonesia table 1 (2019), v3 rule table (2023 = USGS); node: regions_onshore.geojson"
    CO.to_csv(out / "ID_CEMENT_FACILITIES.csv", index=False, float_format="%.6g")
    p_cem = p[(p.country == "ID") & (p.subsector == "cement")].set_index("carrier").mwh_2019.astype(float) / 1e6
    v3_cem19 = float(p_cem.sum())
    ev["cement"] = dict(ratio_v3=ratio_v3, el_kiln_share=el_kiln_share, ck_el=ck_el, cf_el=cf_el, cvec=cvec, v3_2019_twh=v3_cem19, v3_2019_by_carrier=p_cem.to_dict(), t2050_mt=t50c)

    # ================= COMPARISONS ===========================================================================================
    sub = pd.read_csv(R / "industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv"); sub = sub[(sub.case == "main") & (sub.country == "ID")]
    v3_50 = sub.groupby("subsector").mwh_2050.sum() / 1e6
    cmp_ = []

    def add(item, basis, value, ref, ref_label, tol, unit="TWh", note="", grade="C"):
        rel = (value - ref) / ref if ref else np.nan
        cmp_.append(dict(item=item, basis=basis, value=value, reference=ref, reference_label=ref_label, rel_diff=rel, tolerance=tol,
                         within=(bool(abs(rel) <= tol) if tol is not None and not np.isnan(rel) else None), unit=unit, grade=grade, note=note))
    s19 = S[S.activity_kt_2019.notna()]
    add("steel 2019 national", "(b) JRC-IDEES today x facility activity (USGS 2019 8,565 kt)", float(s19.b_2019_total_twh.sum()), unsd19, "UNSD 2019 iron-and-steel row (v3 2019 steel)", 0.20,
        note="final-energy boundary on both sides? no: UNSD row contains BF coke and injected coal (see next row)")
    add("steel 2019 national", "(b) JRC-IDEES today, final-energy boundary", float(s19.b_2019_total_twh.sum()), unsd19 - coke_twh - coal_twh,
        "UNSD 2019 iron-and-steel row minus coke-oven coke (520.3 kt) and hard coal (160.0 kt) consumed by iron and steel = BF reductant removed", 0.20,
        note="alignment: the BF reductant is removed from the UNSD side (ID reports no BF transformation, so its coke sits in the final-consumption row)")
    add("steel 2019 national", "(a) ETSAP BAT x ODA, whole route (incl. BF reductant and coke ovens)", float(s19.a_whole_2019_twh.sum()), unsd19, "UNSD 2019 iron-and-steel row", None, note="report only")
    add("steel 2019 national", "(a) ETSAP BAT x ODA, aligned (route coal removed)", float(s19.a_aligned_2019_twh.sum()), unsd19 - coke_twh - coal_twh, "UNSD row minus BF reductant", None, note="report only")
    add("steel 2019 national", "(c) UNSD row / USGS raw steel x activity", float(s19.c_2019_twh.sum()), unsd19, "UNSD 2019 iron-and-steel row", 0.20, note="equal by construction", grade="B")
    add("steel 2019 national, worldsteel 7,783 kt instead of USGS", "(b) scaled", float(s19.b_2019_total_twh.sum()) * float(ws.crude_steel_2019_kt) / nat19, unsd19 - coke_twh - coal_twh, "UNSD row minus BF reductant", 0.20)
    s24 = S[S.activity_kt_2024.notna()]
    add("steel 2024 (facility basis)", "(b) JRC-IDEES today x 2024 activity (worldsteel 18.642 Mt)", float(s24.b_2024_total_twh.sum()), 35.0962, "S0 preview (BOF share 0.560)", None, note="report only")
    add("steel 2050", "PyPSA-Eur 2050 (30 % H2-DRI, 70 % EAF) x v3 rule 30.824 Mt, all facilities", float(S.y2050_total_twh.sum()), float(v3_50.get("steel", 0.0)), "v3 2050 steel", 0.05,
        note="v3 nets the chlorine by-product hydrogen of ID against the steel hydrogen (v3_industry.decompose)")
    add("steel 2050", "same, facilities at u <= 1 only (GEM coverage)", float(S.y2050_total_twh.sum()) * ev["steel"]["capped_share_2024"], float(v3_50.get("steel", 0.0)), "v3 2050 steel", 0.05,
        note="share of the 2024 national output that GEM capacity can hold at u <= 1")
    for du in (-0.1, 0.1):   # u +-0.1 on the capacity-based lines (plant production unchanged)
        e = 0.0
        for proc in ("BOF", "EAF"):
            m = (S.process == proc) & S.u_2019.notna() & ~S.activity_basis_2019.astype(str).str.startswith("GEM plant production")
            e += float((S.loc[m, "crude_cap_kt"] * du / 1e3).sum()) * float(today.at[sec[proc], "today_total_mwh_per_t"])
        add("steel 2019 national, u " + ("-0.1" if du < 0 else "+0.1"), "(b) JRC-IDEES today", float(s19.b_2019_total_twh.sum()) + e, unsd19 - coke_twh - coal_twh, "UNSD row minus BF reductant", 0.20,
            note=f"activity change {float((S.loc[S.u_2019.notna() & ~S.activity_basis_2019.astype(str).str.startswith('GEM plant production'), 'crude_cap_kt'] * du).sum()):,.0f} kt")
        mc = CO.op_2019.str.startswith("yes")
        dcem = float(CO.loc[mc, "cement_cap_mtpa"].sum()) * du
        add("cement 2019 national, u " + ("-0.1" if du < 0 else "+0.1"), "(b) PyPSA-Eur Cement", float(CO.b_2019_total_twh.sum()) + dcem * (fuel_per_t + cvec["elec"] + cvec["heat"]), v3_cem19,
            "v3 2019 cement deduction", 0.20, note=f"cement {dcem:+.2f} Mt")
    npi = S[S.npi_ferronickel_stainless_flag != ""].drop_duplicates("gem_plant_id")
    ev["npi_check"] = [dict(plant=r.plant, flag=r.npi_ferronickel_stainless_flag, province=r.province, line_status=r.line_status, ferronickel_cap=str(r.ferronickel_cap_ttpa), products=str(r.steel_products),
                            power_source=str(r.power_source), op_2019=r.operating_2019, op_2024=r.operating_2024) for r in npi.itertuples()]
    ev["nearest_node_fallback"] = dict(steel=S[S.node_method != "point in region"].plant.drop_duplicates().tolist(),
                                       cement=CO[CO.node_method != "point in region"]["Plant name (English)"].tolist())
    c19 = CO[CO.op_2019.str.startswith("yes")]
    add("cement 2019 national", "(b) PyPSA-Eur Cement (= JRC-IDEES today) x USGS 2019 71.9 Mt", float(CO.b_2019_total_twh.sum()), v3_cem19, "v3 2019 cement deduction (EDGAR 2.A.1 / 0.52 / 0.656)", 0.20)
    add("cement 2019 national", "(a) ETSAP BAT x ODA (clinker 0.6 in ETSAP; here 0.656 for the split)", float(CO.a_2019_twh.sum()), v3_cem19, "v3 2019 cement deduction", None, note="report only")
    add("cement 2050", "PyPSA-Eur Cement 2050 x v3 rule 112.82 Mt", float(CO.y2050_total_twh.sum()), float(v3_50.get("cement", 0.0)), "v3 2050 cement", 0.05)
    # node shares
    for key, df, w in (("steel", S, "activity_kt_2024"), ("cement", CO, "clinker_2023_mt")):
        f = df.groupby("node")[w].sum(); f = f / f.sum()
        v = shares_v3[(shares_v3.country == "ID") & (shares_v3.subsector == key)].set_index("node").share
        for n in sorted(set(f.index) | set(v.index)):
            fs, vs = float(f.get(n, 0.0)), float(v.get(n, 0.0))
            plants = "; ".join(f"{r.plant if key == 'steel' else r['Plant name (English)']}" for _, r in (df[df.node == n].drop_duplicates("gem_plant_id" if key == "steel" else "GEM plant ID").iterrows())) if abs(fs - vs) > 0.05 else ""
            cmp_.append(dict(item=f"{key} node share", basis=f"facility weight {w}", node=n, value=fs, reference=vs, reference_label="INDUSTRY_NODE_SHARES_V3.csv", rel_diff=fs - vs, tolerance=0.05,
                             within=abs(fs - vs) <= 0.05, unit="share", grade="B", note=plants))
    CMP = pd.DataFrame(cmp_)

    # ================= CEMENT CHECK (item 12): two PROPOSED corrections through a scratch copy of the data chain ===============
    edgar_rel = "research_inputs/registry_v5/sources/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv"
    ed = pd.read_csv(R / "registry_v5/sources/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv")
    co2 = float(ed[(ed.iso == "ID") & (ed.ipcc_code_2006_for_standard_report == "2.A.1")].kt_CO2_2019.iloc[0])
    co2_24 = float(ed[(ed.iso == "ID") & (ed.ipcc_code_2006_for_standard_report == "2.A.1")].kt_CO2_2024.iloc[0])
    clk19 = co2 / 0.52; cem_eq = clk19 / ratio_v3
    gc = dict(clinker_cap_known_mt=float(C.loc[integ & (C.clk > 0), "clk"].sum()), integrated_cement_cap_with_clinker_mt=float(C.loc[integ & (C.clk > 0), "cem"].sum()),
              integrated_plants=int(integ.sum()), integrated_with_clinker=int((integ & (C.clk > 0)).sum()), cement_cap_all_mt=float(C.cem.sum()),
              integrated_cement_cap_mt=float(C.loc[integ, "cem"].sum()), substitution_rate=C["Clinker substitution rate"].astype(str).value_counts().to_dict())
    ev["cement_check"] = dict(edgar_2A1_2019_kt=co2, edgar_2A1_2024_kt=co2_24, ef=0.52, clinker_2019_mt=clk19 / 1e3, cement_equivalent_mt=cem_eq / 1e3,
                              usgs_2019_mt=usgs["cement_kt"][2019] / 1e3, implied_clinker_ratio_vs_usgs=clk19 / usgs["cement_kt"][2019], gem=gc,
                              etsap_clinker_ratio=0.6, edgar_2024_clinker_mt=co2_24 / 0.52 / 1e3, usgs_2023_mt=usgs["cement_kt"][2023] / 1e3,
                              implied_ratio_2023_edgar2024=(co2_24 / 0.52) / usgs["cement_kt"][2023])
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import v3_industry as v3   # noqa: E402
    fut = v3.future_vectors(); nf = v3.nonferrous(fut, "main", v3.nickel_unit_energy())[0]["ID"]
    if a.chain.exists():
        shutil.rmtree(a.chain)
    a.chain.mkdir(parents=True)
    shutil.copytree(a.repo / "research_inputs", a.chain / "research_inputs")
    shutil.copytree(a.repo / "scripts_project", a.chain / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
    (a.chain / "scripts_project/retired").mkdir(exist_ok=True)
    orig_ed = (a.chain / edgar_rel).read_bytes()

    def run(co2_new):
        (a.chain / edgar_rel).write_bytes(orig_ed)
        if co2_new is not None:
            e2 = pd.read_csv(a.chain / edgar_rel, dtype=str)
            m = (e2.iso == "ID") & (e2.ipcc_code_2006_for_standard_report == "2.A.1")
            e2.loc[m, "kt_CO2_2019"] = repr(co2_new); e2.to_csv(a.chain / edgar_rel, index=False)
        r = subprocess.run([sys.executable, "s3_0_industry.py"], cwd=a.chain / "scripts_project", capture_output=True, text=True, env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"})
        if r.returncode:
            raise RuntimeError(r.stderr[-2000:])
        row = pd.read_csv(a.chain / "research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country").loc["ID"]
        ob = pd.read_csv(a.chain / "research_inputs/demand_v5/INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[(ob["mode"] == "aeo8_ats_anchor") & (ob.country == "ID")].iloc[0]
        pz = pd.read_csv(a.chain / "research_inputs/demand_v5/INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv")
        cem = float(pz[(pz.country == "ID") & (pz.subsector == "cement")].mwh_2019.astype(float).sum()) / 1e6
        T = float(sum(row[v3.col(x)] for x in v3.CARRIERS))
        parts = v3.decompose(row, fut); parts.update(nf)
        expl = sum(sum(v.values()) for k, v in parts.items() if k != "other"); so = sum(parts["other"].values()); f = (T - expl) / so
        return dict(cement19_twh=cem, other19_twh=float(ob.other_2019_mwh) / 1e6, T_twh=T / 1e6, other50_twh=(T - expl) / 1e6, other_scale=f,
                    other50_by_carrier={k: v * f / 1e6 for k, v in parts["other"].items()})
    base = run(None)
    if abs(base["other50_twh"] - float(sub[sub.subsector == "other"].mwh_2050.sum()) / 1e6) > 1e-6:
        raise ValueError("unmodified cement chain does not reproduce the v3 ID other bucket")
    corr = {}
    corr["i_usgs_cement_x_0.656"] = run(usgs["cement_kt"][2019] * ratio_v3 * 0.52)   # cement 2019 = USGS 71.9 Mt with the v3 clinker ratio
    run(None)
    ev["cement_check"]["chain"] = dict(base=base, corrections=corr)
    # correction (ii): kiln fuel on EDGAR clinker, grinding electricity on USGS cement (only the electricity part changes): analytic
    d_el = (cem_eq - usgs["cement_kt"][2019]) / 1e3 * cvec["elec"]   # kt -> Mt x MWh/t = TWh less cement electricity taken from other
    ev["cement_check"]["correction_ii_delta_cement19_twh"] = -d_el
    for k, z in corr.items():
        cmp_.append(dict(item="cement check: v3 2019 cement deduction corrected (PROPOSED)", basis=k, value=z["cement19_twh"], reference=base["cement19_twh"], reference_label="v3 2019 cement deduction",
                         rel_diff=(z["cement19_twh"] - base["cement19_twh"]) / base["cement19_twh"], unit="TWh", grade="C",
                         note=f"other 2019 {base['other19_twh']:.3f} -> {z['other19_twh']:.3f}; T_v2(ID) {base['T_twh']:.3f} -> {z['T_twh']:.3f}; v3 other 2050 {base['other50_twh']:.3f} -> {z['other50_twh']:.3f} TWh"))
    dm = pd.read_csv(R / "demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False)
    mult_id = float(dm[(dm.country == "ID") & (dm.sector == "Industry")].multiplier_total.astype(float).iloc[0])
    d50 = d_el * mult_id * base["other_scale"]
    ev["cement_check"]["correction_ii_delta_other50_el_twh"] = d50
    cmp_.append(dict(item="cement check: v3 2019 cement deduction corrected (PROPOSED)", basis="ii_kiln_on_EDGAR_clinker_grinding_on_USGS_cement", value=base["cement19_twh"] - d_el,
                     reference=base["cement19_twh"], reference_label="v3 2019 cement deduction", rel_diff=-d_el / base["cement19_twh"], unit="TWh", grade="C",
                     note=f"only the cement electricity changes by {-d_el:.3f} TWh; other 2019 electricity +{d_el:.3f} TWh; 2050 other electricity about +{d50:.3f} TWh (x multiplier x scale; T_v2 rises by the same amount)"))
    CMP = pd.DataFrame(cmp_)
    CMP.to_csv(out / "ID_S1_COMPARISON.csv", index=False, float_format="%.6g")
    ev["comparison"] = CMP.drop(columns=["note"]).to_dict("records")
    (out / "_facilities_evidence.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 70)
    print(json.dumps(dict(steel_cal=ev["steel_cal"], cement_cal=ev["cement_cal"]), indent=0, default=float))
    print(CMP[["item", "basis", "node", "value", "reference", "rel_diff", "within"]].round(4).to_string())
    print(json.dumps(ev["cement_check"], indent=0, default=float)[:3000])


if __name__ == "__main__":
    main()
