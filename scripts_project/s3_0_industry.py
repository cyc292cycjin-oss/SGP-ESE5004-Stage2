"""S3-0.1 (decision 61): ASEAN industrial final energy 2050 with the reproduced PyPSA-Eur sector ratios (JRC-IDEES-2021).

Per country and allocation variant (R3 tables):
  * UNSD 2019 sub-sector split (research-layer industry table, shares only) of the accepted D1 industry final energy.
  * Steel (physical): worldsteel 2019 crude steel x industry multiplier; 2050 = St_primary_fraction (0.3) x DRI_fraction (1.0)
    x "DRI + Electric arc" + (1 - 0.3) x "Electric arc" ratios (MWh/t) -> elec, methane, hydrogen, heat.
  * Cement (physical): clinker = EDGAR 2.A.1 / 0.52 (IPCC); cement = clinker / 0.656 (technology-data cement finishing clinker
    input); x industry multiplier x "Cement" ratio -> elec, methane, biomass, heat (PyPSA-Eur: kiln fuel to methane except biomass).
  * Every other UNSD sub-sector (energy fallback): 2019 energy x industry multiplier x efficiency factor (future / today EU27
    specific energy of the mapped PyPSA-Eur sectors) re-allocated to carriers by the future ratio carrier shares. The mapping
    UNSD sub-sector -> PyPSA-Eur sectors (weights = EU27 2019 final energy of the mapped sectors, grade C) is written to
    INDUSTRY_SUBSECTOR_MAPPING_UNSD_PYPSA_EUR.csv. Naphtha (feedstock) rows are excluded (non-energy use is handled by R2).
  * Chemicals: the UNSD chemical/petrochemical energy is split into basic chemicals (HVC, ammonia, chlorine, methanol) and other
    chemicals/pharma by EU27 2019 final-energy weights; inside basic chemicals the EU27 2019 energy shares of ammonia (SMR route),
    chlorine and methanol (config constants x productions, script lines 431-448) give the ammonia / chlorine / methanol activity
    equivalents, which are converted with the 2050 ratios (ammonia 5.166 MWh_NH3/t, methanol 5.528 MWh_MeOH/t as carriers).
  * Low-temperature heat = the ratio "heat" rows (industrial low-temperature heat bus).
  * Biomass above the national potential -> methane (decision 36); coal retention listed.
The former technology-data based steel/cement ratios (S2B) are written as the sensitivity file *_TD_SENSITIVITY.csv.

    python scripts_project/s3_0_industry.py
"""
from __future__ import annotations

import json

import pandas as pd

from d1_common import ASEAN, BIOMASS_DIR, DEMAND_DIR, REG_DIR, ROOT, SRC_DIR, Registry, read_csv, sha256, src_sha, write_csv, write_json

