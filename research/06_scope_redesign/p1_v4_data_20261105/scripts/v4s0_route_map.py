"""V4 S0 section 5: V4_PRODUCT_ROUTE_MAP.csv - product -> route -> activity source -> base-year unit energy (ETSAP BAT x ODA inefficiency, or other)
-> carrier split -> 2050 route and carriers (PyPSA-Eur 2050 ratios, as in v3) -> UNSD row and v3 sub-sector, with the v3 overlap and a data grade per cell.

    python scripts/v4s0_route_map.py --work <work dir> --repo /home/jin/wt_v4_data

Numbers come from files (ETSAP BAT table and ODA factors written by v4s0_coverage.py; PyPSA-Eur 2050 and EU27 2019 ratio tables of the repo;
v3 dispersed rows written by v4s0_v3_status.py). Text columns are the S0 design (PROPOSED). Grades: A reported production / statistics at plant or
national level; B official capacity or national statistics with the route; C derived, proxy, EU or regional factor; D modelled estimate (Climate TRACE
activity = capacity x assumed factor); E missing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

GJ = 3.6
ROWS = [
    # product, route, v4 subsector, activity source(s), activity type, base year(s), ETSAP route, ETSAP subsector factor, carrier split (base), heat band of the fuel part,
    # PyPSA-Eur 2050 sector(s), UNSD row, v3 sub-sector, deduction rule, grades (activity, base SEC, split, 2050), notes
    dict(product="crude steel", route="BF-BOF", sub="steel", act="GEM GIST plant/units 2026-09 (capacity; plant production sparse); worldsteel national production (2024 in v3)",
         atype="capacity x utilisation calibrated to national production; plant production where reported", year="2024 (worldsteel), GEM status 2026",
         etsap="steel_bf_bof", fac="iron_steel", split="electricity; fuel (coal incl. BF coke/injection, gas, oil)", band="high (>400 C) for reheating; BF reductant is process fuel, not useful heat",
         pe="DRI + Electric arc (primary 30 %) + Electric arc (secondary 70 %), v3 rule", unsd="iron and steel", v3="steel", ded="explicit in v3: replace, not deduct",
         g=("B", "C", "C", "C"), note="UNSD iron-and-steel row excludes BF / coke-oven transformation where reported separately; ETSAP BF-BOF BAT includes the whole route -> compare on the same boundary"),
    dict(product="crude steel", route="DRI-EAF (gas)", sub="steel", act="GEM DRI furnaces (2 operating in ASEAN, MY / VN); ETSAP DRI 2018", atype="capacity x utilisation", year="2024 / 2026",
         etsap="steel_dri_eaf_gas", fac="iron_steel", split="electricity; gas (reductant + heat)", band="process gas = reductant (2050: hydrogen)", pe="DRI + Electric arc", unsd="iron and steel", v3="steel",
         ded="explicit in v3: replace", g=("B", "C", "C", "C"), note=""),
    dict(product="crude steel", route="scrap EAF / IF", sub="steel", act="GEM EAF / IF units; worldsteel", atype="capacity x utilisation", year="2024 / 2026", etsap="steel_secondary_eaf", fac="iron_steel",
         split="electricity; fuel (reheating, ladle)", band="high (>400 C)", pe="Electric arc", unsd="iron and steel", v3="steel", ded="explicit in v3: replace", g=("B", "C", "C", "C"),
         note="IF (induction) has no ETSAP route; use scrap EAF (grade C)"),
    dict(product="clinker / cement", route="dry kiln + finishing", sub="cement", act="GEM GCCT 2026-07 (cement / clinker capacity, 2024-2025 production for 8 ASEAN plants); USGS MYB 2023 T22 national",
         atype="clinker capacity x utilisation calibrated to USGS national cement; clinker / cement ratio per plant type", year="2023 (USGS), 2024-2025 (GEM production)", etsap="clinker+cement_finishing", fac="non_metallic_minerals",
         split="electricity; kiln heat (fuel)", band="high (>400 C)", pe="Cement", unsd="non-metallic minerals", v3="cement", ded="explicit in v3: replace", g=("B", "C", "B", "C"),
         note="ID: clinker capacity given for 15 of 46 operating plants -> clinker from cement capacity x plant-type ratio (C); ETSAP clinker share 0.6 vs technology-data 0.656 in v3"),
    dict(product="lime", route="lime kiln", sub="non-metallic minerals (other)", act="ETSAP 2018 (MY, TH, VN); Climate TRACE lime: no ASEAN asset", atype="national production", year="2018",
         etsap="lime", fac="non_metallic_minerals", split="electricity; kiln fuel", band="high (>400 C)", pe="Ceramics & other NMM (proxy; PyPSA-Eur has no lime sector)", unsd="non-metallic minerals",
         v3="dispersed (NMM rest) where the UNSD / APEC NMM row exists, else other", ded="dispersed NMM row if present, else other", g=("B", "C", "C", "C"), note="no facility locations -> node shares stay DOSE / electricity"),
    dict(product="glass", route="container / float", sub="non-metallic minerals (other)", act="ETSAP 2020 (PH, SG, TH, VN); Climate TRACE glass 11 assets (float only)", atype="national production; assets for location",
         year="2020", etsap="glass_container|glass_flat", fac="non_metallic_minerals", split="electricity; furnace fuel", band="high (>400 C)", pe="Glass production", unsd="non-metallic minerals",
         v3="dispersed (NMM rest) or other", ded="dispersed NMM row if present, else other", g=("B", "C", "C", "C"), note="Climate TRACE glass activity (IDN 0.03 Mt 2025) far below ETSAP national production: coverage poor"),
    dict(product="primary aluminium", route="Hall-Heroult", sub="non-ferrous", act="USGS MYB (ID 2019, MY AP 2018 est.); ETSAP 2018; Climate TRACE aluminum smelters", atype="national production; assets for location", year="2018-2019",
         etsap="aluminium_primary", fac="non_ferrous", split="electricity; anode coal (feedstock); fuel", band="anode = feedstock; casting fuel high", pe="Aluminium - primary production", unsd="non-ferrous metals",
         v3="nonferrous_aluminium_primary (ID, MY)", ded="explicit in v3 (ID, MY): replace; other countries: none produce", g=("B", "C", "C", "C"), note="ETSAP total includes alumina refining fuel; avoid double count with alumina row"),
    dict(product="alumina", route="Bayer", sub="non-ferrous", act="USGS MYB (ID 2019, VN); Climate TRACE aluminum refineries", atype="national production", year="2019", etsap="alumina_refining_fuel", fac="non_ferrous",
         split="fuel (digestion steam, calcination)", band="medium B (digestion 150-250 C) + high (calcination ~1000 C)", pe="Alumina production", unsd="non-ferrous metals", v3="nonferrous_alumina (ID); VN alumina not explicit",
         ded="ID explicit; VN: dispersed (no UNSD non-ferrous row) -> other", g=("B", "C", "C", "C"), note="ETSAP gives only refining fuel per t alumina"),
    dict(product="copper", route="pyro smelting + refining", sub="non-ferrous", act="USGS MYB (ID smelter 2019); ETSAP 2018 (ID, PH, VN, LA SX-EW)", atype="national production", year="2018-2019",
         etsap="copper_primary_smelting+copper_refining_casting", fac="non_ferrous", split="electricity; fuel", band="high (>400 C)", pe="Other non-ferrous metals", unsd="non-ferrous metals",
         v3="nonferrous_copper (ID); PH, VN not explicit", ded="ID explicit; PH / VN: other", g=("B", "C", "C", "C"), note=""),
    dict(product="nickel (NPI / ferronickel / matte)", route="RKEF", sub="non-ferrous", act="USGS MYB 2023 ID Table 1 (Ni content 2019 / 2023); GEM ferronickel capacity 0 in ASEAN", atype="national production", year="2019 (2023 sensitivity)",
         etsap="none (no nickel route in ETSAP)", fac="non_ferrous", split="electricity (Wei 2020); fuel incl. reductant", band="high (>400 C), reductant = process fuel", pe="v3 rule: electricity + heat high (no PyPSA-Eur sector)",
         unsd="non-ferrous metals (ID: not a row -> other)", v3="nonferrous_nickel (ID)", ded="explicit in v3: replace", g=("B", "C", "C", "C"), note="2023 production 3.65 x 2019 (base-year choice dominates)"),
    dict(product="ammonia", route="SMR Haber-Bosch (gas)", sub="chemicals", act="GEM GCT 2026-11 capacity (ID, MY, VN, BN, MM); USGS Nitrogen T12 2019 (v3); ETSAP 2018; Climate TRACE chemicals", atype="national production (v3); plants for location",
         year="2019", etsap="ammonia_gas", fac="chemicals", split="electricity; fuel gas (reformer firing); feedstock gas (NEU)", band="fuel: high (>400 C) reformer; feedstock outside T_v2",
         pe="Ammonia (product on the national bus, 5.166 MWh_NH3/t)", unsd="chemical and petrochemical (+ NEU gas)", v3="ammonia (product); NEU gas minus 10.8 MWh/t", ded="explicit in v3: replace; process fuel in the chemical row was dropped by DFX F2 only where the EU27 ammonia share existed",
         g=("A", "C", "C", "B"), note="MY / BN / MM: chemical row missing -> reformer fuel may sit in other while the product load is explicit (possible double count, INFERENCE)"),
    dict(product="methanol", route="gas-based synthesis", sub="chemicals", act="GEM GCT capacity (MY 4,080, BN 850, ID 660 ktpa); Climate TRACE chemicals; ETSAP region only", atype="capacity x utilisation", year="2026 (status)",
         etsap="methanol_gas", fac="chemicals", split="electricity; fuel; feedstock (NEU)", band="fuel: high (>400 C)", pe="Methanol (product, 5.528 MWh_MeOH/t)", unsd="chemical and petrochemical (+ NEU gas)",
         v3="dispersed (EU27 methanol share of the chemical row) or other", ded="dispersed chemical row if present, else other; feedstock from NEU gas", g=("B", "C", "C", "B"), note="v3 methanol demand comes from EU27 weights, not ASEAN plants"),
    dict(product="olefins (ethylene, propylene)", route="naphtha / ethane steam cracking", sub="chemicals", act="SFI ethylene 2025-12 (23 ASEAN units); GEM GCT olefins; Climate TRACE steam cracking (14); ETSAP 2018",
         atype="capacity x utilisation; Climate TRACE activity only as cross-check", year="2025", etsap="olefins_naphtha_steam_cracking", fac="chemicals", split="electricity; cracker fuel; feedstock (NEU)",
         band="high (>800 C cracking furnace); fuel often by-product gas (INFERENCE)", pe="HVC (+ recycling routes)", unsd="chemical and petrochemical (+ NEU naphtha / LPG / ethane)", v3="dispersed (HVC share) or other; NEU oil x 0.4",
         ded="process energy: dispersed chemical row or other; feedstock: NEU", g=("B", "C", "C", "C"), note="HVC tonnes are not modelled explicitly in v3"),
    dict(product="aromatics", route="naphtha based", sub="chemicals", act="GEM GCT aromatics capacity; ETSAP region only", atype="capacity x utilisation", year="2026 (status)", etsap="aromatics", fac="chemicals",
         split="electricity; fuel; feedstock (NEU)", band="medium B / high", pe="HVC (proxy) or Other chemicals", unsd="chemical and petrochemical", v3="dispersed or other", ded="as olefins", g=("B", "C", "C", "C"),
         note="often refinery-integrated: boundary with refinery own use to be checked"),
    dict(product="chlorine", route="membrane electrolysis", sub="chemicals", act="ETSAP 2018 (ID 1,485 kt, TH 765 kt)", atype="national production", year="2018", etsap="chlorine_membrane_odc", fac="chemicals",
         split="electricity", band="none", pe="Chlorine", unsd="chemical and petrochemical", v3="dispersed (EU27 chlorine share) or other", ded="dispersed chemical row if present, else other", g=("B", "C", "B", "C"),
         note="no facility list downloaded"),
    dict(product="chemical pulp", route="kraft", sub="pulp and paper", act="SFI pulp & paper 2025-07 (capacity for 8 of 77 ID mills); ETSAP 2018 (ID 7.85 Mt); Climate TRACE pulp-and-paper (59)", atype="national production; capacity for location",
         year="2018", etsap="pulp_chemical", fac="pulp_paper", split="electricity; steam / heat (largely black liquor)", band="medium A (steam 150-200 C)", pe="Pulp production", unsd="paper pulp and print",
         v3="dispersed (PH, TH, VN) or other (ID, MY, MM, ...)", ded="dispersed paper row if present, else other", g=("B", "C", "C", "C"), note="black liquor 22 GJ/t output is own fuel (biomass in UNSD industry)"),
    dict(product="paper", route="graphical / packaging / hygiene", sub="pulp and paper", act="ETSAP 2018 (FAO); SFI capacity", atype="national production", year="2018", etsap="paper_packaging|paper_graphical|paper_hygiene|paper_tech_packaging",
         fac="pulp_paper", split="electricity; drying steam", band="low / medium A (drying steam)", pe="Paper production", unsd="paper pulp and print", v3="dispersed or other", ded="dispersed paper row if present, else other",
         g=("B", "C", "C", "C"), note="recycling pulp: ETSAP pulp_recycling"),
    dict(product="food, beverages, tobacco", route="mixed", sub="food", act="Climate TRACE food (1,406 ASEAN assets; activity modelled, cf 0.3956 for 85 % of rows); no ETSAP", atype="none reliable (modelled)", year="2025 (modelled)",
         etsap="none", fac="none", split="electricity; process steam / hot water", band="low (<150 C)", pe="Food, beverages and tobacco", unsd="food and tobacco", v3="dispersed (MM, PH, TH, VN) or other",
         ded="keep national (UNSD / APEC) energy; use assets only for location", g=("D", "E", "C", "C"), note="APEC / national statistics better than asset activity"),
    dict(product="textiles, leather, apparel", route="mixed", sub="textiles", act="Climate TRACE textiles (1,860 ASEAN assets; activity modelled)", atype="none reliable (modelled)", year="2025 (modelled)", etsap="none", fac="none",
         split="electricity; dyeing / finishing steam", band="low / medium A", pe="Textiles and leather", unsd="textile and leather", v3="dispersed or other", ded="keep national energy; assets for location",
         g=("D", "E", "C", "C"), note=""),
    dict(product="refined products", route="refinery", sub="outside industry final energy", act="Climate TRACE refining (31 ASEAN); USGS GIS (v3)", atype="throughput (modelled)", year="2025",
         etsap="none", fac="none", split="refinery own use (UNSD energy industries own use)", band="-", pe="none (not an industry load)", unsd="energy industries own use (not an industry row)", v3="not in industry; GIS used for NEU / process-emission nodes",
         ded="no deduction from other", g=("D", "E", "-", "-"), note="v3 decision kept: refinery energy is outside industry final energy"),
    dict(product="mining and quarrying", route="non-energy mining", sub="mining (residual)", act="Climate TRACE bauxite / copper / iron mines (ore extracted); UNSD mining row (MM, PH, TH, VN)", atype="ore tonnes (modelled)", year="2025",
         etsap="none", fac="none", split="diesel (mechanical), electricity", band="mechanical fuel", pe="Other industrial sectors", unsd="mining and quarrying", v3="inside other (MM, PH, TH, VN)", ded="stays in the residual",
         g=("D", "E", "C", "C"), note="coal / oil and gas extraction own use is energy-sector own use, not this row"),
    dict(product="construction", route="-", sub="construction (residual)", act="UNSD construction row (MM, PH, TH, VN)", atype="national energy", year="2019", etsap="none", fac="none", split="diesel (mechanical), electricity",
         band="mechanical fuel", pe="Other industrial sectors", unsd="construction", v3="inside other", ded="stays in the residual", g=("A", "-", "C", "C"), note="not covered by any facility data"),
]
PE_CARRIERS = ("elec", "coal", "coke", "biomass", "methane", "hydrogen", "heat", "naphtha", "ammonia", "methanol")
PES = {"BF-BOF": "DRI + Electric arc", "DRI-EAF (gas)": "DRI + Electric arc", "scrap EAF / IF": "Electric arc"}   # v3 2050 route: primary steel -> H2-DRI + EAF
# ODA factors that absorb products outside the ETSAP product list (INFERENCE, see report section 4.4): flag the product rows that use them
FLAG = {"non_ferrous": "ODA non-ferrous fuel factor 6.77 likely absorbs ID nickel smelting (no nickel route in ETSAP): do not apply per product; use product literature or national calibration",
        "chemicals": "ODA chemicals factors (electricity 4.90, fuel 2.12, feedstock 3.22) absorb products outside the list: per-product use overstates (e.g. chlorine 9.8 MWh/t); calibrate to national statistics"}
UNSD_KEY = {"iron and steel": None, "non-metallic minerals": "non-metallic minerals", "non-ferrous metals": "non-ferrous metals", "chemical and petrochemical": "chemical and petrochemical",
            "paper pulp and print": "paper pulp and print", "food and tobacco": "food and tobacco", "textile and leather": "textile and leather"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); ap.add_argument("--repo", type=Path, required=True); a = ap.parse_args()
    ev = a.work / "evidence"
    bat = pd.read_csv(ev / "COVERAGE_ETSAP_BAT_SEC.csv")
    S = json.loads((ev / "COVERAGE_SUMMARY.json").read_text(encoding="utf-8"))["etsap"]["oda_inefficiency_detail"]
    fac = {"iron_steel": S["Iron&Steel"]["bat_adjusted"], "non_ferrous": S["Non-Ferrous"]["bat_adjusted"], "non_metallic_minerals": S["Non-metallic Minerals"]["bat_adjusted"],
           "pulp_paper": S["Paper&Pulp"]["bat_adjusted"], "chemicals": S["Chemicals"]["bat_adjusted"]}
    pe = pd.read_csv(a.repo / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)
    today = pd.read_csv(a.repo / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv").set_index("sector")
    disp = pd.read_csv(ev / "V3_DISPERSED_BY_UNSD_ROW.csv")
    rows_disp = disp[disp.twh_2050 > 1e-6].groupby("unsd_row").country.apply(lambda s: ",".join(sorted(set(s)))).to_dict()
    out = []
    for r in ROWS:
        el = fu = fs = ht = None
        if r["etsap"] not in ("none",) and not r["etsap"].startswith("none"):
            parts = [p for p in r["etsap"].replace("|", "+").split("+")]
            first = parts[0]
            b = bat[bat.route.isin(parts if "+" in r["etsap"] else [first])]
            g = lambda item: float(b[b["item"] == item].bat_gj_per_t.sum()) if (b["item"] == item).any() else 0.0
            if r["etsap"].startswith("clinker"):
                c = bat[bat.route == "clinker"]; f = bat[bat.route == "cement_finishing"]
                ck = float(f[f["item"] == "clinker_t_per_t"].bat_gj_per_t.iloc[0])
                el = float(c[c["item"] == "electricity"].bat_gj_per_t.iloc[0]) * ck + float(f[f["item"] == "electricity"].bat_gj_per_t.iloc[0]); fu = float(c[c["item"] == "heat"].bat_gj_per_t.iloc[0]) * ck
            else:
                el = g("electricity"); fu = g("fuel") + g("heat") + g("fuel_gas") + g("fuel_coal"); fs = g("feedstock") + g("feedstock_gas") + g("feedstock_coal") + g("feedstock_coal_anode")
        f_ = fac.get(r["fac"]) if r["fac"] != "none" else None
        i_el = f_.get("Electricity") if f_ else None
        i_fu = (f_.get("Fuel") if f_ else None)
        i_fs = (f_.get("Feedstock") if f_ else None)
        base_el = el * i_el / GJ if (el is not None and i_el) else None
        base_fu = fu * i_fu / GJ if (fu is not None and i_fu) else None
        base_fs = fs * (i_fs or 1.0) / GJ if fs else None
        sec0 = PES.get(r["route"]) or r["pe"].split(" (")[0].split(" or ")[0].strip()   # sector names can contain '+': explicit for steel
        sec0 = sec0 if sec0 in pe.columns else None
        vec = {f"pe2050_{k}_mwh_per_t": (float(pe.at[k, sec0]) if sec0 else None) for k in PE_CARRIERS}
        key = UNSD_KEY.get(r["unsd"].split(" (")[0])
        out.append(dict(product=r["product"], route=r["route"], v4_subsector=r["sub"], activity_source=r["act"], activity_type=r["atype"], activity_base_year=r["year"],
                        base_sec_source=("ETSAP v2.1.0 BAT (" + r["etsap"] + ") x ODA BAT-adjusted inefficiency (" + r["fac"] + ")") if el is not None else ("Wei et al. 2020 (v3)" if "nickel" in r["product"] else "none"),
                        bat_electricity_gj_per_t=el, bat_fuel_or_heat_gj_per_t=fu, bat_feedstock_gj_per_t=fs, oda_ineff_electricity=i_el, oda_ineff_fuel=i_fu, oda_ineff_feedstock=i_fs,
                        base_electricity_mwh_per_t=base_el, base_fuel_mwh_per_t=base_fu, base_feedstock_mwh_per_t=base_fs, carrier_split_base=r["split"], fuel_part_heat_band=r["band"],
                        route_2050=r["pe"], pe2050_sector_used=sec0 or "", **vec,
                        pe2050_total_mwh_per_t=(float(pe[sec0].drop(["process emission", "process emission from feedstock"], errors="ignore").sum()) if sec0 else None),
                        eu27_2019_total_mwh_per_t=(float(today.at[sec0, "today_total_mwh_per_t"]) if sec0 in today.index and pd.notna(today.at[sec0, "today_total_mwh_per_t"]) else None),
                        unsd_row=r["unsd"], v3_subsector=r["v3"], v3_dispersed_row_countries=(rows_disp.get(key, "") if key else ""), deduction_rule=r["ded"],
                        grade_activity=r["g"][0], grade_base_sec=r["g"][1], grade_carrier_split=r["g"][2], grade_2050=r["g"][3],
                        notes="; ".join(x for x in (r["note"], FLAG.get(r["fac"], "") if el is not None else "") if x)))
    T = pd.DataFrame(out)
    T.to_csv(a.work / "V4_PRODUCT_ROUTE_MAP.csv", index=False, float_format="%.6g")
    print(T[["product", "route", "bat_electricity_gj_per_t", "bat_fuel_or_heat_gj_per_t", "bat_feedstock_gj_per_t", "base_electricity_mwh_per_t", "base_fuel_mwh_per_t",
             "pe2050_sector_used", "pe2050_total_mwh_per_t", "eu27_2019_total_mwh_per_t", "v3_dispersed_row_countries"]].round(3).to_string())


if __name__ == "__main__":
    main()
