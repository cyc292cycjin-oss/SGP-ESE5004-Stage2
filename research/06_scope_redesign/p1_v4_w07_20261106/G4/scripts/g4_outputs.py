"""G4 A6 outputs (V4 W07 B-G4) from the facts and chain results: <CC>_SUBSECTORS_V4.csv, <CC>_CAPTIVE.csv, <CC>_BIOMASS_CHECK.csv,
<CC>_NODE_SHARES.csv, <CC>_MISSING_DATA.csv for MM, KH, LA, BN, TL, and the merged EVIDENCE.json (facts + chain + outputs).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python -I scripts/g4_outputs.py        (WSL)

Node assignment of the new explicit products: facility coordinates (SFI pulp & paper 2025-07, Climate TRACE V5.12.0 copper mines) point in the
v3 onshore regions (regions_onshore.geojson of the main checkout, as S2), nearest region centroid otherwise; compared with the v2 node shares
that the 'other' bucket uses in these countries (INDUSTRY_NODE_ALLOCATION_V2_V3.csv, v2_twh).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g4_common as cm   # noqa: E402

E = cm.G4 / "evidence"
EV = cm.Ev("outputs")
CI = json.loads((E / "_chain_inputs.json").read_text())
SC = pd.read_csv(E / "G4_SCENARIOS.csv")
PARTS = pd.read_csv(E / "G4_PARTS_2050_MAIN.csv")
PZ = pd.read_csv(E / "G4_S3_SUBSECTORS_MAIN.csv")
CAR = ["electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "oil", "gas", "coal", "biomass", "hydrogen", "ammonia", "methanol"]


def sc(name, scheme, c, q):
    z = SC[(SC.scenario == name) & (SC.ncv_scheme == scheme) & (SC.country == c)]
    return float(z[q].iloc[0])


MAIN = ("4 products (closed loop)", "207")


# ------------------------------------------------------------------ SUBSECTORS -------------------------------------------------------------
def subsectors():
    rule = cm.rule(); ob = pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_BASE_M08B.csv").set_index("country")
    cem = pd.read_csv(E / "CEMENT_CLINKER_G4.csv").set_index("iso"); pm = json.loads((E / "_chain_evidence.json").read_text())["extra"]["product_moves_main_2019_mwh"]
    bn = pd.read_csv(E / "BN_CHEMICALS_DIFFERENCE_G4.csv")
    meta = {
        "steel": ("EAF (v3 rule)", "worldsteel 2024 crude steel (INDUSTRY_OUTPUT_BASE_M08B)", "PyPSA-Eur 2050 30 % H2-DRI + 70 % scrap EAF (v3)", "iron and steel (UNSD) / other", "B"),
        "cement": ("clinker + grinding", "USGS MYB 2023 T22 (2023 base, e); 2019: kiln on EDGAR clinker, grinding on USGS 2019 (correction ii)", "PyPSA-Eur Cement 0.8655 MWh/t", "non-metallic minerals (UNSD) then other", "C"),
        "dispersed": ("UNSD row x EU27 weights (v3)", "UNSD 2019 sub-sector rows x ATS multiplier", "PyPSA-Eur sectors x efficiency factor (v3)", "same-name UNSD rows", "C"),
        "other": ("residual (D163-6 a)", "T_v2 - explicit", "s3_0 heat-band conversion (v3)", "-", "C"),
        "MM_paper": ("paper (recovered fibre, case materials)", "FAOSTAT FO, last year with new information (2023 / 2024, A)", "JRC-IDEES today 2.581 MWh/t (2019); PyPSA-Eur Paper production 2050", "paper pulp and print (UNSD gas) then other", "B / C"),
        "MM_pulp": ("non-wood pulp", "FAOSTAT FO 'Pulp from fibres other than wood' (2024, A)", "JRC-IDEES today 3.567 MWh/t; PyPSA-Eur Pulp production 2050", "paper pulp and print then other", "B / C"),
        "MM_copper": ("SX-EW cathode (refined primary)", "USGS MYB 2017-18 AP T3: 153 kt 2018 (no later value on disk); 2019 by R3", "JRC-IDEES today 3.639 MWh/t; PyPSA-Eur Other non-ferrous metals 2050 (v3 rule for ID copper)", "non-ferrous metals (UNSD gas) then other", "B / C"),
        "LA_pulp": ("chemical + dissolving pulp (Sun Paper Savannakhet)", "FAOSTAT FO 2019 286 kt (E); base 2023 323 kt (E)", "JRC-IDEES today 3.567 MWh/t; PyPSA-Eur Pulp production 2050", "other (no UNSD paper row)", "C"),
        "LA_copper": ("SX-EW cathode (refined primary)", "USGS MYB 2017-18 AP T3: 68 kt 2018; 2019 by R3", "JRC-IDEES today 3.639 MWh/t; PyPSA-Eur Other non-ferrous metals 2050", "other", "B / C")}
    for c in cm.C5:
        P = PARTS[PARTS.country == c].pivot_table(index="subsector", columns="carrier", values="mwh_2050", aggfunc="sum").fillna(0.0)
        pz = PZ[PZ.country == c].groupby("subsector").mwh_2019.sum()
        rows = []
        for sub in P.index:
            m = meta.get(sub, ("", "", "", "", "C"))
            if sub == "steel":
                ab, a50, by = ob.at[c, "steel_base_kt"] * 1e3, float(rule.at[c, "steel_2050_mt"]) * 1e6, int(ob.at[c, "steel_base_year"]); e19 = float(pz.get("iron and steel", 0.0))
            elif sub == "cement":
                ab, a50, by = ob.at[c, "cement_base_kt"] * 1e3, float(rule.at[c, "cement_2050_mt"]) * 1e6, int(ob.at[c, "cement_base_year"]); e19 = float(pz.get("cement", 0.0))
            elif sub in CI["products"]:
                d = CI["products"][sub]; ab, a50, by = d["q2019_t"], d["q2050_t"], ("2023/2024" if "paper" in sub or "pulp" in sub else 2018)
                e19 = sum(v[2] for v in pm.get(sub, {}).get("moves", []))
            else:
                ab = a50 = np.nan; by = 2019; e19 = np.nan
            r = dict(subsector=sub, route=m[0], activity_source=m[1], base_year=by, activity_base=ab, activity_2050=a50, sec_source=m[2],
                     energy_2019_deducted_TWh=e19 / 1e6 if pd.notna(e19) else np.nan, deducted_from_row=m[3], energy_2050_TWh=float(P.loc[sub].sum()) / 1e6)
            for k in CAR:
                r[cm.OUT_LABEL[k]] = float(P.loc[sub].get(k, 0.0)) / 1e6
            r["closed_loop_biomass_TWh"] = CI["products"][sub]["v2050_closed_loop_biomass"] / 1e6 if sub in CI["products"] else 0.0
            r["closed_loop_biomass_2019_TWh"] = CI["products"][sub]["e2019_closed_loop_biomass"] / 1e6 if sub in CI["products"] else 0.0
            r["counted_in_T_v2"] = "yes"
            r["grade"] = m[4]
            if c == "BN" and sub == "cement":
                r.update(route="grinding only (iii): no clinker kiln in BN (GEM: one grinding plant)", activity_source="USGS T22 2023 324 kt (e); 2019 100 kt (r, e) for grinding electricity; EDGAR 2.A.1 set to 0")
            rows.append(r)
        # not counted
        if c == "BN":
            for z in bn.itertuples():
                rows.append(dict(subsector=f"chemicals: {z.Product} ({z._2})", route="GEM GCT 2026-11 operating capacity x 0.85 x ETSAP BAT energy", activity_source=f"GEM capacity {z.cap:.0f} kt, start {z.start_year:.0f}",
                                 base_year=2019, activity_base=z.cap * 1e3 * 0.85, activity_2050=np.nan, sec_source=f"ETSAP BAT energy {z.bat_energy_gj_per_t:.2f} GJ/t (feedstock {z.bat_feedstock_gj_per_t:.1f} GJ/t outside T_v2)",
                                 energy_2019_deducted_TWh=0.0, deducted_from_row="not deducted (decision 202 item 4)", energy_2050_TWh=0.0, counted_in_T_v2="no (decision 202 item 4: difference table)",
                                 grade="C", note=f"energy use at u = 0.85: {z.energy_use_at_capacity_u085_twh:.3f} TWh (2019 operating: {bool(z.operating_2019)})"))
        if c == "MM":
            t = CI["mm_ammonia_2018_t"]
            rows.append(dict(subsector="ammonia (not counted)", route="gas SMR urea plants (GEM: 3 operating, 369 kt)", activity_source="USGS AP T3 2018 N content of ammonia 53 kt -> 64.4 kt NH3",
                             base_year=2018, activity_base=t, activity_2050=t * cm.growth(2018, "MM"), sec_source="v3 product rule 5.166 MWh NH3/t; feedstock 10.8 MWh/t in NEU",
                             energy_2019_deducted_TWh=0.0, deducted_from_row="(would be chemical and petrochemical row, gas 1.63 TWh)", energy_2050_TWh=t * cm.growth(2018, "MM") * 5.166 / 1e6,
                             ammonia=t * cm.growth(2018, "MM") * 5.166 / 1e6, counted_in_T_v2="no (sensitivity; 2019 output not on disk)", grade="B (2018) / C"))
        if c == "LA":
            d = CI["products"]["LA_paper_R4"]
            rows.append(dict(subsector="LA_paper_R4 (not counted)", route="packaging paper (new line after 2019)", activity_source="FAOSTAT FO case materials 2021-2023 (E), 0 in 2019",
                             base_year=2023, activity_base=1.01e6, activity_2050=d["q2050_t"], sec_source="PyPSA-Eur Paper production 2050", energy_2019_deducted_TWh=0.0,
                             deducted_from_row="none (not in the 2019 base)", energy_2050_TWh=sum(d["v2050_counted"].values()) / 1e6, closed_loop_biomass_TWh=d["v2050_closed_loop_biomass"] / 1e6,
                             counted_in_T_v2="no (R4 sensitivity)", grade="C"))
            rows.append(dict(subsector="potash (not counted)", route="solution mining + crystallisation", activity_source="USGS AP T3 2018 335 kt K2O", base_year=2018, activity_base=CI["la_potash_2018_t_k2o"],
                             sec_source="no unit energy on disk", counted_in_T_v2="no (stays in other; data gap)", grade="B / E"))
        if c == "TL":
            rows = [dict(subsector="none", route="-", activity_source="UNSD 2019: no industry consumption transaction for any commodity; GEM / USGS: no cement, steel, chemicals",
                         base_year=2019, energy_2019_deducted_TWh=0.0, energy_2050_TWh=0.0, counted_in_T_v2="-", grade="A")]
        D = pd.DataFrame(rows)
        D.to_csv(cm.G4 / f"{c}_SUBSECTORS_V4.csv", index=False, float_format="%.6g")
        for r in D.itertuples():
            EV.put(f"subsectors.{c}.{r.subsector}.energy_2050_TWh", float(r.energy_2050_TWh) if pd.notna(r.energy_2050_TWh) else 0.0, "TWh",
                   "evidence/G4_PARTS_2050_MAIN.csv (scheme 207 full main case)", "EXACT" if r.counted_in_T_v2 == "yes" else "INFERENCE", str(r.grade))


# ------------------------------------------------------------------ CAPTIVE ----------------------------------------------------------------
def captive():
    scr = pd.read_csv(cm.S2W / "s2/ASEAN11_CAPTIVE_SCREEN.csv").set_index("iso")
    M = pd.read_csv(E / "MM_CAPTIVE_COAL_2019.csv").set_index("level")
    eff = lambda name: sc(MAIN[0], "207", "MM", "T_v2_2050_TWh") - sc(name, "207", "MM", "T_v2_2050_TWh")
    for c in cm.C5:
        s = scr.loc[c]
        r = dict(country=c, inequality_result=s.verdict, autoproducer_combustible_gwh_2019=s.autoproducer_combustible_gwh, fuel_in_transformation_twh=s.fuel_in_transformation_twh,
                 gipt_captive_MW_2019=s.gipt_captive_coal_2019_mw, gipt_captive_types=s.gipt_captive_coal_types_2019 if isinstance(s.gipt_captive_coal_types_2019, str) else "")
        if c == "MM":
            r.update(C_low_kt=M.at["low", "coal_kt"], C_low_TWh_v3=M.at["low", "c_twh_v3"], C_low_TWh_207=M.at["low", "c_twh_207"],
                     C_central_kt=M.at["low", "coal_kt"], C_central_TWh_v3=M.at["low", "c_twh_v3"], C_central_TWh_207=M.at["low", "c_twh_207"],
                     C_mid_kt=M.at["mid", "coal_kt"], C_mid_TWh_207=M.at["mid", "c_twh_207"], C_high_kt=M.at["high", "coal_kt"], C_high_TWh_v3=M.at["high", "c_twh_v3"], C_high_TWh_207=M.at["high", "c_twh_207"],
                     E_central_TWh=M.at["low", "gen_twh"], E_mid_TWh=M.at["mid", "gen_twh"], E_high_TWh=M.at["high", "gen_twh"],
                     central_rule="central = low: (1) v3 already logs the UNSD non-metallic minerals row 1.42 TWh below the activity-based kiln fuel, captive coal inside that row widens "
                                  "the shortfall (low 1.90, mid 2.94, high 3.37 TWh); (2) Mawlamyine 40 MW is mothballed (date unknown); (3) MM autoproducer rows hold gas only. "
                                  "Tigyit 120 MW (GIPT 'iron & steel') burns coal recorded in electricity-plant transformation (1,382 kt), not in industry: C = 0 for Tigyit",
                     option_b_effect_2050_TWh_207=-eff("S captive (a) none"),
                     option_b_effect_2050_TWh_v3=sc("2 captive (b) central", "v3", "MM", "T_v2_2050_TWh") - sc("1 ncv", "v3", "MM", "T_v2_2050_TWh"),
                     option_b_mid_effect_2050_TWh_207=sc("S captive mid", "207", "MM", "T_v2_2050_TWh") - sc("S captive (a) none", "207", "MM", "T_v2_2050_TWh"),
                     option_b_high_effect_2050_TWh_207=sc("S captive high", "207", "MM", "T_v2_2050_TWh") - sc("S captive (a) none", "207", "MM", "T_v2_2050_TWh"),
                     hours_source=M.at["low", "hours_source"] + " | mid: " + M.at["mid", "hours_source"] + " | high: " + M.at["high", "hours_source"],
                     heat_rate_source=M.at["low", "heat_rate_source"], grade="C (INFERENCE / PROPOSED)")
        elif c == "BN":
            r.update(C_low_kt=0.0, C_central_kt=0.0, C_high_kt=0.0, C_central_TWh_v3=0.0, C_central_TWh_207=0.0, E_central_TWh=0.0,
                     central_rule="no captive fuel left in industry: Hengyi PMB 4 x 55 MW (GIPT, 2019, 'chemicals') coal = UNSD autoproducer transformation 341.064 kt (brown coal); "
                                  "BN industry coal 0; autoproducer output 911.9 GWh and chemicals electricity 507.7 GWh already recorded -> UNSD already in the option (b) state",
                     option_b_effect_2050_TWh_207=0.0, option_b_effect_2050_TWh_v3=0.0, grade="B (EXACT: industry coal 0)")
        else:
            r.update(C_low_kt=0.0, C_central_kt=0.0, C_high_kt=0.0, C_central_TWh_v3=0.0, C_central_TWh_207=0.0, E_central_TWh=0.0,
                     central_rule=("no autoproducer rows in UNSD 2019 and no GIPT captive unit operating in 2019 (KH Sihanoukville SEZ 2 x 50 MW start 2021 / 2022, not captive-flagged)" if c == "KH" else
                                   "no autoproducer rows in UNSD 2019 and no GIPT captive unit (Hongsa is a main-activity IPP)" if c == "LA" else "no industry, no autoproducer rows"),
                     option_b_effect_2050_TWh_207=0.0, option_b_effect_2050_TWh_v3=0.0, grade="B")
        pd.DataFrame([r]).to_csv(cm.G4 / f"{c}_CAPTIVE.csv", index=False, float_format="%.6g")
        for k in ("gipt_captive_MW_2019", "C_central_kt", "C_central_TWh_207", "E_central_TWh", "option_b_effect_2050_TWh_207"):
            if k in r and pd.notna(r[k]):
                EV.put(f"captive.{c}.{k}", float(r[k]), k.split("_")[-1], "g4_facts.py / g4_chain.py", "INFERENCE" if c == "MM" and k != "gipt_captive_MW_2019" else "VERIFIED", "C" if c == "MM" else "B")


# ------------------------------------------------------------------ BIOMASS -------------------------------------------------------------------
def biomass():
    S = pd.read_csv(E / "BIOMASS_SERIES_G4.csv"); cf = cm.conv_factors()
    eff = lambda name, c: sc(name, "207", c, "T_v2_2050_TWh") - sc(MAIN[0], "207", c, "T_v2_2050_TWh")
    ind = "Consumption by manufacturing, construction and non-fuel industry"

    def ser(c, com, tr, col="export_q", y0=2005, y1=2022):
        z = S[(S.iso == c) & (S.commodity == com) & (S.transaction == tr) & S.year.between(y0, y1)]
        return ";".join(f"{int(r.year)}:{getattr(r, col):.0f}{('*' if (isinstance(r.export_footnote, str) and r.export_footnote) else '')}" for r in z.itertuples() if pd.notna(getattr(r, col)))
    v = lambda c, com, tr, y, col="export_q": float(S[(S.iso == c) & (S.commodity == com) & (S.transaction == tr) & (S.year == y)][col].sum())
    T = {
        "MM": [
            dict(commodity="Fuelwood (5110)", flow="industry n.e.s.", value_2019=f"{v('MM', 'Fuelwood', ind, 2019):.1f} thousand m3 = {v('MM', 'Fuelwood', ind, 2019) * cf['Fuelwood']:.2f} TWh",
                 series_note="equal to commerce and public services in every year 2005-2021 (17 years); footnote Estimate 2005-2017 and 2022; export 2022 drops to 1,131 (households 34,578) "
                             "while SDMX 2022 shows 6,200 (A): a fixed allocation rule, not a measurement (INFERENCE); no 2018-19 jump. " + ser("MM", "Fuelwood", ind, y0=2015),
                 faostat_compare=f"UNSD production {v('MM', 'Fuelwood', 'Production', 2019):.0f} vs FAO wood fuel 38,286 thousand m3 (E, constant 2010-2024: carry-forward, grade D); FAO total only",
                 proposed_main="keep UNSD 2019 (stable series, no break before 2022)", proposed_sensitivity=f"SDMX 2022 level 6,200: 2050 T_v2 {eff('S MM fuelwood at SDMX 2022 level', 'MM'):+.2f} TWh"),
            dict(commodity="Bagasse (5120)", flow="industry n.e.s.", value_2019="1,145 kt (export) / 850 kt (SDMX, E) = 2.45 / 1.82 TWh at 7.72 GJ/t",
                 series_note="footnote Estimate 2011-2017; sugar cane 11.85 Mt (FAOSTAT 2019 A) -> 0.097 t bagasse per t cane (export) vs 0.2-0.3 typical: low", faostat_compare="FAOSTAT QCL sugar cane 11,846 kt (A)",
                 proposed_main="keep (UNSD-reported, in T_v2, as v3 and S2 for ID)", proposed_sensitivity=f"closed loop (outside T_v2): {eff('S bagasse closed loop (MM, LA)', 'MM'):+.2f} TWh; SDMX vintage 850 kt: {eff('S MM bagasse SDMX vintage (850 kt)', 'MM'):+.2f} TWh"),
            dict(commodity="Black liquor (5140)", flow="-", value_2019="not reported (export and SDMX)", series_note="MM pulp: non-wood 1 kt only", faostat_compare="-", proposed_main="nothing to do", proposed_sensitivity="-"),
            dict(commodity="Other vegetal material and residues (5150)", flow="industry n.e.s.", value_2019="33,900 TJ = 9.42 TWh (SDMX, A); NOT in the UNdata export used by the model",
                 series_note="SDMX 2017-2022: 33,938 / 36,638 / 33,900 / 30,925 / 28,750 / 29,045 TJ (A); likely rice husk and mill residues (INFERENCE; MM paddy 26.7 Mt)",
                 faostat_compare="-", proposed_main="outside T_v2 (closed loop, decision 206 item 3; consistent with the export omission)", proposed_sensitivity=f"added as purchased fuel: {eff('S MM other vegetal residues 5150 added (9.42 TWh)', 'MM'):+.2f} TWh"),
            dict(commodity="Charcoal (5160)", flow="households only", value_2019="44.4 kt", series_note="no industry use", faostat_compare="FAO wood charcoal 438 kt (E) vs UNSD 44 kt", proposed_main="-", proposed_sensitivity="-")],
        "KH": [
            dict(commodity="Fuelwood (5110)", flow="industry n.e.s.", value_2019=f"979.3 thousand m3 = {979.3 * cf['Fuelwood']:.2f} TWh",
                 series_note="smooth rise to 1,185 (2016), then decline; 2020: industry -153, households +624 with footnote Estimate 2020-2022 (re-estimation). " + ser("KH", "Fuelwood", ind, y0=2015),
                 faostat_compare="FAO wood fuel = UNSD production from 2020 (7,117,174 m3 both): same estimate; 2019 FAO 7,240 vs UNSD 6,957", proposed_main="keep UNSD 2019",
                 proposed_sensitivity=f"2020-2022 mean 839 thousand m3: {eff('S KH fuelwood 2020-2022 mean', 'KH'):+.2f} TWh"),
            dict(commodity="Bagasse / black liquor / 5150", flow="-", value_2019="no bagasse or black liquor; 5150 1,387.5 TJ only to main-activity power (rice husk), not industry",
                 series_note="KH sugar cane 618 kt (FAOSTAT A); mills burn bagasse unrecorded (closed loop)", faostat_compare="-", proposed_main="nothing to add (closed loop)", proposed_sensitivity="-")],
        "LA": [
            dict(commodity="Fuelwood (5110)", flow="industry n.e.s.", value_2019="225 thousand m3 (Estimate) = 0.57 TWh", series_note="flat 200-228 since 2005, Estimate 2016-2023. " + ser("LA", "Fuelwood", ind, y0=2015),
                 faostat_compare="FAO wood fuel = UNSD production (5,732,171 m3): same estimate", proposed_main="keep", proposed_sensitivity="none: LA 'other' fuel is fully absorbed by the v3 cement deduction (no T_v2 effect)"),
            dict(commodity="Bagasse (5120)", flow="industry n.e.s.", value_2019="426 kt (Estimate) = 0.91 TWh", series_note="Estimate 2009-2023; sugar cane 1.49 Mt (FAOSTAT A) -> 0.29 t/t",
                 faostat_compare="FAOSTAT QCL sugar cane 1,490 kt (A)", proposed_main="keep", proposed_sensitivity=f"closed loop: {eff('S bagasse closed loop (MM, LA)', 'LA'):+.2f} TWh (absorbed by the cement gap)"),
            dict(commodity="Black liquor (5140) / 5150", flow="-", value_2019="not reported", series_note="LA kraft / dissolving pulp mill (FAOSTAT 286 kt 2019, E): black liquor unrecorded = closed loop",
                 faostat_compare="-", proposed_main="pulp biomass listed separately (closed loop)", proposed_sensitivity="-")],
        "BN": [dict(commodity="Fuelwood / charcoal", flow="households only", value_2019="9.65 thousand m3; charcoal 0.61 kt", series_note="Estimate every year; no industry biomass",
                    faostat_compare="FAO wood fuel = UNSD production (11,642 m3)", proposed_main="nothing to change", proposed_sensitivity="-")],
        "TL": [dict(commodity="Fuelwood", flow="households only", value_2019="81.2 thousand m3", series_note="Estimate every year; no industry", faostat_compare="FAO = UNSD", proposed_main="nothing", proposed_sensitivity="-")]}
    for c, rows in T.items():
        pd.DataFrame(rows).to_csv(cm.G4 / f"{c}_BIOMASS_CHECK.csv", index=False)
        for i, r in enumerate(rows):
            EV.put(f"biomass.{c}.{i}.proposed_main", r["proposed_main"], "-", r["series_note"][:120], "PROPOSED", "-")


# ------------------------------------------------------------------ NODE SHARES -------------------------------------------------------------
def nodes():
    import geopandas as gpd
    from shapely.geometry import Point
    reg = gpd.read_file(cm.MAIN / "research_inputs/renewable_v5/regions_onshore.geojson")
    ncol = "name" if "name" in reg.columns else reg.columns[0]
    v3s = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv")
    alloc = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_NODE_ALLOCATION_V2_V3.csv").drop_duplicates()
    v2 = {c: (g.set_index("node").v2_twh / g.v2_twh.sum()) for c, g in alloc.groupby("country")}
    W = cm.S2W
    sfi = pd.read_excel(W / "downloads/04_sfi_pulp_paper/SFI_ALD_Pulp_Paper_Database_July_2025.xlsx", sheet_name="SFI_Pulp_Paper_Database")
    fac = []
    for r in sfi[sfi.iso3.isin(["MMR", "LAO"])].itertuples():
        c = {"MMR": "MM", "LAO": "LA"}[r.iso3]
        subs = {"MM": ["MM_paper"] + (["MM_pulp"] if "Pulp" in str(r.plant_type) else []), "LA": (["LA_pulp"] if "Pulp" in str(r.plant_type) else [])}[c]
        for s in subs:
            fac.append(dict(country=c, subsector=s, facility=r.plant_name, lat=r.latitude, lon=r.longitude, weight=1.0, source="SFI 2025-07 (equal weights, no capacity values; D)"))
    ct = pd.read_parquet(W / "extracted/06_climate_trace/copper-mining/DATA/copper-mining_emissions_sources_v5_12_0.parquet") if (W / "extracted/06_climate_trace/copper-mining/DATA/copper-mining_emissions_sources_v5_12_0.parquet").exists() else None
    if ct is None:
        import glob
        f = glob.glob(str(W / "extracted/06_climate_trace/**/copper-mining_emissions_sources_v5_12_0.parquet"), recursive=True)[0]
        ct = pd.read_parquet(f)
    ct = ct.drop_duplicates(subset=["source_name"])
    for nm, c, s in (("Letpadaung Mine", "MM", "MM_copper"), ("Sabetaung & Kyisintaung Mine", "MM", "MM_copper"), ("Sepon Mine", "LA", "LA_copper")):
        z = ct[ct.source_name == nm].iloc[0]
        fac.append(dict(country=c, subsector=s, facility=nm, lat=z.lat, lon=z.lon, weight=float(z.capacity), source="Climate TRACE V5.12.0 copper mine (location; capacity as weight, D)"))
    F = pd.DataFrame(fac)
    pts = gpd.GeoDataFrame(F, geometry=[Point(xy) for xy in zip(F.lon, F.lat)], crs="EPSG:4326")
    j = gpd.sjoin(pts, reg[[ncol, "geometry"]].to_crs("EPSG:4326"), how="left", predicate="within")
    j = j[~j.index.duplicated()]
    F["node"] = j[ncol].values; F["node_method"] = np.where(F.node.notna(), "point in region", "nearest region")
    for i in F[F.node.isna()].index:
        cand = reg[reg[ncol].astype(str).str.startswith(F.at[i, "country"])]
        d = cand.geometry.centroid.distance(Point(F.at[i, "lon"], F.at[i, "lat"]))
        F.at[i, "node"] = cand.loc[d.idxmin(), ncol]
    F.to_csv(E / "NEW_PRODUCT_FACILITY_NODES_G4.csv", index=False)
    for c in cm.C5:
        rows = []
        for r in v3s[v3s.country == c].itertuples():
            rows.append(dict(subsector=r.subsector, node=r.node, share_v4=r.share, share_v3=r.share, diff_pp=0.0, note="unchanged (v3 GEM / facility weights)"))
        if c in v2:
            for n_, s_ in v2[c].items():
                rows.append(dict(subsector="other (and dispersed)", node=n_, share_v4=s_, share_v3=s_, diff_pp=0.0, note="unchanged: v2 rule (IndustryFinalEnergy node electricity shares)"))
        for s in sorted(F[F.country == c].subsector.unique()):
            g = F[(F.country == c) & (F.subsector == s)]
            sh = g.groupby("node").weight.sum() / g.weight.sum()
            for n_, x in sh.items():
                o = float(v2[c].get(n_, 0.0)) if c in v2 else 0.0
                rows.append(dict(subsector=s, node=n_, share_v4=x, share_v3=o, diff_pp=(x - o) * 100,
                                 note=f"new explicit sub-sector; share_v3 = v2 'other' share of the node (where this energy sat in v3); {'; '.join(g[g.node == n_].facility)}"))
        if not rows:
            rows.append(dict(subsector="none", node="-", share_v4=0.0, share_v3=0.0, diff_pp=0.0, note="no industrial demand"))
        D = pd.DataFrame(rows); D.to_csv(cm.G4 / f"{c}_NODE_SHARES.csv", index=False, float_format="%.6f")
        for r in D[D.diff_pp.abs() > 5].itertuples():
            EV.put(f"nodes.{c}.{r.subsector}.{r.node}.diff_pp", r.diff_pp, "pp", r.note[:150], "VERIFIED", "B / D")


# ------------------------------------------------------------------ MISSING DATA ------------------------------------------------------------
def missing():
    M = {
        "MM": [("UN Comtrade HS 252310 clinker imports / exports 2019-2023", "clinker ratio (EDGAR clinker = USGS cement x 0.786 by construction)", "https://comtradeplus.un.org/", "high"),
               ("MOEE / Myanmar Energy Statistics: autoproducer coal plants (Myainggalay, Mawlamyine) generation and coal 2019; Tigyit generation and coal", "captive coal C and Tigyit plausibility (1,382 kt vs 120 MW)", "", "high"),
               ("Myanmar national energy balance 2019 (ADB / MOEE / ERIA)", "fuelwood industry = commerce allocation; 5150 residues; coal rank and NCV", "", "high"),
               ("USGS Minerals Yearbook Burma chapter 2019-2022 (country tables)", "copper cathode, ammonia, cement 2019 actuals (current base 2018 AP table)", "https://www.usgs.gov/centers/national-minerals-information-center/asia-and-pacific", "medium"),
               ("MPCI / paper mill energy data", "paper unit energy (recovered fibre)", "", "low"),
               ("Coal quality data (MM coal NCV, Tigyit lignite)", "decision 207 physical evidence for MM coal", "", "medium")],
        "KH": [("UN Comtrade HS 252310 clinker imports 2019-2023", "clinker ratio / kiln fuel (GEM clinker capacity known for 2 of 6 plants: 3.33 Mt vs 7.4 Mt cement)", "https://comtradeplus.un.org/", "high"),
               ("GEM GCCT clinker capacity of the 4 plants without values / KH cement association", "clinker production 2019", "", "medium"),
               ("Cambodia energy balance 2019 (MME / EAC / ERIA): industrial fuelwood by sub-sector, coal by sub-sector", "fuelwood revision 2020; coal NCV (imports, Indonesian sub-bituminous)", "", "medium")],
        "LA": [("UN Comtrade HS 252310 / 2523 clinker and cement trade 2019-2024", "EDGAR 2024 implied clinker 1.43 x USGS 2023 cement (export of clinker?)", "https://comtradeplus.un.org/", "high"),
               ("Lao energy statistics / Lao energy balance 2019 (MEM, ERIA)", "industry rows (all LA industry is 'n.e.s.'), Estimate flags", "", "high"),
               ("USGS Minerals Yearbook Laos chapter 2019-2022; Lane Xang Minerals (Sepon) annual reports", "copper cathode 2019+ (continuation of SX-EW output), potash output", "https://www.usgs.gov/centers/national-minerals-information-center/asia-and-pacific", "high"),
               ("Potash processing unit energy (solution mining / crystallisation)", "potash 335 kt K2O stays in 'other' without a route", "", "medium"),
               ("Sun Paper Laos mill data (pulp and paper output, power and steam balance)", "pulp purchased electricity (self-generation from black liquor) and the 2021+ paper line", "", "medium")],
        "BN": [("Hengyi PMB refinery and aromatics: 2019-2022 throughput and fuel / power balance", "BN chemicals difference table (decision 202 item 4), coal own use from 2020", "", "medium"),
               ("BN cement grinding plant (clinker imports) data", "BN cement (iii) grinding only", "", "low"),
               ("Brunei energy balance 2019 (DES)", "NEU gas (methanol), refinery own use", "", "low")],
        "TL": [("Timor-Leste energy balance 2019 (if any)", "confirm no industrial fuel use (UNSD has none)", "", "low")]}
    for c, rows in M.items():
        pd.DataFrame(rows, columns=["item", "purpose", "url_if_known", "priority"]).to_csv(cm.G4 / f"{c}_MISSING_DATA.csv", index=False)


def merge_evidence():
    parts = []
    for f in ("_facts_evidence.json", "_chain_evidence.json", "_outputs_evidence.json"):
        d = json.loads((E / f).read_text())
        parts += d["numbers"]
    keys = [r["key"] for r in parts]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicated evidence keys across sections")
    by = pd.Series([r["status"] for r in parts]).value_counts().to_dict()
    cm.jdump(dict(instruction="V4_W07_INSTRUCTION.md v1 (SHA256 20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf), section B-G4",
                  count=len(parts), count_by_status=by, sections=["facts", "chain", "outputs"], numbers=parts), cm.G4 / "EVIDENCE.json")
    return len(parts), by


def main():
    subsectors(); captive(); biomass(); nodes(); missing()
    EV.write(E / "_outputs_evidence.json")
    n, by = merge_evidence()
    print("evidence", n, by)
    for c in cm.C5:
        print(c, pd.read_csv(cm.G4 / f"{c}_NODE_SHARES.csv").query("abs(diff_pp) > 0").round(3).to_string(index=False)[:1500])


if __name__ == "__main__":
    main()