SCRIPT = "scripts_project/s3_0_industry.py"
CACHE = ROOT / "research_inputs/assembly_v1/sources/industry_cache.json"
WORLDSTEEL = "WORLDSTEEL_2019_ASEAN.csv"
EDGAR = "EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv"
TD = ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv"
RATIOS = REG_DIR / "INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv"
TODAY = REG_DIR / "INDUSTRY_SECTOR_RATIOS_TODAY_EU27_2019.csv"
ALLOCATIONS = {"aeo8_ats_relative": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "gdp": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_GDP_SENSITIVITY.csv",
               "population": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_POP_SENSITIVITY.csv",
               "aeo8_ats_relative_level": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_LEVEL_SENSITIVITY.csv"}   # S3B R1: level growth method (sensitivity)
CARRIERS = ["coal", "oil", "gas", "biomass", "electricity"]
FUELS = ["coal", "oil", "gas", "biomass"]
OUT_CARRIERS = ["coal", "oil", "gas", "biomass", "electricity", "hydrogen", "heat", "ammonia", "methanol"]
RATIO_TO_OUT = {"elec": "electricity", "coal": "coal", "coke": "coal", "biomass": "biomass", "methane": "gas", "hydrogen": "hydrogen", "heat": "heat",
                "ammonia": "ammonia", "methanol": "methanol"}   # naphtha excluded (feedstock, R2)
EF_CLINKER = 0.52; H2_DRI_TD = 2.1; EAF_EL_TD = 0.6395; BOF_COAL_TD = 5.34
PE = dict(St_primary_fraction=0.3, DRI_fraction=1.0, MWh_CH4_per_tNH3_SMR=10.8, MWh_elec_per_tNH3_SMR=0.7, chlorine_production_today=9.58, MWh_elec_per_tCl=3.6,
          MWh_H2_per_tCl=-0.9372, methanol_production_today=1.5, MWh_elec_per_tMeOH=0.167, MWh_CH4_per_tMeOH=10.25, HVC_production_today=52.0)
OIS_TODAY = REG_DIR / "INDUSTRY_OIS_TODAY_CARRIERS_EU27_2019.csv"   # S3B R2 (decision 67): scripts_project/s3b_r2_ois_today.py
OTHER_BUCKET_MODES = ["pypsa_eur_2050", "idees_today"]
OTHER_BUCKET_SUFFIX = {"pypsa_eur_2050": "", "idees_today": "_OTHER_IDEES_TODAY"}
RATIO_EVIDENCE = REG_DIR / "INDUSTRY_SECTOR_RATIOS_EVIDENCE.json"   # EU27 ammonia 2019 (USGS T12 via the reproduced PyPSA-Eur build_ammonia_production)
# UNSD sub-sector -> PyPSA-Eur sectors (weights = EU27 2019 final energy of the mapped sectors unless stated). Grade C mapping.
MAPPING = {
    "chemical and petrochemical": ["HVC", "Ammonia", "Chlorine", "Methanol", "Other chemicals", "Pharmaceutical products etc."],
    "non-metallic minerals": ["Ceramics & other NMM", "Glass production"],   # cement handled physically
    "non-ferrous metals": ["Alumina production", "Aluminium - primary production", "Aluminium - secondary production", "Other non-ferrous metals"],
    "paper pulp and print": ["Pulp production", "Paper production", "Printing and media reproduction"],
    "food and tobacco": ["Food, beverages and tobacco"], "textile and leather": ["Textiles and leather"], "machinery": ["Machinery equipment"],
    "transport equipment": ["Transport equipment"], "wood and wood products": ["Wood and wood products"],
    "other": ["Other industrial sectors"], "construction": ["Other industrial sectors"], "mining and quarrying": ["Other industrial sectors"],
}
OTHER_BUCKET = [u for u, secs in MAPPING.items() if secs == ["Other industrial sectors"]]   # S3B R2: the UNSD sub-sectors in the 'other' bucket


def td_value(td, tech, param):
    r = td[(td.technology == tech) & (td.parameter == param)]
    return float(r.value.iloc[0])


def main():
    cache = json.loads(CACHE.read_text()); cache_sha = sha256(CACHE)
    cdf = pd.DataFrame(cache["records"]); subs = [c for c in cdf.columns if c not in ("country", "carrier")]
    for s_ in subs:
        cdf[s_] = cdf[s_].astype(float)
    ws = {r["iso2"]: r for r in read_csv(SRC_DIR / WORLDSTEEL)}; ws_sha = src_sha(WORLDSTEEL)
    ed = pd.read_csv(SRC_DIR / EDGAR); ed_sha = src_sha(EDGAR)
    clinker_kt = {c: float(ed[(ed.iso == c) & (ed.ipcc_code_2006_for_standard_report == "2.A.1")].kt_CO2_2019.fillna(0.0).sum()) for c in ASEAN}
    td = pd.read_csv(TD); td_sha = sha256(TD)
    cf_ck = td_value(td, "cement finishing", "clinker-input"); ck_heat = td_value(td, "cement dry clinker", "heat-input"); ck_gas = td_value(td, "cement dry clinker", "gas-input")
    ck_el = td_value(td, "cement dry clinker", "electricity-input"); cf_el = td_value(td, "cement finishing", "electricity-input")
    ratios = pd.read_csv(RATIOS, index_col=0); r_sha = sha256(RATIOS)
    today = pd.read_csv(TODAY).set_index("sector"); t_sha = sha256(TODAY)
    ois = pd.read_csv(OIS_TODAY).set_index("carrier"); ois_sha = sha256(OIS_TODAY)
    ois_today = {oc: float(ois.at[oc, "share"]) if oc in ois.index else 0.0 for oc in OUT_CARRIERS}
    assert abs(sum(ois_today.values()) - 1.0) < 1e-9
    toe = 11.63
    PE["EU27_ammonia_kt"] = float(json.loads(RATIO_EVIDENCE.read_text())["eu27_ammonia_kt_2019"])
    # EU27 2019 energy weights of the chemicals split (script lines 431-448): basic chemicals energy use (feedstock excluded) = HVC + NH3 + Cl + MeOH
    basic_fec_mwh = (float(today.at["HVC", "fec_2019_ktoe"]) - float(today.at["HVC", "feedstock_2019_ktoe"])) * toe * 1e3
    nh3_mwh = PE["EU27_ammonia_kt"] * 1e3 * (PE["MWh_CH4_per_tNH3_SMR"] + PE["MWh_elec_per_tNH3_SMR"])
    cl_mwh = PE["chlorine_production_today"] * 1e6 * (PE["MWh_elec_per_tCl"] + PE["MWh_H2_per_tCl"])
    meoh_mwh = PE["methanol_production_today"] * 1e6 * (PE["MWh_CH4_per_tMeOH"] + PE["MWh_elec_per_tMeOH"])
    hvc_mwh = basic_fec_mwh - nh3_mwh - cl_mwh - meoh_mwh
    eu_fec = {s: float(today.at[s, "fec_2019_ktoe"]) * toe * 1e3 if s in today.index and pd.notna(today.at[s, "fec_2019_ktoe"]) else None for s in ratios.columns}
    eu_fec.update({"HVC": hvc_mwh, "Ammonia": nh3_mwh, "Chlorine": cl_mwh, "Methanol": meoh_mwh})
    # today specific energy per PyPSA sector (MWh/t, energy use only) and the future vector (carriers, naphtha excluded)
    today_spec = {s: (float(today.at[s, "today_total_mwh_per_t"]) if s in today.index and pd.notna(today.at[s, "today_total_mwh_per_t"]) else None) for s in ratios.columns}
    # HVC 2019 specific energy comes from the ratio script on the PyPSA-Eur convention (energy use + feedstock natural gas - NH3/Cl/MeOH energy per t HVC;
    # the 2050 ratio counts the feedstock natural gas as methane, script lines 330-345); the chemicals split weights above stay energy-only (UNSD basis).
    today_spec.update({"Ammonia": PE["MWh_CH4_per_tNH3_SMR"] + PE["MWh_elec_per_tNH3_SMR"],
                       "Chlorine": PE["MWh_elec_per_tCl"] + PE["MWh_H2_per_tCl"], "Methanol": PE["MWh_CH4_per_tMeOH"] + PE["MWh_elec_per_tMeOH"]})
    fut = {s: {oc: 0.0 for oc in OUT_CARRIERS} for s in ratios.columns}
    for s in ratios.columns:
        for k, oc in RATIO_TO_OUT.items():
            fut[s][oc] += float(ratios.at[k, s])
    fut_total = {s: sum(v.values()) for s, v in fut.items()}
    mapping_rows = []
    for u, secs in MAPPING.items():
        wsum = sum(eu_fec[s] or 0.0 for s in secs)
        for s in secs:
            w = (eu_fec[s] or 0.0) / wsum if wsum else 1.0 / len(secs)
            mapping_rows.append(dict(unsd_subsector=u, pypsa_eur_sector=s, weight=w, weight_basis="EU27 2019 final energy of the mapped sectors (JRC-IDEES-2021; chemicals split per PyPSA-Eur script lines 431-448)"
                                     + ("; HVC 2019 specific energy incl. feedstock natural gas as methane (PyPSA-Eur convention, lines 330-345), naphtha excluded on both sides" if s == "HVC" else ""),
                                     today_mwh_per_t=today_spec[s], future_mwh_per_t=fut_total[s], efficiency_factor=(fut_total[s] / today_spec[s]) if today_spec[s] else None,
                                     future_shares={k: (v / fut_total[s] if fut_total[s] else 0.0) for k, v in fut[s].items()}))
    mp = {(r["unsd_subsector"], r["pypsa_eur_sector"]): r for r in mapping_rows}
    write_csv([dict(r, future_shares=json.dumps({k: round(v, 6) for k, v in r["future_shares"].items()})) for r in mapping_rows], DEMAND_DIR / "INDUSTRY_SUBSECTOR_MAPPING_UNSD_PYPSA_EUR.csv",
              ["unsd_subsector", "pypsa_eur_sector", "weight", "weight_basis", "today_mwh_per_t", "future_mwh_per_t", "efficiency_factor", "future_shares"])
    bio = pd.read_csv(BIOMASS_DIR / "BIOMASS_POTENTIAL_2050.csv")
    solid_pot = bio[bio.feedstock_group != "biogas"].assign(p=pd.to_numeric(bio.potential_main_mwh, errors="coerce").fillna(0.0)).groupby("country").p.sum().to_dict()
    s2b_path = DEMAND_DIR / "INDUSTRY_2050_SUMMARY_aeo8_ats_relative_S2B_FROZEN.csv"   # S2B result frozen from commit 8d61bd37 (s2b_industry.py) -> comparison column
    s2b_summary = pd.read_csv(s2b_path).set_index("country").to_dict("index"); s2b_sha = sha256(s2b_path)
    outputs, gaps, other_rows, outputs_today = {}, [], [], {}
    reg = Registry(SCRIPT)
    for mode, fname in ALLOCATIONS.items():
        dem = pd.read_csv(DEMAND_DIR / fname, keep_default_na=False)
        rows, summaries, tds = [], {ob: [] for ob in OTHER_BUCKET_MODES}, {ob: [] for ob in OTHER_BUCKET_MODES}
        summary, td_rows = summaries["pypsa_eur_2050"], tds["pypsa_eur_2050"]
        for c in ASEAN:
            d = dem[(dem.country == c) & (dem.sector == "Industry")]
            if not len(d):
                continue
            mult = float(d.multiplier_total.iloc[0])
            e19 = {car: float(d[d.carrier == car].base_2019_mwh.sum()) for car in CARRIERS}
            ag_bio_50 = float(pd.to_numeric(dem[(dem.country == c) & (dem.sector == "AgricultureOthers") & (dem.carrier == "biomass")].value_2050_mwh, errors="coerce").fillna(0).sum())
            cc = cdf[cdf.country == c].set_index("carrier")
            sub19 = {s_: {} for s_ in subs}; present = []
            for car in CARRIERS:
                col = cc.loc[car] if car in cc.index else None
                tot = float(col[subs].sum()) if col is not None else 0.0
                for s_ in subs:
                    sub19[s_][car] = e19[car] * ((float(col[s_]) / tot) if (col is not None and tot > 0) else (1.0 if s_ == "other" else 0.0))
            for s_ in subs:
                if sum(sub19[s_].values()) > 0 and s_ != "other":
                    present.append(s_)

            def take(bucket, want, label):
                got = {}
                for car in CARRIERS:
                    t = min(want.get(car, 0.0), bucket.get(car, 0.0)); bucket[car] = bucket.get(car, 0.0) - t; got[car] = t
                    if want.get(car, 0.0) - t > 1e-6:
                        gaps.append(dict(mode=mode, country=c, item=label, carrier=car, mwh=want[car] - t))
                return got

            def spread(amount_fuel, amount_el, bucket):
                ft = sum(bucket.get(f, 0.0) for f in FUELS)
                out = {f: (amount_fuel * bucket.get(f, 0.0) / ft if ft > 0 else 0.0) for f in FUELS}
                if ft <= 0 and amount_fuel > 0:
                    out["coal"] = amount_fuel
                out["electricity"] = amount_el
                return out

            # ---- steel (physical) --------------------------------------------------------------------------
            w = ws.get(c, {})
            crude = float(w.get("crude_steel_2019_kt") or 0.0) * 1e3; bof = float(w.get("bof_oxygen_kt") or 0.0) * 1e3
            eaf = (float(w.get("eaf_electric_kt") or 0.0) + float(w.get("other_kt") or 0.0)) * 1e3
            # 2019 steel energy to remove: PyPSA-Eur today ratios (Integrated steelworks for BOF, Electric arc for EAF; MWh/t, IDEES EU27 2019)
            want_steel = {car: 0.0 for car in CARRIERS}
            steel19_spec = dict(coal=(float(ratios.at["coal", "Integrated steelworks"]) + float(ratios.at["coke", "Integrated steelworks"])) * bof,
                                gas=float(ratios.at["methane", "Integrated steelworks"]) * bof + float(ratios.at["methane", "Electric arc"]) * eaf,
                                electricity=float(ratios.at["elec", "Integrated steelworks"]) * bof + float(ratios.at["elec", "Electric arc"]) * eaf, oil=0.0, biomass=0.0)
            for car in CARRIERS:
                want_steel[car] = steel19_spec[car]
            if "iron and steel" in present:
                row = dict(sub19["iron and steel"])
                if sum(want_steel.values()) > sum(row.values()) * 1.000001:
                    excess = {car: max(0.0, want_steel[car] - row[car]) for car in CARRIERS}
                    got = take(sub19["other"], excess, "steel: activity-based 2019 energy above the UNSD row, excess not found in other")
                    steel19 = {car: row[car] + got[car] for car in CARRIERS}
                    gaps.append(dict(mode=mode, country=c, item="UNSD iron-and-steel row below worldsteel activity x PyPSA-Eur 2019 ratios; excess removed from other (grade C)", carrier="all", mwh=sum(excess.values())))
                else:
                    steel19 = row
                sub19["iron and steel"] = {car: 0.0 for car in CARRIERS}
                steel_src = "UNSD 2019 sub-sector row replaced by the 2050 routes"
            else:
                steel19 = take(sub19["other"], want_steel, "steel 2019 (PyPSA-Eur today ratios x worldsteel) exceeds the other bucket")
                steel_src = "no UNSD iron-and-steel row: 2019 energy = worldsteel activity x PyPSA-Eur Integrated steelworks / Electric arc ratios, taken from other (grade C)"
                if crude > 0:
                    gaps.append(dict(mode=mode, country=c, item="no UNSD iron-and-steel row; 2019 steel energy derived (grade C)", carrier="all", mwh=sum(want_steel.values())))
            prod50 = crude * mult; primary = PE["St_primary_fraction"] * prod50; dri = PE["DRI_fraction"] * primary; secondary = prod50 - primary
            steel50 = {oc: fut["DRI + Electric arc"][oc] * dri + fut["Electric arc"][oc] * secondary for oc in OUT_CARRIERS}
            # ---- cement (physical) --------------------------------------------------------------------------
            clk19 = clinker_kt[c] * 1e3 / EF_CLINKER; cem_t19 = clk19 / cf_ck
            cem19_spec = {car: 0.0 for car in CARRIERS}
            fuel19 = (float(ratios.at["methane", "Cement"]) + float(ratios.at["biomass", "Cement"])) * cem_t19   # kiln fuel (today: same total, IDEES fuels)
            el19 = float(ratios.at["elec", "Cement"]) * cem_t19
            if "non-metallic minerals" in present:
                nmm19 = dict(sub19["non-metallic minerals"]); nmm_src = "UNSD NMM row: cement part = EDGAR clinker x PyPSA-Eur Cement ratio, remainder = ceramics/glass"
                want = spread(fuel19, el19, nmm19); got = take(nmm19, want, "cement: activity-based 2019 energy above the UNSD NMM row (logged, then taken from other)")
                excess = {car: max(0.0, want[car] - got[car]) for car in CARRIERS}
                got2 = take(sub19["other"], spread(sum(excess[f] for f in FUELS), excess["electricity"], sub19["other"]), "cement: excess over the NMM row not found in other") if sum(excess.values()) > 1e-6 else {car: 0.0 for car in CARRIERS}
                if sum(excess.values()) > 1e-6:
                    gaps.append(dict(mode=mode, country=c, item="UNSD NMM row below EDGAR clinker x PyPSA-Eur Cement ratio; excess removed from other (grade C)", carrier="all", mwh=sum(excess.values())))
                cem19 = {car: got[car] + got2[car] for car in CARRIERS}; nmm_rest19 = dict(nmm19); sub19["non-metallic minerals"] = {car: 0.0 for car in CARRIERS}
            else:
                nmm_src = "no UNSD NMM row: cement 2019 energy = EDGAR clinker x PyPSA-Eur Cement ratio, taken from other (grade C)"
                cem19 = take(sub19["other"], spread(fuel19, el19, sub19["other"]), "cement 2019 derived energy exceeds the other bucket"); nmm_rest19 = {car: 0.0 for car in CARRIERS}
                if clk19 > 0:
                    gaps.append(dict(mode=mode, country=c, item="no UNSD NMM row; 2019 cement energy derived (grade C)", carrier="all", mwh=fuel19 + el19))
            cem_t50 = cem_t19 * mult
            cement50 = {oc: fut["Cement"][oc] * cem_t50 for oc in OUT_CARRIERS}
            # ---- other sub-sectors: energy fallback with mapped ratios -----------------------------------------
            rest50 = {oc: 0.0 for oc in OUT_CARRIERS}; rest19 = {car: 0.0 for car in CARRIERS}; detail = []
            for s_ in subs:
                src_bucket = sub19[s_] if s_ != "non-metallic minerals" else nmm_rest19
                e_sub = sum(src_bucket.values())
                if e_sub <= 0:
                    continue
                for car in CARRIERS:
                    rest19[car] += src_bucket[car]
                secs = MAPPING.get(s_, ["Other industrial sectors"])
                for p in secs:
                    m_ = mp[(s_, p)]; share = m_["weight"]; eff = m_["efficiency_factor"] or 1.0
                    e_p = e_sub * share * mult * eff
                    for oc in OUT_CARRIERS:
                        rest50[oc] += e_p * m_["future_shares"][oc]
                    detail.append(dict(subsector=s_, pypsa=p, e2019=e_sub * share, e2050=e_p, eff=eff))
            # ---- S3B R2 (decision 67): other-bucket variant idees_today -------------------------------------------------
            # UNSD sub-sectors mapped to "Other industrial sectors" (other, construction, mining and quarrying) keep the JRC-IDEES-2021 EU27 2019 carrier
            # structure of that sector (no process switch, efficiency factor 1); every other sub-sector, steel and cement unchanged.
            rest50_today = {oc: 0.0 for oc in OUT_CARRIERS}; other19 = {car: 0.0 for car in CARRIERS}
            other50 = {ob: {oc: 0.0 for oc in OUT_CARRIERS} for ob in OTHER_BUCKET_MODES}
            for s_ in subs:
                src_bucket = sub19[s_] if s_ != "non-metallic minerals" else nmm_rest19
                e_sub = sum(src_bucket.values())
                if e_sub <= 0:
                    continue
                for p in MAPPING.get(s_, ["Other industrial sectors"]):
                    m_ = mp[(s_, p)]; share = m_["weight"]; eff = m_["efficiency_factor"] or 1.0
                    e_main = e_sub * share * mult * eff
                    if s_ in OTHER_BUCKET:
                        for car in CARRIERS:
                            other19[car] += src_bucket[car] * share
                        for oc in OUT_CARRIERS:
                            other50["pypsa_eur_2050"][oc] += e_main * m_["future_shares"][oc]
                            other50["idees_today"][oc] += e_sub * share * mult * ois_today[oc]
                            rest50_today[oc] += e_sub * share * mult * ois_today[oc]
                    else:
                        for oc in OUT_CARRIERS:
                            rest50_today[oc] += e_main * m_["future_shares"][oc]
            e19_tot = sum(e19.values())
            other_rows.append(dict(mode=mode, country=c, industry_2019_mwh=e19_tot, other_2019_mwh=sum(other19.values()),
                                   other_share_of_industry_2019=(sum(other19.values()) / e19_tot if e19_tot else 0.0), industry_multiplier=mult,
                                   **{f"other_2019_{car}_mwh": other19[car] for car in CARRIERS},
                                   **{f"other_2050_{ob}_{oc}_mwh": other50[ob][oc] for ob in OTHER_BUCKET_MODES for oc in OUT_CARRIERS}))
            # ---- technology-data sensitivity (S2B method) for steel/cement, other sub-sectors as above ---------------
            td_steel = {oc: 0.0 for oc in OUT_CARRIERS}; td_steel["hydrogen"] = 1.7 * dri; td_steel["electricity"] = 0.322 * dri + EAF_EL_TD * (dri + secondary)
            td_cement = {oc: 0.0 for oc in OUT_CARRIERS}; td_cement["gas"] = (ck_heat + ck_gas) * clk19 * mult; td_cement["electricity"] = (ck_el + cf_el / cf_ck) * clk19 * mult
            s2b = s2b_summary.get(c, {})
            for ob, rest in (("pypsa_eur_2050", rest50), ("idees_today", rest50_today)):
                main_ob = ob == "pypsa_eur_2050"
                pe = {oc: rest[oc] + steel50[oc] + cement50[oc] for oc in OUT_CARRIERS}
                if pe["hydrogen"] < 0:   # chlorine H2 by-product (ratio -0.9372 MWh_H2/t Cl) exceeds the H2 uses: no net industrial H2 demand, by-product not credited (logged)
                    if main_ob:
                        gaps.append(dict(mode=mode, country=c, item="net industrial hydrogen negative (chlorine by-product > H2 uses) -> 0, by-product not credited", carrier="hydrogen", mwh=pe["hydrogen"]))
                    pe["hydrogen"] = 0.0
                bas = {car: e19[car] * mult for car in CARRIERS}
                pot = float(solid_pot.get(c, 0.0)); overflow = max(0.0, pe["biomass"] + ag_bio_50 - pot)
                ov_ind = min(overflow, pe["biomass"]); ov_ag = min(overflow - ov_ind, ag_bio_50)
                pe_final = dict(pe); pe_final["biomass"] -= ov_ind; pe_final["gas"] += ov_ind
                td = {oc: rest[oc] + td_steel[oc] + td_cement[oc] for oc in OUT_CARRIERS}
                if main_ob:
                    for s_, dd19, dd50, src in [("iron and steel", steel19, steel50, steel_src), ("cement", cem19, cement50, nmm_src)]:
                        for oc in OUT_CARRIERS:
                            rows.append(dict(country=c, subsector=s_, carrier=oc, mwh_2019=dd19.get(oc, 0.0), mwh_2050=dd50.get(oc, 0.0), method=src, ratio_source="PyPSA-Eur v2025.07.0 x JRC-IDEES-2021 EU27", tier="B"))
                    for dt in detail:
                        rows.append(dict(country=c, subsector=dt["subsector"], carrier="all (see mapping shares)", mwh_2019=dt["e2019"], mwh_2050=dt["e2050"], method=f"energy fallback x efficiency factor {dt['eff']:.3f} via {dt['pypsa']}", ratio_source="PyPSA-Eur x JRC-IDEES-2021", tier="C"))
                summaries[ob].append(dict(country=c, industry_multiplier=mult, crude_steel_2019_t=crude, crude_steel_2050_t=prod50, primary_dri_2050_t=dri, secondary_eaf_2050_t=secondary,
                                          clinker_2019_t=clk19, cement_2019_t=cem_t19, cement_2050_t=cem_t50, unsd_subsector_rows_present=";".join(present),
                                          **{f"bas_{car}_mwh": bas[car] for car in CARRIERS}, bas_hydrogen_mwh=0.0, bas_heat_mwh=0.0, bas_ammonia_mwh=0.0, bas_methanol_mwh=0.0,
                                          **{f"pe_{oc}_mwh": pe_final[oc] for oc in OUT_CARRIERS}, pe_biomass_before_overflow_mwh=pe["biomass"],
                                          biomass_overflow_industry_to_gas_mwh=ov_ind, biomass_overflow_agriculture_to_gas_mwh=ov_ag, solid_biomass_potential_main_mwh=pot, agriculture_biomass_2050_mwh=ag_bio_50,
                                          coal_retained_2050_mwh=pe_final["coal"], coal_retained_in=(("mapped PyPSA-Eur ratios (coal/coke rows: none in 2050 except Integrated steelworks, not used)" if main_ob else
                                                                                                       "other bucket with the JRC-IDEES-2021 EU27 2019 carrier structure (solids, derived gases)") if pe_final["coal"] > 0 else ""),
                                          **{f"s2b_td_{oc}_mwh": float(s2b.get(f"pe_{oc}_mwh", 0.0)) for oc in ["coal", "oil", "gas", "biomass", "electricity", "hydrogen", "heat"]},
                                          **{f"td_{oc}_mwh": td[oc] for oc in OUT_CARRIERS}, other_bucket=ob))
                tds[ob].append(dict(country=c, **{f"pe_{oc}_mwh": td[oc] for oc in OUT_CARRIERS}, pe_biomass_before_overflow_mwh=td["biomass"], biomass_overflow_industry_to_gas_mwh=0.0, biomass_overflow_agriculture_to_gas_mwh=0.0))
        outputs[mode] = summary
        write_csv(rows, DEMAND_DIR / f"INDUSTRY_2050_PYPSA_EUR_{mode}.csv", list(rows[0].keys()))
        write_csv(summary, DEMAND_DIR / f"INDUSTRY_2050_SUMMARY_{mode}.csv", list(summary[0].keys()))
        write_csv(td_rows, DEMAND_DIR / f"INDUSTRY_2050_SUMMARY_{mode}_TD_SENSITIVITY.csv", list(td_rows[0].keys()))
        sfx = OTHER_BUCKET_SUFFIX["idees_today"]; outputs_today[mode] = summaries["idees_today"]   # S3B R2 sensitivity tables (research.s3.industry.other_bucket = idees_today)
        write_csv(summaries["idees_today"], DEMAND_DIR / f"INDUSTRY_2050_SUMMARY_{mode}{sfx}.csv", list(summaries["idees_today"][0].keys()))
        write_csv(tds["idees_today"], DEMAND_DIR / f"INDUSTRY_2050_SUMMARY_{mode}_TD_SENSITIVITY{sfx}.csv", list(tds["idees_today"][0].keys()))
    write_csv(gaps, DEMAND_DIR / "INDUSTRY_2050_GAPS.csv", ["mode", "country", "item", "carrier", "mwh"])
    write_csv(other_rows, DEMAND_DIR / "INDUSTRY_2050_OTHER_BUCKET.csv", list(other_rows[0].keys()))
    ob_cmp = []
    for r_m, r_t in zip(outputs["aeo8_ats_relative"], outputs_today["aeo8_ats_relative"]):
        assert r_m["country"] == r_t["country"]
        for oc in OUT_CARRIERS:
            ob_cmp.append(dict(country=r_m["country"], carrier=oc, pypsa_eur_2050_mwh=r_m[f"pe_{oc}_mwh"], idees_today_mwh=r_t[f"pe_{oc}_mwh"], idees_today_minus_main_mwh=r_t[f"pe_{oc}_mwh"] - r_m[f"pe_{oc}_mwh"]))
    write_csv(ob_cmp, DEMAND_DIR / "INDUSTRY_2050_OTHER_BUCKET_COMPARISON.csv", list(ob_cmp[0].keys()))
    main = {r["country"]: r for r in outputs["aeo8_ats_relative"]}
    comp = []
    for c, m in main.items():
        for oc in ["coal", "oil", "gas", "biomass", "electricity", "hydrogen", "heat", "ammonia", "methanol"]:
            comp.append(dict(country=c, carrier=oc, bas_fixed_mwh=m.get(f"bas_{oc}_mwh", 0.0), s2b_technology_data_mwh=m.get(f"s2b_td_{oc}_mwh", 0.0), s3_0_idees_mwh=m[f"pe_{oc}_mwh"]))
    write_csv(comp, DEMAND_DIR / "INDUSTRY_2050_COMPARISON_BAS_S2B_S3.csv", ["country", "carrier", "bas_fixed_mwh", "s2b_technology_data_mwh", "s3_0_idees_mwh"])
    # ---- registry fragment (replaces the S2B fragment industry_2050) ------------------------------------------
    src_r = f"ratios:{r_sha}|today:{t_sha}"
    reg.add("industry_carrier_mode", "Main industrial carrier structure = pypsa_eur_2050 with JRC-IDEES-2021 reproduced ratios for all sub-sectors (S3-0, decision 61); "
            "technology-data steel/cement ratios (S2B) kept as sensitivity file INDUSTRY_2050_SUMMARY_*_TD_SENSITIVITY.csv; bas_fixed kept as comparison switch", "pypsa_eur_2050", "flag", "B",
            "S3 instruction S3-0.1", "configs/research/baseline.yaml research.s2.industry", src_r, decision_ref="55,61")
    reg.add("industry_ratio_source", "Sector ratio source for the industrial carrier structure", "jrc_idees_2021_pypsa_eur_v2025.07.0", "flag", "B", "scripts_project/s3_0_industry_ratios.py", "INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", src_r, decision_ref="61")
    reg.add("industry_s2b_comparison_table", "S2B industrial carrier result (technology-data steel/cement, 2019 shares elsewhere) frozen from commit 8d61bd37 for the BAS / S2B / S3-0 comparison (INDUSTRY_2050_COMPARISON_BAS_S2B_S3.csv)",
            "INDUSTRY_2050_SUMMARY_aeo8_ats_relative_S2B_FROZEN.csv", "file", "B", "git 8d61bd37 (S2B)", "research_inputs/demand_v5", s2b_sha, decision_ref="55,61", status="REFERENCE_ONLY")
    reg.add("industry_subsector_mapping", "UNSD industry sub-sectors mapped to PyPSA-Eur sectors with EU27 2019 final-energy weights (file INDUSTRY_SUBSECTOR_MAPPING_UNSD_PYPSA_EUR.csv)", len(mapping_rows), "rows", "C",
            "derived (JRC-IDEES-2021 EU27 weights)", "scripts_project/s3_0_industry.py MAPPING", src_r, decision_ref="61", sensitivity_low=None, sensitivity_high=None, status="REFERENCE_ONLY")
    reg.add("industry_cement_clinker_ratio", "Cement output per clinker: 1 / clinker-input 0.656 (technology-data cement finishing); PyPSA-Eur Cement ratio is per t cement", 1 / cf_ck, "t_cement/t_clinker", "B",
            "technology-data v0.15.0", "cement finishing clinker-input", td_sha, decision_ref="61")
    reg.add("industry_clinker_emission_factor_ipcc", "Default clinker CO2 emission factor corrected for CKD (EF_cl = 0.510 + 0.011); clinker activity = EDGAR 2.A.1 / EF", EF_CLINKER, "tCO2/t_clinker", "B",
            "IPCC 2006 Guidelines Vol.3 Ch.2 Mineral Industry Emissions", "Section 2.2.1.2 (p.2.12)", src_sha("IPCC2006_V3_Ch2_Mineral_Industry.pdf"), decision_ref="55,61")
    reg.add("industry_subsector_source", "2019 industry sub-sector split source: research-layer UNSD 2019 industry table (shares only; totals = accepted D1 IndustryFinalEnergy)", "industry_cache.json", "file", "B",
            "research_inputs/assembly_v1/sources/industry_cache.json", f"source sha {cache['source_sha256'][:16]}", cache_sha, decision_ref="55,61", status="REFERENCE_ONLY")
    for c, m in main.items():
        w = ws.get(c, {})
        if float(w.get("crude_steel_2019_kt") or 0) > 0:
            reg.add(f"industry_steel_crude_2019_{c}", f"{c} crude steel 2019 (BOF {w['bof_oxygen_kt']} kt, EAF {w['eaf_electric_kt']} kt, other/induction {w['other_kt']} kt)", float(w["crude_steel_2019_kt"]) * 1e3, "t/a", "A",
                    "worldsteel Steel Statistical Yearbook 2020 concise", str(w["source_locator"]), f"raw7 pdf:d9e23af6f925c75c6559a801147bbeaaa0e6e328a7ccbb5e0d412a16c0c92064; extraction:{ws_sha}", country=c, decision_ref="55")
            reg.add(f"industry_steel_2050_{c}", f"{c} crude steel 2050 = 2019 x industry multiplier {m['industry_multiplier']:.4f}; H2-DRI primary {m['primary_dri_2050_t']:.4g} t, scrap EAF {m['secondary_eaf_2050_t']:.4g} t",
                    m["crude_steel_2050_t"], "t/a", "B", "derived", "s3_0_industry.py", ws_sha, country=c, decision_ref="55,61")
            reg.add(f"industry_hydrogen_2050_{c}", f"{c} industrial hydrogen 2050 (H2-DRI steel 1.7 MWh_H2/t via PyPSA-Eur ratio + HVC/chlorine rows); low 0, high technology-data H2-DRI 2.1 MWh/t",
                    m["pe_hydrogen_mwh"], "MWh_H2/a", "C", "derived", "s3_0_industry.py", src_r, country=c, decision_ref="55,61", sensitivity_low=0.0, sensitivity_high=m["pe_hydrogen_mwh"] * 2.1 / 1.7)
        else:
            reg.add(f"industry_steel_crude_2019_{c}", f"{c} not listed in the worldsteel yearbook -> 0", 0.0, "t/a", "A", "worldsteel Steel Statistical Yearbook 2020 concise", "not listed", ws_sha, country=c, decision_ref="55", status="SOURCE_ZERO")
        if m["clinker_2019_t"] > 0:
            reg.add(f"industry_clinker_2019_{c}", f"{c} clinker 2019 = EDGAR 2.A.1 {clinker_kt[c]:.1f} kt CO2 / 0.52; cement = clinker / 0.656", m["clinker_2019_t"], "t/a", "B", "EDGAR 2025 2.A.1 / IPCC default EF", "s3_0_industry.py", ed_sha, country=c, decision_ref="55,61")
        else:
            reg.add(f"industry_clinker_2019_{c}", f"{c} EDGAR 2.A.1 empty or 0 -> no clinker activity", 0.0, "t/a", "A", "EDGAR 2025", "2.A.1 row", ed_sha, country=c, decision_ref="55", status="SOURCE_ZERO")
        reg.add(f"industry_subsector_rows_{c}", f"{c} UNSD 2019 industry sub-sector rows present: {m['unsd_subsector_rows_present'] or 'none (all in other)'}", m["unsd_subsector_rows_present"] or "none", "list", "B",
                "research-layer UNSD 2019 industry table", "industry_cache.json", cache_sha, country=c, decision_ref="55", status="REFERENCE_ONLY")
        reg.add(f"industry_biomass_overflow_to_gas_{c}", f"{c} solid-biomass demand above the national main potential moved to methane (industry {m['biomass_overflow_industry_to_gas_mwh']:.4g}, agriculture {m['biomass_overflow_agriculture_to_gas_mwh']:.4g} MWh)",
                m["biomass_overflow_industry_to_gas_mwh"] + m["biomass_overflow_agriculture_to_gas_mwh"], "MWh/a", "B", "derived (decision 36)", "s3_0_industry.py", sha256(BIOMASS_DIR / "BIOMASS_POTENTIAL_2050.csv"), country=c, decision_ref="36,55",
                status="REGISTERED" if (m["biomass_overflow_industry_to_gas_mwh"] + m["biomass_overflow_agriculture_to_gas_mwh"]) > 0 else "SOURCE_ZERO")
        reg.add(f"industry_coal_retained_2050_{c}", f"{c} coal still used in 2050 industry routes ({m['coal_retained_in'] or 'none'})", m["coal_retained_2050_mwh"], "MWh/a", "C", "derived", "s3_0_industry.py", src_r, country=c, decision_ref="55,61",
                sensitivity_low=0.0, sensitivity_high=m["coal_retained_2050_mwh"], status="REGISTERED" if m["coal_retained_2050_mwh"] > 0 else "SOURCE_ZERO")
        reg.add(f"industry_low_temperature_heat_2050_{c}", f"{c} industrial low-temperature heat demand 2050 from the PyPSA-Eur ratio heat rows (industry low-T heat bus)", m["pe_heat_mwh"], "MWh/a", "B", "derived", "s3_0_industry.py", src_r, country=c,
                decision_ref="61", status="REGISTERED" if m["pe_heat_mwh"] > 0 else "SOURCE_ZERO")
        reg.add(f"industry_ammonia_2050_{c}", f"{c} industrial ammonia demand 2050 (fertiliser/chemicals; PyPSA-Eur Ammonia sector share of the chemical sub-sector x 5.166 MWh_NH3/t)", m["pe_ammonia_mwh"], "MWh_NH3/a", "C", "derived",
                "s3_0_industry.py (EU27 2019 ammonia energy share of basic chemicals, script lines 431-436)", src_r, country=c, decision_ref="61", sensitivity_low=0.0, sensitivity_high=m["pe_ammonia_mwh"] * 1.2,
                status="REGISTERED" if m["pe_ammonia_mwh"] > 0 else "SOURCE_ZERO")
        reg.add(f"industry_methanol_2050_{c}", f"{c} industrial methanol demand 2050 (PyPSA-Eur Methanol sector share x 5.528 MWh_MeOH/t)", m["pe_methanol_mwh"], "MWh_MeOH/a", "C", "derived", "s3_0_industry.py", src_r, country=c, decision_ref="61",
                sensitivity_low=0.0, sensitivity_high=m["pe_methanol_mwh"] * 1.2, status="REGISTERED" if m["pe_methanol_mwh"] > 0 else "SOURCE_ZERO")
    for r in other_rows:
        if r["mode"] != "aeo8_ats_relative":
            continue
        mix = ", ".join(f"{car} {r[f'other_2019_{car}_mwh'] / r['other_2019_mwh']:.1%}" for car in CARRIERS if r["other_2019_mwh"] and r[f"other_2019_{car}_mwh"] > 0)
        reg.add(f"industry_other_bucket_2019_{r['country']}", f"{r['country']} UNSD 2019 industry energy in the other bucket (other / construction / mining after steel and cement) = "
                f"{r['other_share_of_industry_2019']:.1%} of industry; carrier mix {mix or 'none'}", r["other_2019_mwh"], "MWh/a", "B", "derived", "s3_0_industry.py (S3B R2)", f"{cache_sha}|ois:{ois_sha}",
                country=r["country"], decision_ref="67", status="REFERENCE_ONLY" if r["other_2019_mwh"] > 0 else "SOURCE_ZERO")
    reg.write(REG_DIR / "fragments" / "industry_2050.csv")
    write_json(dict(script=SCRIPT, sources=dict(industry_cache=cache_sha, worldsteel=ws_sha, edgar=ed_sha, technology_data=td_sha, ratios=r_sha, today=t_sha, ois_today=ois_sha), parameters=PE,
                    other_bucket=dict(subsectors=OTHER_BUCKET, ois_today_shares=ois_today, main="pypsa_eur_2050", sensitivity="idees_today", suffix=OTHER_BUCKET_SUFFIX["idees_today"]),
                    eu27_chemicals_split_mwh=dict(basic=basic_fec_mwh, ammonia=nh3_mwh, chlorine=cl_mwh, methanol=meoh_mwh, hvc=hvc_mwh), gaps=gaps, summary_main=outputs["aeo8_ats_relative"]),
               DEMAND_DIR / "INDUSTRY_2050_EVIDENCE.json")
    s = pd.DataFrame(outputs["aeo8_ats_relative"]).set_index("country")
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
    print((s[[f"pe_{oc}_mwh" for oc in OUT_CARRIERS] + ["biomass_overflow_industry_to_gas_mwh", "biomass_overflow_agriculture_to_gas_mwh"]] / 1e6).round(2).to_string())
    print("gaps:", len(gaps))


if __name__ == "__main__":
    main()
