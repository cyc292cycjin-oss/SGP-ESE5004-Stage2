"""I1-3: HVC 2050 specific energy (decision 208 item 6) and the methanol check - PyPSA-Eur v2025.07.0 chemicals_industry() taken apart.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_hvc.py

Runs in the scratch copy /home/jin/v4i1/chain (s3_0_industry_ratios.load_pe_module() writes ammonia_production.csv next to its sources, so it
must not be imported from the repository). Re-computes every component of the HVC column of the PyPSA-Eur sector-ratio table from JRC-IDEES-2021
EU27 2019 with the script's own load_idees_data(), then checks that the components add up to the registered ratio table
(research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv).

Vectors (MWh per t HVC, energy carriers only; naphtha-type feedstock excluded on all sides):
  (a)  PyPSA-Eur 2050 HVC vector as used by S2 / G0-G4 (elec + heat + methane + hydrogen = 6.103);
  (b)  (a) minus the net natural-gas FEEDSTOCK still inside its methane row: JRC-IDEES basic-chemicals feedstock natural gas minus the feedstock
       part of the subtracted ammonia SMR gas and methanol gas (ammonia feedstock 5.833 MWh/t ETSAP as in G1, 4.92 stoichiometric as sensitivity;
       methanol feedstock = product energy 5.528 MWh/t);
  (c1) 2019 energy-use intensity used by S2 / G0-G4 for the 2019 deduction (3.269): basic-chemicals energy use WITHOUT feedstock minus the
       FULL ammonia SMR gas (10.8, which contains the feedstock that is not in the minuend), chlorine and methanol energy;
  (c2) consistent 2019 energy-use intensity: same minuend, minus only the FUEL part of ammonia SMR (10.8 - feedstock) and of methanol;
  (s3_0) the repository's own consistent pair: 2019 6.667 incl. feedstock NG vs 2050 6.103 incl. feedstock NG (efficiency 0.915).
Country table (ID, MY, TH, SG, PH, VN): 2050 HVC production from the W07 sessions (A6 SUBSECTORS tables) x vector -> 2050 HVC energy and the
T_v2 change against (a) (the 2019 deduction held as in the sessions; the explicit 2050 HVC enters T_v2 directly).
Methanol: s3_0 gives every country with a UNSD chemicals row an EU27-weight methanol share (2.659 %) whose 2050 vector is the methanol
CARRIER (product, 5.528 MWh/t); the 2050 methanol load per country and the NEU gas of the same country are listed.
Writes HVC_VECTOR_CHECK.csv, tables/I1_3_*.csv, evidence/I1_3_hvc.json. Nothing in the repository is written.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i1_common as cm  # noqa: E402

CHAIN_SP = cm.SCRATCH / "chain" / "scripts_project"
sys.path.insert(0, str(CHAIN_SP))           # scratch copy first: its ROOT is the scratch chain
import s3_0_industry_ratios as sr  # noqa: E402

assert str(Path(sr.__file__).resolve()).startswith(str(cm.SCRATCH)), sr.__file__
NH3_FEED = {"etsap_5.833": 5.833, "stoich_4.92": 4.92}     # MWh CH4 feedstock per t NH3 (G1 / m08b AMMONIA_GAS_MWH_PER_T_STOICH)
MEOH_FEED = 5.528                                          # MWh per t MeOH (product energy, PyPSA-Eur MWh_MeOH_per_tMeOH)
HVC_2050_T = {   # 2050 HVC production (t) and the session's 2019 deduction intensity, from the A6 tables of G0-G3 (VN: G2 R4 sensitivity only)
    "ID": dict(t2050=4350380.0, t2019=None, ded19_twh=4.054170, src="G0/ID_SUBSECTORS_V4.csv ethylene (HVC) activity_2050 (incl. LINE, u 0.85)"),
    "MY": dict(t2050=39.678703e6 / 6.102996, t2019=3646229.727, ded19_twh=11.92, src="G1/MY_SUBSECTORS_V4.csv hvc energy_2050 / 6.103 (activity 2050 not printed)"),
    "TH": dict(t2050=10379500.0, t2019=6200540.0, ded19_twh=20.268343, src="G3/TH_SUBSECTORS_V4.csv ethylene activity_2050"),
    "SG": dict(t2050=11050500.0, t2019=7596190.0, ded19_twh=24.830436, src="G3/SG_SUBSECTORS_V4.csv ethylene activity_2050 (PCS duplicate removed)"),
    "PH": dict(t2050=1667940.0, t2019=816000.0, ded19_twh=1.988576, src="G3/PH_SUBSECTORS_V4.csv ethylene activity_2050"),
    "VN": dict(t2050=15.84e6 / 6.102996, t2019=0.0, ded19_twh=0.0, src="G2 R4 sensitivity +15.84 TWh / 6.103 (Long Son, not in the main path)"),
}


def components(ev: cm.Evidence) -> tuple[dict, pd.DataFrame]:
    mod = sr.load_pe_module()
    idees = mod.load_idees_data("Chemicals Industry")
    fec, ued = idees["fec"], idees["ued"]
    P = mod.params; toe = mod.toe_to_MWh
    rows = []

    def put(block, item, ktoe, kind="fec"):
        rows.append(dict(block=block, item=str(item), kind=kind, ktoe_2019=float(ktoe), twh_2019=float(ktoe) * toe / 1e3))

    s_bc = fec[3:9]
    for k, v in s_bc.items():
        put("Basic chemicals (fec[3:9])", k, v)
    s_feed = fec[14:23]
    for k, v in s_feed.items():
        put("Chemicals: Feedstock (fec[14:23])", k, v)
    s_st, u_st = fec[23:34], ued[23:34]
    for k, v in s_st.items():
        put("Chemicals: Steam processing (fec[23:34])", k, v)
    for k, v in u_st.items():
        put("Chemicals: Steam processing (ued[23:34])", k, v, "ued")
    s_fu, u_fu = fec[34:42], ued[34:42]
    for k, v in s_fu.items():
        put("Chemicals: Furnaces (fec[34:42])", k, v)
    for k, v in u_fu.items():
        put("Chemicals: Furnaces (ued[34:42])", k, v, "ued")
    s_co, u_co = fec[42:56], ued[42:56]
    put("Chemicals: Process cooling", s_co.index[0], s_co.iloc[0]); put("Chemicals: Process cooling", u_co.index[0], u_co.iloc[0], "ued")
    put("Chemicals: Generic electric process", fec[56:57].index[0], fec[56:57].iloc[0])
    C = pd.DataFrame(rows)
    cm.write_csv(C.to_dict("records"), cm.TABLES / "I1_3_JRC_IDEES_EU27_2019_BASIC_CHEMICALS.csv")
    # ---- PyPSA-Eur 2050 vector, component by component (MWh per t HVC) ------------------------------------------------------------------
    out_t = P["HVC_production_today"] * 1e6
    amm = pd.read_csv(sr.OUT_DIR / "sources" / "jrc_idees_2021" / "ammonia_production.csv", index_col=0)
    nh3_kt = float(amm.loc[amm.index.intersection(mod.eu27), str(max(2018, mod.year))].sum())
    k = lambda ktoe: float(ktoe) * toe * 1e3 / out_t      # ktoe -> MWh per t HVC
    el_motor = k(s_bc[["Lighting", "Air compressors", "Motor drives", "Fans and pumps"]].sum())
    heat_low = k(s_bc["Low-enthalpy heat"])
    feed_ng = k(s_feed["Natural gas"])
    feed_naphtha = k(s_feed["Naphtha"] + s_feed[["Solids", "Refinery gas", "LPG", "Diesel oil", "Fuel oil", "Other liquids"]].sum())
    eff_ch4 = float(u_st["Natural gas and biogas"] / s_st["Natural gas and biogas"])
    steam_ch4 = k(u_st[s_st.index[0]] / eff_ch4)
    eff_fu = float(u_fu["Chemicals: Furnaces - Electric"] / s_fu["Chemicals: Furnaces - Electric"])
    furn_el = k(u_fu[s_fu.index[0]] / eff_fu)
    eff_co = float(u_co["Chemicals: Process cooling - Electric"] / s_co["Chemicals: Process cooling - Electric"])
    cool_el = k(u_co[s_co.index[0]] / eff_co)
    gen_el = k(fec[56:57].iloc[0])
    nh3_ch4 = nh3_kt * 1e3 * P["MWh_CH4_per_tNH3_SMR"] / out_t; nh3_el = nh3_kt * 1e3 * P["MWh_elec_per_tNH3_SMR"] / out_t
    cl_h2 = P["chlorine_production_today"] * 1e6 * P["MWh_H2_per_tCl"] / out_t; cl_el = P["chlorine_production_today"] * 1e6 * P["MWh_elec_per_tCl"] / out_t
    me_ch4 = P["methanol_production_today"] * 1e6 * P["MWh_CH4_per_tMeOH"] / out_t; me_el = P["methanol_production_today"] * 1e6 * P["MWh_elec_per_tMeOH"] / out_t
    vec = dict(elec=el_motor + furn_el + cool_el + gen_el - nh3_el - cl_el - me_el, heat=heat_low, methane=feed_ng + steam_ch4 - nh3_ch4 - me_ch4, hydrogen=-cl_h2,
               naphtha=feed_naphtha)
    reg = pd.read_csv(cm.REPO / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", index_col=0)["HVC"]
    dev = {c: vec[c] - float(reg[c]) for c in vec}
    ok = max(abs(v) for v in dev.values()) < 1e-9
    ev.add("vector.reproduces_registered_ratio_table", ok, "bool", "EXACT", "B", "registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv column HVC", json.dumps({c: round(v, 12) for c, v in dev.items()}))
    if not ok:
        raise SystemExit(f"STOP: HVC components do not reproduce the registered table {dev}")
    # ---- 2019 intensities -------------------------------------------------------------------------------------------------------------
    total_bc = k(s_bc.iloc[0]); feed_all = k(s_feed.iloc[0])
    proc19 = total_bc - feed_all                                   # basic-chemicals energy use without any feedstock
    cl19 = P["chlorine_production_today"] * 1e6 * (P["MWh_elec_per_tCl"] + P["MWh_H2_per_tCl"]) / out_t
    me19 = P["methanol_production_today"] * 1e6 * (P["MWh_CH4_per_tMeOH"] + P["MWh_elec_per_tMeOH"]) / out_t
    nh3_19 = nh3_kt * 1e3 * (P["MWh_CH4_per_tNH3_SMR"] + P["MWh_elec_per_tNH3_SMR"]) / out_t
    c1 = proc19 - nh3_19 - cl19 - me19                              # S2 / G0-G4 value (3.269)
    s30_today = proc19 + feed_ng - nh3_19 - cl19 - me19             # repository s3_0 'today' (6.667)
    res = dict(nh3_kt=nh3_kt, out_t=out_t, el_motor=el_motor, heat_low=heat_low, feed_ng=feed_ng, feed_naphtha=feed_naphtha, steam_ch4=steam_ch4, eff_ch4=eff_ch4,
               furn_el=furn_el, eff_furnace_el=eff_fu, cool_el=cool_el, gen_el=gen_el, nh3_ch4=nh3_ch4, nh3_el=nh3_el, cl_h2=cl_h2, cl_el=cl_el, me_ch4=me_ch4, me_el=me_el,
               vec=vec, a_total=vec["elec"] + vec["heat"] + vec["methane"] + vec["hydrogen"], proc19=proc19, c1=c1, s30_today=s30_today,
               steam_fec19=k(s_st.iloc[0]), furn_fec19=k(s_fu.iloc[0]), cool_fec19=k(s_co.iloc[0]))
    for nm, f_nh3 in NH3_FEED.items():
        net_feed = feed_ng - nh3_kt * 1e3 * f_nh3 / out_t - P["methanol_production_today"] * 1e6 * MEOH_FEED / out_t
        res[f"net_feed_{nm}"] = net_feed
        res[f"b_{nm}"] = res["a_total"] - net_feed
        res[f"c2_{nm}"] = proc19 - nh3_kt * 1e3 * (P["MWh_CH4_per_tNH3_SMR"] - f_nh3 + P["MWh_elec_per_tNH3_SMR"]) / out_t - cl19 \
            - P["methanol_production_today"] * 1e6 * (P["MWh_CH4_per_tMeOH"] - MEOH_FEED + P["MWh_elec_per_tMeOH"]) / out_t
    for key in ("a_total", "c1", "s30_today", "proc19", "feed_ng", "steam_ch4", "furn_el", "steam_fec19", "furn_fec19", "nh3_ch4", "b_etsap_5.833", "c2_etsap_5.833",
                "net_feed_etsap_5.833", "b_stoich_4.92", "c2_stoich_4.92", "nh3_kt"):
        ev.add(f"eu27.{key}", res[key], "MWh/t HVC" if key != "nh3_kt" else "kt NH3", "EXACT", "B", "JRC-IDEES-2021 EU27 2019 x PyPSA-Eur v2025.07.0 chemicals_industry() (scratch run)",
               "registry_v5/sources/pypsa_eur_v2025.07.0_build_industry_sector_ratios.py lines 316-452")
    return res, C


def country_table(res: dict, ev: cm.Evidence) -> pd.DataFrame:
    vecs = {"a_pypsa_eur_2050": res["a_total"], "b_without_net_feedstock_etsap": res["b_etsap_5.833"], "b_without_net_feedstock_stoich": res["b_stoich_4.92"],
            "c1_2019_energy_use_s2": res["c1"], "c2_2019_energy_use_consistent_etsap": res["c2_etsap_5.833"]}
    rows = []
    for c, d in HVC_2050_T.items():
        base = d["t2050"] * res["a_total"] / 1e6
        for nm, v in vecs.items():
            e = d["t2050"] * v / 1e6
            rows.append(dict(country=c, vector=nm, mwh_per_t=v, hvc_2050_mt=d["t2050"] / 1e6, hvc_energy_2050_twh=e, dT_v2_vs_a_twh=e - base,
                             in_main_path=(c != "VN"), activity_source=d["src"]))
        if d.get("t2019"):
            # consistent 2019 deduction (c2) vs the session's c1 deduction: 2019 energy moved out of the UNSD chemicals row / 'other' (multiplier applies in T_v2)
            rows.append(dict(country=c, vector="2019_deduction_c2_minus_c1", mwh_per_t=res["c2_etsap_5.833"] - res["c1"], hvc_2050_mt=d["t2019"] / 1e6,
                             hvc_energy_2050_twh=None, dT_v2_vs_a_twh=None, in_main_path=(c != "VN"),
                             activity_source=f"2019 HVC {d['t2019'] / 1e6:.3f} Mt: extra 2019 deduction {d['t2019'] * (res['c2_etsap_5.833'] - res['c1']) / 1e6:.2f} TWh (x the ATS industry multiplier in T_v2, through the row it is taken from)"))
    T = pd.DataFrame(rows)
    cm.write_csv(T.to_dict("records"), cm.TABLES / "I1_3_HVC_COUNTRY_VECTORS.csv")
    for r in T[T.vector != "2019_deduction_c2_minus_c1"].itertuples():
        ev.add(f"country.{r.country}.{r.vector}", dict(energy_2050_twh=r.hvc_energy_2050_twh, dT_v2_vs_a=r.dT_v2_vs_a_twh), "TWh (2050)", "INFERENCE", "C",
               "tables/I1_3_HVC_COUNTRY_VECTORS.csv", f"{r.hvc_2050_mt:.3f} Mt HVC x {r.mwh_per_t:.4f} MWh/t; {r.activity_source}")
    return T


def methanol(ev: cm.Evidence) -> pd.DataFrame:
    s = pd.read_csv(cm.DEMAND / "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country")
    mp = pd.read_csv(cm.DEMAND / "INDUSTRY_SUBSECTOR_MAPPING_UNSD_PYPSA_EUR.csv")
    w = float(mp[(mp.unsd_subsector == "chemical and petrochemical") & (mp.pypsa_eur_sector == "Methanol")].weight.iloc[0])
    eff = float(mp[(mp.unsd_subsector == "chemical and petrochemical") & (mp.pypsa_eur_sector == "Methanol")].efficiency_factor.iloc[0])
    cache = pd.DataFrame(json.loads((cm.SRC / "industry_cache.json").read_text())["records"])
    cache["chem"] = pd.to_numeric(cache["chemical and petrochemical"])
    a = pd.read_csv(cm.DEMAND / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False)
    a["v"] = pd.to_numeric(a.value_2050_mwh, errors="coerce").fillna(0.0)
    rows = []
    for c in cm.ASEAN:
        chem19 = float(cache[cache.country == c].chem.sum())
        neu_gas = float(a[(a.country == c) & (a.sector == "NonEnergyUse") & (a.carrier == "gas")].v.sum())
        rows.append(dict(country=c, unsd_chemicals_row_2019_twh_cache=chem19 / 1e6, eu27_methanol_weight=w, methanol_efficiency_factor=eff,
                         pe_methanol_2050_twh=float(s.at[c, "pe_methanol_mwh"]) / 1e6, neu_gas_2050_twh=neu_gas / 1e6,
                         note=("MY has no UNSD chemicals row: no s3_0 methanol load; G1 made Labuan methanol explicit (energy use only)" if c == "MY" else "")))
    M = pd.DataFrame(rows)
    cm.write_csv(M.to_dict("records"), cm.TABLES / "I1_3_METHANOL_LOAD_CHECK.csv")
    ev.add("methanol.asean_2050_twh", float(M.pe_methanol_2050_twh.sum()), "TWh (2050)", "VERIFIED", "A", "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv pe_methanol_mwh",
           "EU27 methanol weight of the UNSD chemicals row x efficiency 0.531 x multiplier; carrier = methanol product")
    for r in M[M.pe_methanol_2050_twh > 0].itertuples():
        ev.add(f"methanol.{r.country}", dict(pe_methanol_2050=r.pe_methanol_2050_twh, neu_gas_2050=r.neu_gas_2050_twh, chem_row_2019=r.unsd_chemicals_row_2019_twh_cache), "TWh",
               "VERIFIED", "A", "summary / ATS table / industry_cache.json", "")
    return M


def main():
    ev = cm.Evidence("I1_3_hvc")
    res, C = components(ev)
    T = country_table(res, ev)
    M = methanol(ev)
    vec_rows = []
    v = res["vec"]
    for car in ("elec", "heat", "methane", "hydrogen", "naphtha"):
        vec_rows.append(dict(item=f"2050 vector {car}", mwh_per_t=v[car], in_T_v2=(car != "naphtha"), source="PyPSA-Eur v2025.07.0 build_industry_sector_ratios.py chemicals_industry() with JRC-IDEES-2021 EU27 2019",
                             meaning={"elec": "motor drives, lighting, air compressors, fans/pumps + furnaces fully electrified (UED / electric efficiency) + process cooling + generic electric, minus EU27 ammonia (0.7), chlorine (3.6) and methanol (0.167) electricity",
                                      "heat": "low-enthalpy heat (unchanged FEC)", "methane": "feedstock natural gas + steam processing UED / natural-gas efficiency (steam crackers, >1000 C), minus EU27 ammonia SMR gas (10.8 MWh/t) and methanol gas (10.25 MWh/t)",
                                      "hydrogen": "minus chlorine by-product hydrogen (MWh_H2_per_tCl = -0.9372): the H2 that chlor-alkali supplied inside basic chemicals is now demanded",
                                      "naphtha": "naphtha + LPG + refinery gas + solids + diesel + fuel oil + other liquids FEEDSTOCK (non-energy, outside T_v2)"}[car]))
    detail = [("component: motor/lighting/compressors/fans electricity", res["el_motor"]), ("component: furnaces electrified", res["furn_el"]),
              ("component: process cooling electrified", res["cool_el"]), ("component: generic electric process", res["gen_el"]),
              ("component: feedstock natural gas (in methane)", res["feed_ng"]), ("component: steam processing as methane", res["steam_ch4"]),
              ("component: minus EU27 ammonia SMR gas", -res["nh3_ch4"]), ("component: minus EU27 methanol gas", -res["me_ch4"]),
              ("component: minus ammonia electricity", -res["nh3_el"]), ("component: minus chlorine electricity", -res["cl_el"]), ("component: minus methanol electricity", -res["me_el"]),
              ("component: chlorine hydrogen (sign flipped)", -res["cl_h2"]), ("2019 steam processing FEC (all fuels)", res["steam_fec19"]), ("2019 furnaces FEC (all fuels)", res["furn_fec19"]),
              ("2019 process cooling FEC", res["cool_fec19"]),
              ("(a) 2050 vector total, energy carriers", res["a_total"]), ("net feedstock NG inside (a) (ammonia feedstock 5.833 ETSAP)", res["net_feed_etsap_5.833"]),
              ("net feedstock NG inside (a) (ammonia feedstock 4.92 stoichiometric)", res["net_feed_stoich_4.92"]),
              ("(b) 2050 vector without net feedstock (ETSAP)", res["b_etsap_5.833"]), ("(b) 2050 vector without net feedstock (stoichiometric)", res["b_stoich_4.92"]),
              ("2019 basic-chemicals energy use without feedstock", res["proc19"]), ("(c1) 2019 energy-use intensity, S2 / G0-G4 (full SMR gas subtracted)", res["c1"]),
              ("(c2) 2019 energy-use intensity, consistent (only SMR fuel part subtracted, ETSAP)", res["c2_etsap_5.833"]),
              ("(c2) 2019 energy-use intensity, consistent (stoichiometric)", res["c2_stoich_4.92"]),
              ("s3_0 today (incl. feedstock NG), repository", res["s30_today"]), ("ratio (a) / (c1)", res["a_total"] / res["c1"]),
              ("ratio (b ETSAP) / (c2 ETSAP)", res["b_etsap_5.833"] / res["c2_etsap_5.833"]), ("ratio (a) / s3_0 today", res["a_total"] / res["s30_today"]),
              ("EU27 ammonia production 2019 (kt NH3)", res["nh3_kt"])]
    for nm, val in detail:
        vec_rows.append(dict(item=nm, mwh_per_t=val, in_T_v2="", source="scratch re-run of chemicals_industry() (EXACT, B)", meaning=""))
    cm.write_csv(vec_rows, cm.I1 / "HVC_VECTOR_CHECK.csv")
    p = ev.write()
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90); pd.set_option("display.max_rows", 200)
    print(pd.DataFrame(vec_rows)[["item", "mwh_per_t"]].round(4).to_string())
    print(T.round(3).to_string())
    print(M.round(3).to_string())
    print(C[C.twh_2019.abs() > 0.5].round(2).to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
