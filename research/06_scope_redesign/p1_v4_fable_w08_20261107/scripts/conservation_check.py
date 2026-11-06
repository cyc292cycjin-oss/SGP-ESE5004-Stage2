"""Fable W08 review, dimension 4: conservation and double-counting checks on the committed v4 tables (out_ras, out_iid) and inputs.

Own arithmetic on the files only (no repository module imported). Writes CONSERVATION_CHECK.json.
"""
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(sys.argv[1]); OUT = Path(sys.argv[2])
V4 = REPO / "research_inputs/industry_v4"; BIO = REPO / "research_inputs/biomass_v5"; DEM = REPO / "research_inputs/demand_v5"
CARS = ["coal", "oil", "gas", "biomass", "electricity", "hydrogen", "heat", "ammonia", "methanol", "heat_medium_a", "heat_medium_b", "heat_high"]
res = {}

for mode in ("ras", "iid"):
    od = V4 / f"out_{mode}"
    S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
    P = pd.read_csv(od / "INDUSTRY_2050_SUBSECTOR_CARRIER_V4.csv")
    snap = json.loads((od / "SNAPSHOT.json").read_text())
    ats = pd.read_csv(od / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False, dtype=str)
    ats["v50"] = pd.to_numeric(ats.value_2050_mwh, errors="coerce").fillna(0.0); ats["b19"] = pd.to_numeric(ats.base_2019_mwh, errors="coerce").fillna(0.0)
    an = pd.read_csv(od / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
    rows = []
    for c in S.index:
        T_sum = float(sum(S.at[c, f"pe_{k}_mwh"] for k in CARS))
        parts = P[P.country == c]
        parts_sum = float(parts.mwh_2050.sum()); other = float(parts[parts.subsector == "other"].mwh_2050.sum())
        neg = parts[(parts.subsector == "other") & (parts.mwh_2050 < -1e-9)]
        snapc = snap["countries"].get(c, {})
        ind = ats[(ats.country == c) & (ats.sector == "Industry")]
        rows.append(dict(country=c, T_summary_mwh=T_sum, parts_sum_mwh=parts_sum, diff_mwh=parts_sum - T_sum, other_mwh=other, other_negative_cells=len(neg),
                         snapshot_T_mwh=snapc.get("T"), snapshot_other_mwh=snapc.get("other"), ats_industry_2050_mwh=float(ind.v50.sum()), ats_industry_2019_mwh=float(ind.b19.sum()),
                         products_2050_mwh=snapc.get("prod50"), industry_anchor_mwh=float(an.at[c, "industry_anchor_mwh"]), industry_multiplier=float(an.at[c, "industry_multiplier"]),
                         ats_2050_minus_anchor_mwh=float(ind.v50.sum()) - float(an.at[c, "industry_anchor_mwh"]),
                         T_minus_ats_minus_products_mwh=T_sum - float(ind.v50.sum()) - float(snapc.get("prod50") or 0.0),
                         bio_before_overflow_mwh=float(S.at[c, "pe_biomass_before_overflow_mwh"]), overflow_mwh=float(S.at[c, "biomass_overflow_industry_mwh"]) if "biomass_overflow_industry_mwh" in S.columns else None,
                         pot_main_mwh=float(S.at[c, "solid_biomass_potential_main_mwh"]), meoh_dropped_mwh=snapc.get("meoh_dropped")))
    res[f"out_{mode}"] = dict(by_country=rows, asean_T_twh=sum(r["T_summary_mwh"] for r in rows) / 1e6, asean_other_twh=sum(r["other_mwh"] for r in rows) / 1e6,
                              switch_record=json.loads((od / "V4_SWITCHES.json").read_text())["asean_T_v2_TWh"])
    # NEU: BN methanol gas deduction; NEU rows 2019 -> 2050 multiplier
    neu = ats[(ats.sector == "NonEnergyUse")]
    res[f"out_{mode}"]["neu_by_country_2050_twh"] = neu.groupby("country").v50.sum().div(1e6).round(4).to_dict()
    bn = neu[(neu.country == "BN") & (neu.carrier == "gas")]
    res[f"out_{mode}"]["bn_neu_gas_rows"] = bn[["account", "base_2019_mwh", "value_2050_mwh", "growth_method"]].to_dict("records")
    # transport: rail parent / children, land fuel, EV
    tr = ats[ats.sector == "Transport"]
    res[f"out_{mode}"]["rail_parent_2050_twh"] = tr[tr.account == "TransportEmbeddedFuelParent"].groupby("country").v50.sum().div(1e6).round(6).to_dict()
    res[f"out_{mode}"]["rail_child_2050_twh"] = tr[tr.account == "RailNonElectric"].groupby("country").v50.sum().div(1e6).round(4).to_dict()
    land = tr[tr.account.isin(["RoadResidualFuel", "TransportNEC"]) & (tr.carrier != "electricity")]
    res[f"out_{mode}"]["land_fuel_2050_twh"] = land.groupby("country").v50.sum().div(1e6).round(4).to_dict()
    res[f"out_{mode}"]["ev_2050_twh_x0.30215"] = (land.groupby("country").v50.sum() * 0.30215 / 1e6).round(4).to_dict()

# residue symmetry: demand side (2019 removed, x industry multiplier of the mode) vs potential side (2050 deduction)
rr = pd.read_csv(V4 / "RESIDUE_RECORDS_2019.csv", dtype={"tx": str, "code": str})
adj = pd.read_csv(BIO / "BIOMASS_POTENTIAL_ADJ_V4.csv")
an_ras = pd.read_csv(V4 / "out_ras/DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
cov = pd.read_csv(V4 / "NATIONAL_BALANCE_BIOMASS_COVERAGE.csv").set_index("country")
sym = []
for c in sorted(set(rr.country)):
    a = rr[(rr.country == c) & (rr.cls == "a")]
    d19 = float(a.mwh.sum()); m = float(an_ras.at[c, "industry_multiplier"])
    cats = adj[(adj.country == c) & (adj.category != "TOTAL solid")]
    f4 = float(cats.F4_self_use_TWh.sum()) * 1e6; f3 = float(cats.F3_bagasse_R2_TWh.sum()) * 1e6
    bag = float(a[a.code == "5120"].mwh.sum()); bl = float(a[a.code == "5140"].mwh.sum()); r5150 = float(a[a.code == "5150"].mwh.sum())
    sym.append(dict(country=c, demand_removed_2019_mwh=d19, bagasse_2019=bag, black_liquor_2019=bl, residues_5150_2019=r5150, industry_multiplier_ras=m,
                    demand_removed_2050_at_multiplier_mwh=d19 * m, potential_F4_deduction_2050_mwh=f4, potential_F3_mwh=f3,
                    balance_contains=str(cov.at[c, "balance_contains_self_produced_residues"]), anchor_deducted=(str(cov.at[c, "balance_contains_self_produced_residues"]) == "as_unsd"),
                    rules="; ".join(sorted(set(x for x in cats.rule if isinstance(x, str) and x)))))
res["residue_symmetry"] = sym
# pulp and paper: closed loop outside T_v2
items = pd.read_csv(V4 / "PRODUCT_ITEMS_V4.csv", keep_default_na=False)
pp = items[items.name == "pulp_paper"]
res["pulp_paper"] = pp[["country", "fuel19_mwh", "el19_mwh", "v2050_total_mwh", "v2050_biomass_mwh", "closed_loop_bl19_mwh", "closed_loop_bl50_mwh"]].to_dict("records")
# captive coal
cap = pd.read_csv(V4 / "CAPTIVE_COAL_2019.csv", keep_default_na=False)
res["captive"] = [dict(country=r.country, coal_kt=float(r.coal_kt), gj_per_t=(float(r.gj_per_t) if r.gj_per_t != "" else None),
                       coal_mwh=(float(r.coal_kt) * float(r.gj_per_t) / 3.6 * 1e3 if r.gj_per_t != "" else 0.0),
                       e_mwh=(float(r.e_mwh) if r.e_mwh != "" else (float(r.e_gwh) * 1e3 if r.e_gwh != "" else 0.0))) for r in cap.itertuples() if float(r.coal_kt) > 0]
json.dump(res, open(OUT, "w"), indent=1, default=float)
for m in ("out_ras", "out_iid"):
    df = pd.DataFrame(res[m]["by_country"])
    print(m, "ASEAN T", round(res[m]["asean_T_twh"], 6), "record", round(res[m]["switch_record"], 6), "| max |parts-T|", float(df.diff_mwh.abs().max()), "| negative other cells", int(df.other_negative_cells.sum()),
          "| max |T - ATS - products|", float(df.T_minus_ats_minus_products_mwh.abs().max()))
    print(df[["country", "T_summary_mwh", "ats_industry_2050_mwh", "products_2050_mwh", "industry_anchor_mwh", "ats_2050_minus_anchor_mwh", "bio_before_overflow_mwh", "overflow_mwh", "pot_main_mwh"]].round(1).to_string())
    print("rail parent 2050", res[m]["rail_parent_2050_twh"]); print("BN NEU gas rows", res[m]["bn_neu_gas_rows"])
print(pd.DataFrame(sym)[["country", "demand_removed_2019_mwh", "demand_removed_2050_at_multiplier_mwh", "potential_F4_deduction_2050_mwh", "potential_F3_mwh", "anchor_deducted"]].round(0).to_string())
