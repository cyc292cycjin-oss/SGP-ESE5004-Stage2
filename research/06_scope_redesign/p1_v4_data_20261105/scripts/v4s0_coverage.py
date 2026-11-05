"""V4 S0 section 4: coverage of every downloaded source for the 11 ASEAN countries.

    python scripts/v4s0_coverage.py --work <work dir>

Writes evidence/COVERAGE_*.csv and evidence/COVERAGE_SUMMARY.json. Read-only. ETSAP BAT values are transcribed with their sheet and row and
verified against the workbook cells at run time (the script stops on a mismatch).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pyarrow.dataset as pads

ISO2 = {"Brunei": "BN", "Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Laos": "LA", "Lao PDR": "LA", "Lao People's Democratic Republic": "LA",
        "Malaysia": "MY", "Myanmar": "MM", "Burma": "MM", "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "East Timor": "TL",
        "Vietnam": "VN", "Viet Nam": "VN"}
ISO3 = {"BRN": "BN", "KHM": "KH", "IDN": "ID", "LAO": "LA", "MYS": "MY", "MMR": "MM", "PHL": "PH", "SGP": "SG", "THA": "TH", "TLS": "TL", "VNM": "VN"}
ASEAN = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]


def num(s):
    return pd.to_numeric(s, errors="coerce")


def ctab(df, key, col):
    t = df.groupby([key, col]).size().unstack(fill_value=0)
    return t.reindex(ASEAN, fill_value=0)


def gem_steel(ex: Path, out: Path, S: dict):
    d = ex / "01_gem_steel/gem-download (2)"
    pl = pd.read_excel(d / "Plant-level data - Global Iron and Steel Tracker - September 2026 (V1).xlsx", sheet_name=None)
    pdata, cap, prod = pl["Plant data"], pl["Plant capacities and status"], pl["Plant production"]
    pdata["iso"] = pdata["Country/area"].map(ISO2); cap["iso"] = cap["Country/area"].map(ISO2)
    a = pdata[pdata.iso.notna()]; c = cap[cap.iso.notna()]
    c = c.assign(crude=num(c["Nominal crude steel capacity (ttpa)"]), bof=num(c["Nominal BOF steel capacity (ttpa)"]), eaf=num(c["Nominal EAF steel capacity (ttpa)"]),
                 ind=num(c["Nominal IF steel capacity (ttpa)"]), bf=num(c["Nominal BF capacity (ttpa)"]), dri=num(c["Nominal DRI capacity (ttpa)"]))
    st = ctab(c, "iso", "Status"); st.to_csv(out / "COVERAGE_GEM_STEEL_STATUS.csv")
    op = c[c.Status.isin(["operating", "operating pre-retirement"])]
    capsum = op.groupby("iso")[["crude", "bof", "eaf", "ind", "bf", "dri"]].sum().reindex(ASEAN, fill_value=0.0)
    capsum.to_csv(out / "COVERAGE_GEM_STEEL_OPERATING_CAPACITY_KTPA.csv")
    ids = set(a["GEM plant ID"])
    p = prod[prod["GEM plant ID"].isin(ids)].copy()
    years = [x for x in p.columns if re.fullmatch(r"20\d\d(\.0)?", str(x))]
    pm = p.melt(id_vars=["GEM plant ID", "Type of production"], value_vars=years, var_name="year", value_name="v")
    pm["v"] = num(pm.v); pm["year"] = pm.year.astype(str).str[:4]
    iso_of = dict(zip(pdata["GEM plant ID"], pdata.iso))
    pm["iso"] = pm["GEM plant ID"].map(iso_of)
    pc = pm[pm.v.notna()].groupby(["iso", "Type of production", "year"]).agg(plants=("GEM plant ID", "nunique"), kt=("v", "sum")).reset_index()
    pc.to_csv(out / "COVERAGE_GEM_STEEL_PRODUCTION.csv", index=False)
    coords = a.Coordinates.astype(str).str.contains(",")
    units = {}
    for fn, kind in (("Steel unit data - Global Iron and Steel Tracker - September 2026 (V1).xlsx", "steel"), ("Iron unit data - Global Iron and Steel Tracker - September 2026 (V1).xlsx", "iron")):
        u = pd.read_excel(d / fn, sheet_name=None)
        for sh, df in u.items():
            if "GEM unit ID" not in df.columns or "Country/area" not in df.columns:   # relining sheet has no country column
                continue
            df = df.assign(iso=df["Country/area"].map(ISO2), capk=num(df["Current capacity (ttpa)"]))
            df = df[df.iso.notna()]
            units[sh] = dict(units=int(len(df)), operating=int(df["Unit status"].astype(str).str.startswith("operating").sum()),
                             operating_capacity_ktpa=float(df[df["Unit status"].astype(str).str.startswith("operating")].capk.sum()),
                             by_country=df.groupby("iso").size().to_dict())
    S["gem_steel"] = dict(plants=int(len(a)), plants_by_country=a.iso.value_counts().to_dict(), with_coordinates=int(coords.sum()),
                          coordinate_accuracy=a["Coordinate accuracy"].value_counts().to_dict(),
                          ferronickel_capacity_nonzero=int((num(a.get("Ferronickel capacity (ttpa)")) > 0).sum()),
                          production_years=sorted(pm[pm.v.notna()].year.unique().tolist()),
                          production_plant_years_by_type=pm[pm.v.notna()].groupby("Type of production").size().to_dict(), units=units,
                          name_unmatched=sorted(set(x for x in pdata["Country/area"].dropna().unique() if any(k in str(x) for k in ("Viet", "Lao", "Burma", "Timor", "Brunei")) and x not in ISO2)))


def gem_cement(ex: Path, out: Path, S: dict):
    f = ex / "02_gem_cement/gem-download (2)/Plant-level data - Global Cement and Concrete Tracker - July 2026 - Standard Copy V1.xlsx"
    df = pd.read_excel(f, sheet_name="Final data")
    df["iso"] = df["Country/area"].map(ISO2); a = df[df.iso.notna()].copy()
    a["cem"] = num(a["Cement capacity (million metric tonnes per annum)"]); a["clk"] = num(a["Clinker capacity (million metric tonnes per annum)"])
    a["prod"] = num(a["2024-2025 Cement production (million metric tonnes)"])
    st = ctab(a, "iso", "Operating status"); st.to_csv(out / "COVERAGE_GEM_CEMENT_STATUS.csv")
    op = a[a["Operating status"].isin(["operating", "operating pre-retirement"])]
    g = op.groupby("iso").agg(plants=("GEM plant ID", "size"), cement_mtpa=("cem", "sum"), clinker_mtpa=("clk", "sum"), with_cement_cap=("cem", "count"),
                              with_clinker_cap=("clk", "count"), with_production=("prod", "count"), production_mt=("prod", "sum")).reindex(ASEAN, fill_value=0)
    g = g.join(ctab(op, "iso", "Plant type").add_prefix("type_"))
    g.to_csv(out / "COVERAGE_GEM_CEMENT_OPERATING.csv")
    S["gem_cement"] = dict(plants=int(len(a)), operating=int(len(op)), clinker_method=op["Clinker production method"].value_counts().to_dict(),
                           with_coordinates=int(a.Coordinates.astype(str).str.contains(",").sum()), production_field="2024-2025 Cement production (million metric tonnes)")


def gem_chem(dl: Path, out: Path, S: dict):
    f = dl / "03_gem_chemicals/Plant-level-data-Global-Chemicals-Tracker-November-2026-V1.xlsx"
    pdat = pd.read_excel(f, sheet_name="Plant Data"); cap = pd.read_excel(f, sheet_name="Chemical Capacities")
    ccol = [c for c in pdat.columns if c.lower().startswith("country")][0]
    pdat["iso"] = pdat[ccol].map(ISO2); a = pdat[pdat.iso.notna()]
    scol = [c for c in pdat.columns if c.lower() == "operating status"][0]
    ctab(a, "iso", scol).to_csv(out / "COVERAGE_GEM_CHEM_STATUS.csv")
    c = cap.merge(a[["GEM Plant ID", "iso"]], on="GEM Plant ID")
    c["cap"] = num(c["Capacity (ttpa)"])
    op = c[c["Capacity Status"].astype(str).str.startswith("operating")]
    t = op.pivot_table(index="Product Group", columns="iso", values="cap", aggfunc="sum").reindex(columns=ASEAN).fillna(0.0)
    t.to_csv(out / "COVERAGE_GEM_CHEM_OPERATING_CAPACITY_KTPA_BY_PRODUCT_GROUP.csv")
    S["gem_chemicals"] = dict(plants=int(len(a)), plants_by_country=a.iso.value_counts().to_dict(), columns=list(pdat.columns),
                              product_groups_operating=sorted(op["Product Group"].dropna().unique().tolist()), capacity_rows_asean=int(len(c)))


def sfi(dl: Path, out: Path, S: dict):
    f = dl / "04_sfi_pulp_paper/SFI_ALD_Pulp_Paper_Database_July_2025.xlsx"
    df = pd.read_excel(f, sheet_name="SFI_Pulp_Paper_Database"); df["iso"] = df.iso3.map(ISO3); a = df[df.iso.notna()].copy()
    a["pulp"] = num(a["capacity_pulp (tonnes per year) "] if "capacity_pulp (tonnes per year) " in a else a.filter(like="capacity_pulp").iloc[:, 0])
    a["paper"] = num(a.filter(like="capacity_paper").iloc[:, 0])
    g = a.groupby("iso").agg(mills=("uid", "size"), pulp_t=("pulp", "sum"), paper_t=("paper", "sum"), with_pulp=("pulp", "count"), with_paper=("paper", "count")).reindex(ASEAN, fill_value=0)
    g = g.join(ctab(a, "iso", "status").add_prefix("status_")).join(ctab(a, "iso", "plant_type").add_prefix("type_"))
    g.to_csv(out / "COVERAGE_SFI_PULP_PAPER.csv")
    comp = pd.read_excel(f, sheet_name="About_Completeness", header=None)
    hdr = comp.index[comp.iloc[:, 0].astype(str).str.strip() == "Country"][0]
    comp.columns = comp.iloc[hdr]; comp = comp.iloc[hdr + 1:]
    comp = comp[comp.Country.astype(str).str.strip().isin(ISO2)]
    comp.to_csv(out / "COVERAGE_SFI_PULP_PAPER_COMPLETENESS_ASEAN.csv", index=False)
    S["sfi_pulp_paper"] = dict(mills=int(len(a)), fuel=a.fuel.value_counts().head(10).to_dict(), accuracy=a.accuracy.value_counts().to_dict())
    e = pd.read_excel(dl / "05_sfi_ethylene/Global_Ethylene_Production_Database_December_2025.xlsx")
    e["iso"] = e.iso3.map(ISO3); b = e[e.iso.notna()].copy(); b["cap"] = num(b["capacity (Kt ethylene/year)"])
    gb = b.groupby(["iso", "status"]).agg(units=("uid", "size"), kt=("cap", "sum")).reset_index()
    gb.to_csv(out / "COVERAGE_SFI_ETHYLENE.csv", index=False)
    S["sfi_ethylene"] = dict(units=int(len(b)), by_country=b.iso.value_counts().to_dict(), feedstock=b.feedstock.value_counts().to_dict(),
                             refinery_integration=b.refinery_integration.value_counts().to_dict(), total_rows_global=int(len(e)))


def climate_trace(ex: Path, out: Path, S: dict):
    rows, defs = [], []
    schema = pd.read_csv(next((ex / "06_climate_trace/manufacturing_cement/ABOUT_THE_DATA").glob("detailed_data_schema_*.csv")))
    for pkg in sorted((ex / "06_climate_trace").iterdir()):
        if pkg.name in ("manufacturing", "fossil_fuel_operations") or not (pkg / "DATA").exists():
            continue
        src = [p for p in (pkg / "DATA").glob("*_emissions_sources_v*.parquet") if not re.search(r"_(confidence|uncertainty|ownership)_", p.name)]
        if not src:
            rows.append(dict(package=pkg.name, country="ALL", note="no asset file (country totals only)")); continue
        ds = pads.dataset(src[0])
        tab = ds.to_table(columns=["source_id", "source_type", "iso3_country", "subsector", "start_time", "gas", "activity", "activity_units", "capacity", "capacity_units",
                                   "capacity_factor", "emissions_quantity", "most_granular"],
                          filter=(pads.field("gas") == "co2e_100yr") & pads.field("iso3_country").isin(list(ISO3))).to_pandas()
        sub = tab.subsector.iloc[0] if len(tab) else pkg.name.split("_", 1)[-1]
        sc = schema[schema.subsector == sub]
        if len(sc):
            r = sc.iloc[0]
            defs.append(dict(subsector=sub, activity=r.get("activity"), activity_units=r.get("activity_units"), capacity=r.get("capacity"), capacity_units=r.get("capacity_units"),
                             asset_definition=r.get("2026_asset-definition"), data_through=r.get("Data available through"),
                             others="; ".join(f"{r.get(f'other{i}')}={r.get(f'other{i}_def')}" for i in range(1, 11) if pd.notna(r.get(f"other{i}"))) ))
        if not len(tab):
            rows.append(dict(package=pkg.name, subsector=sub, country="ASEAN", sources=0)); continue
        tab["year"] = pd.to_datetime(tab.start_time).dt.year; tab["iso"] = tab.iso3_country.map(ISO3)
        last = int(tab.year.max()); full = last if (tab[tab.year == last].start_time.nunique() >= 12) else last - 1
        for iso, g in tab.groupby("iso"):
            y = g[g.year == full]
            rows.append(dict(package=pkg.name, subsector=sub, country=iso, sources=int(g.source_id.nunique()), source_types=";".join(sorted(g.source_type.dropna().astype(str).unique())),
                             most_granular_true=int(g[g.most_granular == True].source_id.nunique()), years=f"{int(g.year.min())}-{int(g.year.max())}",  # noqa: E712
                             full_year=full, activity_nonnull_share=float(g.activity.notna().mean()), activity_units=";".join(sorted(g.activity_units.dropna().astype(str).unique())),
                             capacity_units=";".join(sorted(g.capacity_units.dropna().astype(str).unique())), capacity_nonnull_share=float(g.capacity.notna().mean()),
                             activity_full_year=float(y.activity.sum()), co2e_100yr_full_year_t=float(y.emissions_quantity.sum())))
    pd.DataFrame(rows).to_csv(out / "COVERAGE_CLIMATE_TRACE.csv", index=False)
    pd.DataFrame(defs).to_csv(out / "COVERAGE_CLIMATE_TRACE_DEFINITIONS.csv", index=False)
    S["climate_trace"] = dict(packages=len({r["package"] for r in rows}), rows=len(rows))


# ETSAP BAT transcription (GJ per t product): (sheet, row of the value, column index of the BAT value in the openpyxl row tuple, value)
BAT = [
    ("steel_bf_bof", "Steel", [("total", 5, 19.51), ("electricity", 6, 2.35), ("fuel", 7, 17.16), ("coal", 8, 16.44), ("gas", 9, 0.68), ("oil", 10, 0.04)]),
    ("steel_dri_eaf_gas", "Steel", [("total", 15, 20.1), ("electricity", 16, 4.37), ("fuel", 17, 15.73), ("coal", 18, 1.02), ("gas", 19, 14.71)]),
    ("steel_secondary_eaf", "Steel", [("total", 25, 2.68), ("electricity", 26, 1.45), ("fuel", 27, 1.23), ("coal", 28, 0.45), ("gas", 29, 0.78)]),
    ("clinker", "Cement", [("total", 4, 3.116), ("heat", 5, 2.9), ("electricity", 11, 0.216)]),
    ("cement_finishing", "Cement", [("total", 18, 0.14), ("electricity", 19, 0.14), ("clinker_t_per_t", 20, 0.6)]),
    ("aluminium_primary", "Aluminium", [("total_energy", 28, 64.15), ("electricity", 29, 49.35), ("fuel", 30, 14.8), ("feedstock_coal_anode", 26, 13.93)]),
    ("alumina_refining_fuel", "Aluminium", [("fuel", 5, 9.65)]),
    ("aluminium_secondary", "Aluminium", [("total_energy", 52, 6.4), ("electricity", 53, 2.15), ("fuel", 54, 4.25)]),
    ("copper_primary_smelting", "Copper", [("total", 13, 3.2), ("electricity", 5, 2.368), ("fuel", 6, 0.832)]),
    ("copper_refining_casting", "Copper", [("total_energy", 46, 5.199), ("electricity", 47, 2.144), ("fuel", 48, 3.055)]),
    ("glass_container", "Glass", [("total", 5, 5.4), ("electricity", 6, 1.24), ("fuel", 7, 4.16)]),
    ("glass_flat", "Glass", [("total", 18, 10.62), ("electricity", 19, 3.03), ("fuel", 20, 7.59)]),
    ("lime", "Lime", [("total", 5, 4.47), ("electricity", 6, 0.22), ("fuel", 7, 4.25)]),
    ("pulp_chemical", "Paper", [("total", 4, 14.9), ("heat", 5, 12.6), ("electricity", 12, 2.3), ("black_liquor_output", 14, 22.0)]),
    ("pulp_mechanical", "Paper", [("total", 19, 6.7), ("heat_recovery", 20, -1.2), ("electricity", 27, 7.9)]),
    ("pulp_recycling", "Paper", [("total", 33, 1.43), ("heat", 35, 0.5), ("electricity", 41, 0.93)]),
    ("paper_packaging", "Paper", [("total", 47, 6.1), ("heat", 48, 4.3), ("electricity", 54, 1.8)]),
    ("paper_graphical", "Paper", [("total", 60, 7.0), ("heat", 61, 5.2), ("electricity", 67, 1.8)]),
    ("paper_hygiene", "Paper", [("total", 73, 8.7), ("heat", 74, 5.1), ("electricity", 80, 3.6)]),
    ("paper_tech_packaging", "Paper", [("total", 86, 7.8), ("heat", 87, 4.9), ("electricity", 93, 2.9)]),
    ("chlorine_membrane_odc", "Chlorine", [("total", 4, 7.2), ("electricity", 5, 7.2)]),
    ("ammonia_gas", "Ammonia", [("total_with_feedstock", 5, 32.3), ("electricity", 6, 0.3), ("fuel_gas", 9, 11.0), ("feedstock_gas", 12, 21.0), ("total_energy", 15, 11.3)]),
    ("ammonia_coal", "Ammonia", [("total_with_feedstock", 18, 37.4), ("electricity", 19, 3.7), ("fuel_coal", 21, 15.1), ("feedstock_coal", 25, 18.6), ("total_energy", 28, 18.8)]),
    ("methanol_gas", "Methanol", [("total_with_feedstock", 4, 30.86), ("electricity", 5, 0.56), ("fuel", 6, 10.6), ("feedstock", 7, 19.7), ("total_energy", 10, 11.16)]),
    ("olefins_naphtha_steam_cracking", "Olefins", [("total_with_feedstock", 4, 54.5), ("electricity", 5, 1.0), ("fuel", 6, 11.0), ("feedstock", 12, 42.5), ("total_energy", 15, 12.0)]),
    ("aromatics", "Aromatics", [("total_with_feedstock", 4, 49.5), ("electricity", 5, 0.336), ("fuel", 6, 6.664), ("feedstock", 12, 42.5), ("total_energy", 15, 7.0)]),
]


def etsap(ex: Path, out: Path, S: dict):
    E = next((ex / "07_etsap_industrial_demand").glob("*/Follow-ETSAP-*"))
    wb = openpyxl.load_workbook(E / "02_Energy_calculation/01 Specific energy demand_minimal.xlsx", read_only=True, data_only=True)
    rows = []
    for route, sheet, items in BAT:
        ws = list(wb[sheet].iter_rows(values_only=True))
        for item, r, v in items:
            nums = [x for x in ws[r - 1] if isinstance(x, (int, float)) and not isinstance(x, bool)]
            if not any(abs(float(x) - v) <= 1e-3 * max(1.0, abs(v)) for x in nums):
                raise SystemExit(f"ETSAP transcription mismatch {route} {item} row {r}: {v} not in {nums}")
            rows.append(dict(route=route, sheet=sheet, row=r, item=item, bat_gj_per_t=v, bat_mwh_per_t=v / 3.6))
    pd.DataFrame(rows).to_csv(out / "COVERAGE_ETSAP_BAT_SEC.csv", index=False)
    # ODA inefficiency factors (BAT, adjusted) from the Overview sheet and the per-subsector sheets
    wb3 = openpyxl.load_workbook(E / "02_Energy_calculation/03 Inefficiencies and scaled energy.xlsx", read_only=True, data_only=True)
    ov = {r[0]: r for r in wb3["Overview"].iter_rows(values_only=True) if r and r[0]}
    oda = ov["ODA"]
    ineff = dict(iron_steel=oda[1], non_ferrous=oda[2], non_metallic_minerals=oda[3], pulp_paper=oda[4], chemicals=oda[5], average=oda[6])
    detail = {}
    for sh in ("Iron&Steel", "Non-Ferrous", "Non-metallic Minerals", "Paper&Pulp", "Chemicals"):
        rr = list(wb3[sh].iter_rows(values_only=True))
        hdr2, hdr3 = rr[1], rr[2]; oda_row = [r for r in rr if r and r[0] == "ODA"][0]
        # the 'BAT raw' / 'BAT adjusted' groups: find their start columns in row 2 and read the following (Total, Electricity, Fuel[, ...]) cells
        def grp(name):
            i = [j for j, x in enumerate(hdr2) if isinstance(x, str) and x.strip() == name][0]
            k = i; vals = {}
            while k < len(hdr3) and (k == i or (hdr2[k] in (None, "") )) and hdr3[k]:
                vals[str(hdr3[k]).strip()] = oda_row[k]; k += 1
            return vals
        detail[sh] = dict(bat_raw=grp("BAT raw"), bat_adjusted=grp("BAT adjusted"), theoretical_adjusted=oda_row[[j for j, x in enumerate(hdr2) if isinstance(x, str) and x.strip() == "theoretical adjusted"][0]])
    # production quantities: which ASEAN countries / years appear in 01_Production_quantities
    prod = []
    for f in sorted((E / "01_Production_quantities").rglob("*.xlsx")):
        wbp = openpyxl.load_workbook(f, read_only=True, data_only=True)
        for ws in wbp.worksheets:
            if ws.title.lower().startswith("ref"):
                continue
            rr = list(ws.iter_rows(values_only=True))
            title = next((str(r[0]) for r in rr if r and r[0]), "")
            year = re.search(r"(20\d\d)", title).group(1) if re.search(r"(20\d\d)", title) else ""
            hdr = next(r for r in rr[1:4] if r and any(isinstance(x, str) for x in r))
            for r in rr:
                names = [x for x in r[:2] if isinstance(x, str)]
                iso = next((ISO2.get(x) or ISO3.get(x) for x in names if (ISO2.get(x) or ISO3.get(x))), None)
                if iso:
                    for h, x in zip(hdr, r):
                        if isinstance(x, (int, float)) and h not in (None, "gadm_gid_0"):
                            prod.append(dict(file=f.name, sheet=ws.title, year=year, country=iso, product=str(h), kt=float(x)))
                if r and r[0] == "ODA":
                    for h, x in zip(hdr, r):
                        if isinstance(x, (int, float)):
                            prod.append(dict(file=f.name, sheet=ws.title, year=year, country="ODA (region row)", product=str(h), kt=float(x)))
    P = pd.DataFrame(prod); P.to_csv(out / "COVERAGE_ETSAP_PRODUCTION_ASEAN.csv", index=False)
    reg = pd.read_csv(E / "TIAM_regions.csv", encoding="latin-1"); r_ = reg[reg.GID_0.isin(ISO3)]   # file is Latin-1 encoded
    S["etsap"] = dict(tiam_region_of_asean=dict(zip(r_.GID_0.map(ISO3), r_["TIAM-Region"])), oda_members=int((reg["TIAM-Region"] == "ODA").sum()),
                      oda_inefficiency_bat_adjusted_overview=ineff, oda_inefficiency_detail=detail,
                      production_files_with_asean_rows=sorted(P[P.country.isin(ASEAN)].file.unique().tolist()),
                      production_files_region_only=sorted(set(P.file) - set(P[P.country.isin(ASEAN)].file)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); ap.add_argument("--only", default="")
    a = ap.parse_args()
    dl, ex, out = a.work / "downloads", a.work / "extracted", a.work / "evidence"
    S = {}
    steps = dict(gem_steel=lambda: gem_steel(ex, out, S), gem_cement=lambda: gem_cement(ex, out, S), gem_chem=lambda: gem_chem(dl, out, S),
                 sfi=lambda: sfi(dl, out, S), etsap=lambda: etsap(ex, out, S), climate_trace=lambda: climate_trace(ex, out, S))
    for k, f in steps.items():
        if a.only and k not in a.only.split(","):
            continue
        f(); print("done", k, flush=True)
    p = out / "COVERAGE_SUMMARY.json"
    old = json.loads(p.read_text()) if p.exists() else {}
    old.update(S)
    p.write_text(json.dumps(old, indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o)) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
