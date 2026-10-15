"""R1 (decision 55, S2 supplement 02): industrial final energy 2050 by 2050 process routes.

Method (per country, per allocation variant of the D1 demand table):
  1. The accepted 2019 industry final energy (D1 table, UNSD reconstruction) is split into sub-sectors with the
     research-layer UNSD 2019 industry sub-sector table (assembly_v1/sources/industry_cache.json, shares only).
     Missing sub-sector rows are reported, not estimated (the sub-sector then sits inside "other").
  2. Steel (physical activity): worldsteel SSY2020 2019 crude steel and process split; 2050 production =
     2019 x industry multiplier (R3). 2050 structure = PyPSA-Eur St_primary_fraction 0.3 and DRI_fraction 1.0
     (D1 registry rows from config.default.yaml lines 823-838). Route ratios follow
     scripts/build_industry_sector_ratios.py v2025.07.0 lines 194-206 (DRI + Electric arc = Electric arc + H2_DRI
     + elec_DRI; config lines 839-840). The IDEES-derived "Electric arc" base ratio is not available locally
     (JRC-IDEES-2021 not downloaded); it is replaced by technology-data v0.15.0 "electric arc furnace"
     electricity-input (MPP steel model) and reported as a deviation.
  3. Cement (physical activity): clinker 2019 = EDGAR 2.A.1 / 0.52 tCO2 per t clinker (IPCC 2006 Vol.3 Ch.2
     Section 2.2.1.2, EF_cl = 0.510 + 0.011); 2050 clinker = 2019 x industry multiplier. Ratios: technology-data
     v0.15.0 "cement dry clinker" and "cement finishing" (JRC-EU-TIMES); kiln fuel goes to methane except the
     2019 biomass share of the sub-sector (PyPSA-Eur build_industry_sector_ratios.py lines 653-698 rule).
  4. All other sub-sectors: 2019 energy x industry multiplier with 2019 carrier shares (energy conservation);
     the PyPSA-Eur 2050 ratio re-allocation needs JRC-IDEES-2021 -> DATA_PENDING.
  5. Low-temperature heat: the ratio "heat" row only; the technology-data steel/cement rows carry none and the
     pending sectors have no ratio -> 0 in this round (the former 20 % assumption is dropped).
  6. Solid-biomass demand above the national main potential is moved to methane at equal heat (decision 36).
  7. Coal is retained only where the 2050 routes still use it (reported per country).

    python scripts_project/s2b_industry.py
"""
from __future__ import annotations

import json

import pandas as pd

from d1_common import (ASEAN, BIOMASS_DIR, DEMAND_DIR, REG_DIR, ROOT, SRC_DIR, Registry, read_csv, sha256, src_sha, write_csv, write_json)

SCRIPT = "scripts_project/s2b_industry.py"
CACHE = ROOT / "research_inputs/assembly_v1/sources/industry_cache.json"
WORLDSTEEL = "WORLDSTEEL_2019_ASEAN.csv"
EDGAR = "EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv"
TD = ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv"
PE_SCRIPT = "pypsa_eur_v2025.07.0_build_industry_sector_ratios.py"
PE_CONFIG = "pypsa_eur_v2025.07.0_config.default.yaml"
ALLOCATIONS = {"aeo8_ats_relative": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "gdp": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_GDP_SENSITIVITY.csv",
               "population": "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_POP_SENSITIVITY.csv"}
CARRIERS = ["coal", "oil", "gas", "biomass", "electricity"]
FUELS = ["coal", "oil", "gas", "biomass"]
EF_CLINKER = 0.52          # tCO2 / t clinker, IPCC 2006 Vol.3 Ch.2 Section 2.2.1.2 (EF_cl = 0.510 + 0.011, CKD-corrected default)
H2_DRI = 1.7               # MWh_H2 / t steel, PyPSA-Eur v2025.07.0 config.default.yaml line 839 (industry: H2_DRI)
ELEC_DRI = 0.322           # MWh_el / t steel, config line 840 (industry: elec_DRI)
PENDING_SOURCE = "JRC-IDEES-2021 Industry EU27 workbook (JRC-IDEES-2021_Industry_EU27.xlsx inside https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/POTEnCIA/JRC-IDEES-2021/JRC-IDEES-2021.zip)"


def td_value(td, tech, param):
    r = td[(td.technology == tech) & (td.parameter == param)]
    if len(r) != 1:
        raise ValueError(f"technology-data row {tech}/{param} not unique")
    return float(r.value.iloc[0]), str(r.unit.iloc[0]), int(r.index[0]) + 2   # +2 = csv line number (header + 0-based)


def main():
    cache = json.loads(CACHE.read_text()); cache_sha = sha256(CACHE)
    cdf = pd.DataFrame(cache["records"]); subs = [c for c in cdf.columns if c not in ("country", "carrier")]
    for s_ in subs:
        cdf[s_] = cdf[s_].astype(float)
    ws = {r["iso2"]: r for r in read_csv(SRC_DIR / WORLDSTEEL)}; ws_sha = src_sha(WORLDSTEEL)
    ed = pd.read_csv(SRC_DIR / EDGAR); ed_sha = src_sha(EDGAR)
    clinker_kt = {c: float(ed[(ed.iso == c) & (ed.ipcc_code_2006_for_standard_report == "2.A.1")].kt_CO2_2019.fillna(0.0).sum()) for c in ASEAN}
    td = pd.read_csv(TD); td_sha = sha256(TD)
    eaf_el, eaf_u, eaf_line = td_value(td, "electric arc furnace", "electricity-input")
    bof_coal, bof_u, bof_line = td_value(td, "blast furnace-basic oxygen furnace", "coal-input")
    ck_heat, ck_heat_u, ck_heat_line = td_value(td, "cement dry clinker", "heat-input")
    ck_el, ck_el_u, ck_el_line = td_value(td, "cement dry clinker", "electricity-input")
    ck_gas, _, ck_gas_line = td_value(td, "cement dry clinker", "gas-input")
    cf_el, cf_el_u, cf_el_line = td_value(td, "cement finishing", "electricity-input")
    cf_ck, cf_ck_u, cf_ck_line = td_value(td, "cement finishing", "clinker-input")
    reg_df = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    st_primary = float(reg_df.loc["share_St_primary_fraction_2050", "value"]); dri_frac = float(reg_df.loc["share_DRI_fraction_2050", "value"])
    bio = pd.read_csv(BIOMASS_DIR / "BIOMASS_POTENTIAL_2050.csv")
    solid_pot = bio[bio.feedstock_group != "biogas"].assign(p=pd.to_numeric(bio.potential_main_mwh, errors="coerce").fillna(0.0)).groupby("country").p.sum().to_dict()
    pe_sha, cfg_sha = src_sha(PE_SCRIPT), src_sha(PE_CONFIG)
    outputs = {}
    reg = Registry(SCRIPT)
    gaps = []
    for mode, fname in ALLOCATIONS.items():
        dem = pd.read_csv(DEMAND_DIR / fname, keep_default_na=False)
        rows, summary = [], []
        for c in ASEAN:
            d = dem[(dem.country == c) & (dem.sector == "Industry")]
            if not len(d):
                continue
            mult = float(d.multiplier_total.iloc[0])
            e19 = {car: float(d[d.carrier == car].base_2019_mwh.sum()) for car in CARRIERS}
            ag_bio_50 = float(pd.to_numeric(dem[(dem.country == c) & (dem.sector == "AgricultureOthers") & (dem.carrier == "biomass")].value_2050_mwh, errors="coerce").fillna(0).sum())
            # 1. sub-sector shares from the UNSD 2019 industry table (shares only; totals stay the accepted D1 values)
            cc = cdf[cdf.country == c].set_index("carrier")
            sub19 = {s_: {} for s_ in subs}
            present = []
            for car in CARRIERS:
                col = cc.loc[car] if car in cc.index else None
                tot = float(col[subs].sum()) if col is not None else 0.0
                for s_ in subs:
                    share = (float(col[s_]) / tot) if (col is not None and tot > 0) else (1.0 if s_ == "other" else 0.0)
                    sub19[s_][car] = e19[car] * share
            for s_ in subs:
                if sum(sub19[s_].values()) > 0 and s_ != "other":
                    present.append(s_)
            def take(bucket, want, label):
                """Remove `want` (by carrier) from `bucket`; return what could be taken and log the shortfall."""
                got = {}
                for car in CARRIERS:
                    t = min(want.get(car, 0.0), bucket.get(car, 0.0)); bucket[car] = bucket.get(car, 0.0) - t; got[car] = t
                    if want.get(car, 0.0) - t > 1e-6:
                        gaps.append(dict(mode=mode, country=c, item=label, carrier=car, mwh=want[car] - t))
                return got

            def spread(amount_fuel, amount_el, bucket):
                """Allocate a fuel amount over the bucket's fuel carriers proportionally (electricity separately)."""
                ft = sum(bucket.get(f, 0.0) for f in FUELS)
                out = {f: (amount_fuel * bucket.get(f, 0.0) / ft if ft > 0 else 0.0) for f in FUELS}
                if ft <= 0 and amount_fuel > 0:
                    out["coal"] = amount_fuel   # no fuel in the bucket: book against coal so the shortfall is logged by take()
                out["electricity"] = amount_el
                return out

            # 2. steel
            w = ws.get(c, {})
            crude = float(w.get("crude_steel_2019_kt") or 0.0) * 1e3; bof = float(w.get("bof_oxygen_kt") or 0.0) * 1e3
            eaf = (float(w.get("eaf_electric_kt") or 0.0) + float(w.get("other_kt") or 0.0)) * 1e3   # VN "other" = induction furnace -> EAF (instruction)
            steel19_derived = {"coal": bof * bof_coal, "electricity": eaf * eaf_el}
            want_steel = {car: steel19_derived.get(car, 0.0) for car in CARRIERS}
            if "iron and steel" in present:
                row = dict(sub19["iron and steel"]); steel19_src = "UNSD 2019 sub-sector row (research-layer industry table); activity-derived check vs technology-data ratios"
                if sum(want_steel.values()) > sum(row.values()) * 1.000001:
                    # the UNSD row is smaller than what the worldsteel activity implies: the row is removed and the excess leaves 'other'
                    excess = {car: max(0.0, want_steel[car] - row[car]) for car in CARRIERS}
                    got = take(sub19["other"], excess, "steel: activity-derived 2019 energy above the UNSD row, excess not found in 'other'")
                    steel19 = {car: row[car] + got[car] for car in CARRIERS}
                    gaps.append(dict(mode=mode, country=c, item="UNSD 'iron and steel' row below the worldsteel activity x technology-data ratio; excess removed from 'other' (grade C)", carrier="all", mwh=sum(excess.values())))
                else:
                    steel19 = row   # the UNSD row (incl. energy of processes the ratios do not cover) is replaced entirely by the 2050 route
                sub19["iron and steel"] = {car: 0.0 for car in CARRIERS}
            else:
                steel19_src = "derived: BOF t x BF-BOF coal-input + EAF t x EAF electricity-input (technology-data v0.15.0), subtracted from 'other'"
                steel19 = take(sub19["other"], want_steel, "steel 2019 derived energy exceeds the 'other' bucket")
                if crude > 0:
                    gaps.append(dict(mode=mode, country=c, item="no UNSD 'iron and steel' row; 2019 steel energy derived from technology-data ratios (grade C)", carrier="all", mwh=sum(want_steel.values())))
            prod50 = crude * mult; primary = st_primary * prod50; dri = dri_frac * primary; secondary = prod50 - primary
            steel50 = {"hydrogen": H2_DRI * dri, "electricity": ELEC_DRI * dri + eaf_el * (dri + secondary), "coal": 0.0, "oil": 0.0, "gas": 0.0, "biomass": 0.0, "heat": 0.0}
            if primary - dri > 1e-9:
                gaps.append(dict(mode=mode, country=c, item="primary steel not via DRI (DRI_fraction < 1) has no 2050 route in this round", carrier="coal", mwh=(primary - dri) * bof_coal))
            # 3. cement
            clk19 = clinker_kt[c] * 1e3 / EF_CLINKER
            cem19_derived = {"fuel": (ck_heat + ck_gas) * clk19, "electricity": (ck_el + cf_el / cf_ck) * clk19}
            if "non-metallic minerals" in present:
                nmm19 = dict(sub19["non-metallic minerals"]); nmm_src = "UNSD 2019 non-metallic-minerals row; cement part = EDGAR clinker x technology-data ratios, any excess taken from 'other'"
                fuel_tot = sum(nmm19[f] for f in FUELS)
                bio_share = (nmm19["biomass"] / fuel_tot) if fuel_tot > 0 else 0.0
                want = spread(cem19_derived["fuel"], cem19_derived["electricity"], nmm19)
                got = take(nmm19, want, "cement: derived 2019 energy above the UNSD non-metallic-minerals row (logged, then taken from 'other')")
                excess = {car: max(0.0, want[car] - got[car]) for car in CARRIERS}
                if sum(excess.values()) > 1e-6:
                    got2 = take(sub19["other"], spread(sum(excess[f] for f in FUELS), excess["electricity"], sub19["other"]), "cement: excess over the NMM row not found in 'other'")
                    gaps.append(dict(mode=mode, country=c, item="UNSD 'non-metallic minerals' row below the EDGAR clinker x technology-data ratio; excess removed from 'other' (grade C)", carrier="all", mwh=sum(excess.values())))
                else:
                    got2 = {car: 0.0 for car in CARRIERS}
                cem19 = {car: got[car] + got2[car] for car in CARRIERS}
                nmm_rest19 = dict(nmm19)   # ceramics, glass, lime etc. (ratio pending)
                sub19["non-metallic minerals"] = {car: 0.0 for car in CARRIERS}
            else:
                nmm_src = "no UNSD 'non-metallic minerals' row; cement 2019 energy derived from EDGAR clinker x technology-data ratios, subtracted from 'other' (grade C)"
                bio_share = 0.0
                cem19 = take(sub19["other"], spread(cem19_derived["fuel"], cem19_derived["electricity"], sub19["other"]), "cement 2019 derived energy exceeds the 'other' bucket")
                nmm_rest19 = {car: 0.0 for car in CARRIERS}
                if clk19 > 0:
                    gaps.append(dict(mode=mode, country=c, item="no UNSD 'non-metallic minerals' row; 2019 cement energy derived (grade C)", carrier="all", mwh=cem19_derived["fuel"] + cem19_derived["electricity"]))
            clk50 = clk19 * mult
            kiln50 = (ck_heat + ck_gas) * clk50
            cement50 = {"gas": kiln50 * (1 - bio_share), "biomass": kiln50 * bio_share, "electricity": (ck_el + cf_el / cf_ck) * clk50, "coal": 0.0, "oil": 0.0, "hydrogen": 0.0, "heat": 0.0}
            # 4. remaining sub-sectors: 2019 carriers x multiplier (ratio re-allocation pending)
            rest19 = {car: 0.0 for car in CARRIERS}
            for s_ in subs:
                for car in CARRIERS:
                    rest19[car] += sub19[s_][car]
            for car in CARRIERS:
                rest19[car] += nmm_rest19[car]
            rest50 = {car: rest19[car] * mult for car in CARRIERS}
            # totals
            pe = {car: rest50.get(car, 0.0) + steel50.get(car, 0.0) + cement50.get(car, 0.0) for car in CARRIERS + ["hydrogen", "heat"]}
            bas = {car: e19[car] * mult for car in CARRIERS}
            # 6. biomass overflow -> methane (industry first, then agriculture)
            pot = float(solid_pot.get(c, 0.0)); fixed = pe["biomass"] + ag_bio_50
            overflow = max(0.0, fixed - pot)
            ov_ind = min(overflow, pe["biomass"]); ov_ag = min(overflow - ov_ind, ag_bio_50)
            pe_final = dict(pe); pe_final["biomass"] -= ov_ind; pe_final["gas"] += ov_ind
            bas_fixed = float(e19["biomass"] * mult); bas_over = max(0.0, bas_fixed + ag_bio_50 - pot); bas_ov_ind = min(bas_over, bas_fixed); bas_ov_ag = min(bas_over - bas_ov_ind, ag_bio_50)
            for s_, src, dd in [("iron and steel", steel19_src, steel19)]:
                for car in CARRIERS:
                    rows.append(dict(country=c, subsector="iron and steel", carrier=car, mwh_2019=dd.get(car, 0.0), mwh_2050=steel50.get(car, 0.0), route="DRI(H2)+EAF 0.3 / scrap EAF 0.7", method=src, tier="B", status="REGISTERED"))
                rows.append(dict(country=c, subsector="iron and steel", carrier="hydrogen", mwh_2019=0.0, mwh_2050=steel50["hydrogen"], route="H2-DRI 1.7 MWh_H2/t", method="PyPSA-Eur config H2_DRI", tier="C", status="REGISTERED"))
            for car in CARRIERS:
                rows.append(dict(country=c, subsector="cement", carrier=car, mwh_2019=cem19.get(car, 0.0), mwh_2050=cement50.get(car, 0.0), route="dry clinker kiln -> methane (+2019 biomass share); clinker/finishing electricity",
                                 method=nmm_src, tier="B", status="REGISTERED"))
            for car in CARRIERS:
                rows.append(dict(country=c, subsector="other sub-sectors (chemicals energy, non-ferrous, NMM excl. cement, other)", carrier=car, mwh_2019=rest19[car], mwh_2050=rest50[car],
                                 route="2019 carrier shares x industry multiplier", method="PyPSA-Eur 2050 ratio re-allocation pending (JRC-IDEES-2021)", tier="C", status="DATA_PENDING_RATIOS"))
            summary.append(dict(country=c, industry_multiplier=mult, crude_steel_2019_t=crude, crude_steel_2050_t=prod50, primary_dri_2050_t=dri, secondary_eaf_2050_t=secondary,
                                clinker_2019_t=clk19, clinker_2050_t=clk50, cement_kiln_biomass_share_2019=bio_share, unsd_subsector_rows_present=";".join(present),
                                **{f"bas_{car}_mwh": bas[car] for car in CARRIERS}, bas_hydrogen_mwh=0.0, bas_heat_mwh=0.0,
                                **{f"pe_{car}_mwh": pe_final[car] for car in CARRIERS + ["hydrogen", "heat"]},
                                pe_biomass_before_overflow_mwh=pe["biomass"], biomass_overflow_industry_to_gas_mwh=ov_ind, biomass_overflow_agriculture_to_gas_mwh=ov_ag,
                                bas_biomass_overflow_industry_to_gas_mwh=bas_ov_ind, bas_biomass_overflow_agriculture_to_gas_mwh=bas_ov_ag,
                                solid_biomass_potential_main_mwh=pot, agriculture_biomass_2050_mwh=ag_bio_50,
                                coal_retained_2050_mwh=pe_final["coal"], coal_retained_in="other sub-sectors (2019 shares; ratio pending)" if pe_final["coal"] > 0 else "",
                                steel_coal_removed_2050_mwh=steel19.get("coal", 0.0) * mult, cement_fuel_to_methane_2050_mwh=cement50["gas"]))
        outputs[mode] = dict(rows=rows, summary=summary)
        write_csv(rows, DEMAND_DIR / f"INDUSTRY_2050_PYPSA_EUR_{mode}.csv", list(rows[0].keys()))
        write_csv(summary, DEMAND_DIR / f"INDUSTRY_2050_SUMMARY_{mode}.csv", list(summary[0].keys()))
    write_csv(gaps, DEMAND_DIR / "INDUSTRY_2050_GAPS.csv", ["mode", "country", "item", "carrier", "mwh"])
    # ---- registry (main allocation) ------------------------------------------------------------------------------
    main = {r["country"]: r for r in outputs["aeo8_ats_relative"]["summary"]}
    src_td = f"technology-data v0.15.0 EUR2020 layer:{td_sha}"
    reg.add("industry_carrier_mode", "Main industrial carrier structure = pypsa_eur_2050 (R1, decision 55); bas_fixed (AEO8 BAS 2019 carrier shares x multiplier) kept as comparison switch research.s2.industry.carrier_mode",
            "pypsa_eur_2050", "flag", "B", "S2 supplement 02 R1", "configs/research/baseline.yaml", pe_sha, decision_ref="55")
    reg.add("industry_pypsa_eur_H2_DRI", "Hydrogen input of H2 direct reduction per tonne steel (PyPSA-Eur route DRI + Electric arc)", H2_DRI, "MWh_H2/t_steel", "C",
            "PyPSA-Eur v2025.07.0 config.default.yaml", "industry: H2_DRI, line 839; applied in scripts/build_industry_sector_ratios.py line 202", cfg_sha, decision_ref="21,55", sensitivity_low=H2_DRI, sensitivity_high=2.1)
    reg.add("industry_pypsa_eur_elec_DRI", "Electricity input of the DRI shaft per tonne steel (PyPSA-Eur route DRI + Electric arc)", ELEC_DRI, "MWh_el/t_steel", "C",
            "PyPSA-Eur v2025.07.0 config.default.yaml", "industry: elec_DRI, line 840; applied in build_industry_sector_ratios.py line 205", cfg_sha, decision_ref="21,55", sensitivity_low=ELEC_DRI, sensitivity_high=1.03)
    reg.add("industry_eaf_electricity_td_v015", f"Electric arc furnace electricity input ({eaf_u}); replaces the JRC-IDEES 'Electric arc' base ratio of PyPSA-Eur (IDEES not available locally)",
            eaf_el, eaf_u, "B", "technology-data v0.15.0 (MPP steel model)", f"costs_2050_EUR2020.csv line {eaf_line}: electric arc furnace, electricity-input", src_td, decision_ref="55")
    reg.add("industry_bf_bof_coal_td_v015", f"Blast furnace-basic oxygen furnace coal input ({bof_u}); used only to derive 2019 steel energy where the UNSD sub-sector row is missing",
            bof_coal, bof_u, "B", "technology-data v0.15.0 (MPP steel model)", f"costs_2050_EUR2020.csv line {bof_line}", src_td, decision_ref="55", status="REFERENCE_ONLY")
    reg.add("industry_cement_clinker_heat_td_v015", f"Dry clinker kiln heat input per t clinker (technology-data unit label '{ck_heat_u}' read as MWh_th per t clinker, JRC-EU-TIMES ICMDRYPRD01 ~3.4 GJ/t)",
            ck_heat, "MWh_th/t_clinker", "B", "technology-data v0.15.0 (JRC-EU-TIMES)", f"costs_2050_EUR2020.csv line {ck_heat_line}", src_td, decision_ref="55")
    reg.add("industry_cement_clinker_elec_td_v015", "Dry clinker electricity input per t clinker", ck_el, ck_el_u, "B", "technology-data v0.15.0 (JRC-EU-TIMES)", f"costs_2050_EUR2020.csv line {ck_el_line}", src_td, decision_ref="55")
    reg.add("industry_cement_finishing_elec_td_v015", "Cement finishing electricity input per t cement", cf_el, cf_el_u, "B", "technology-data v0.15.0 (JRC-EU-TIMES)", f"costs_2050_EUR2020.csv line {cf_el_line}", src_td, decision_ref="55")
    reg.add("industry_cement_finishing_clinker_input_td_v015", "Clinker per t cement (cement finishing)", cf_ck, cf_ck_u, "B", "technology-data v0.15.0 (JRC-EU-TIMES)", f"costs_2050_EUR2020.csv line {cf_ck_line}", src_td, decision_ref="55")
    reg.add("industry_clinker_emission_factor_ipcc", "Default clinker CO2 emission factor corrected for CKD (EF_cl = 0.510 + 0.011); clinker activity = EDGAR 2.A.1 / EF", EF_CLINKER, "tCO2/t_clinker", "B",
            "IPCC 2006 Guidelines Vol.3 Ch.2 Mineral Industry Emissions", "Section 2.2.1.2 (p.2.12), Equation 2.4 and text 'EF cl = 0.510 + 0.011 = 0.52'", src_sha("IPCC2006_V3_Ch2_Mineral_Industry.pdf"), decision_ref="55")
    reg.add("industry_sector_ratios_pypsa_eur_2050", "PyPSA-Eur 2050 industry sector ratios (MWh/t by carrier for all 27 sub-sectors incl. the low-temperature 'heat' row) require the JRC-IDEES-2021 EU27 workbook; "
            "not available locally and not authorised for download in this round -> chemicals energy, non-ferrous, NMM except cement and other sectors keep 2019 carrier shares; low-temperature heat row = 0",
            None, "MWh/t", "C", PENDING_SOURCE, "scripts/build_industry_sector_ratios.py (load_idees_data line 79-99)", pe_sha, decision_ref="21,55", status="DATA_PENDING")
    reg.add("industry_subsector_source", "2019 industry sub-sector split source: research-layer UNSD 2019 industry table (shares only; totals = accepted D1 IndustryFinalEnergy)", "industry_cache.json", "file", "B",
            "research_inputs/assembly_v1/sources/industry_cache.json (base_industry_totals_2030.csv, UNSD 2019)", f"source sha {cache['source_sha256'][:16]}", cache_sha, decision_ref="55", status="REFERENCE_ONLY")
    for c in ASEAN:
        m = main.get(c)
        if m is None:
            continue
        w = ws.get(c, {})
        if float(w.get("crude_steel_2019_kt") or 0) > 0:
            reg.add(f"industry_steel_crude_2019_{c}", f"{c} crude steel 2019 (BOF {w['bof_oxygen_kt']} kt, EAF {w['eaf_electric_kt']} kt, other/induction {w['other_kt']} kt)", float(w["crude_steel_2019_kt"]) * 1e3, "t/a", "A",
                    "worldsteel Steel Statistical Yearbook 2020 concise", str(w["source_locator"]), f"raw7 pdf:{read_csv(SRC_DIR / 'SHA256SUMS_raw7.txt') if False else 'd9e23af6f925c75c6559a801147bbeaaa0e6e328a7ccbb5e0d412a16c0c92064'}; extraction:{ws_sha}", country=c, decision_ref="55")
            reg.add(f"industry_steel_2050_{c}", f"{c} crude steel 2050 = 2019 x industry multiplier {m['industry_multiplier']:.4f}; primary (H2-DRI) {m['primary_dri_2050_t']:.4g} t, scrap EAF {m['secondary_eaf_2050_t']:.4g} t",
                    m["crude_steel_2050_t"], "t/a", "B", "derived", "s2b_industry.py", ws_sha, country=c, decision_ref="55")
            reg.add(f"industry_hydrogen_2050_{c}", f"{c} industrial hydrogen demand 2050 from H2-DRI steel (low: no primary steel; high: technology-data H2-DRI 2.1 MWh_H2/t_hbi instead of 1.7)",
                    m["pe_hydrogen_mwh"], "MWh_H2/a", "C", "derived", "s2b_industry.py (H2_DRI x primary steel)", cfg_sha, country=c, decision_ref="55",
                    sensitivity_low=0.0, sensitivity_high=m["pe_hydrogen_mwh"] * 2.1 / H2_DRI)
        else:
            reg.add(f"industry_steel_crude_2019_{c}", f"{c} not listed in the worldsteel yearbook -> 0", 0.0, "t/a", "A", "worldsteel Steel Statistical Yearbook 2020 concise", "not listed", ws_sha, country=c, decision_ref="55", status="SOURCE_ZERO")
        if m["clinker_2019_t"] > 0:
            reg.add(f"industry_clinker_2019_{c}", f"{c} clinker 2019 = EDGAR 2.A.1 {clinker_kt[c]:.1f} kt CO2 / 0.52", m["clinker_2019_t"], "t/a", "B", "EDGAR 2025 2.A.1 / IPCC default EF", "s2b_industry.py", ed_sha, country=c, decision_ref="55")
        else:
            reg.add(f"industry_clinker_2019_{c}", f"{c} EDGAR 2.A.1 empty or 0 -> no clinker activity", 0.0, "t/a", "A", "EDGAR 2025", "2.A.1 row", ed_sha, country=c, decision_ref="55", status="SOURCE_ZERO")
        reg.add(f"industry_subsector_rows_{c}", f"{c} UNSD 2019 industry sub-sector rows present: {m['unsd_subsector_rows_present'] or 'none (all in other)'}", m["unsd_subsector_rows_present"] or "none", "list", "B",
                "research-layer UNSD 2019 industry table", "industry_cache.json", cache_sha, country=c, decision_ref="55", status="REFERENCE_ONLY")
        reg.add(f"industry_biomass_overflow_to_gas_{c}", f"{c} solid-biomass demand above the national main potential moved to methane at equal heat (industry {m['biomass_overflow_industry_to_gas_mwh']:.4g}, agriculture {m['biomass_overflow_agriculture_to_gas_mwh']:.4g} MWh)",
                m["biomass_overflow_industry_to_gas_mwh"] + m["biomass_overflow_agriculture_to_gas_mwh"], "MWh/a", "B", "derived (decision 36)", "s2b_industry.py", sha256(BIOMASS_DIR / "BIOMASS_POTENTIAL_2050.csv"), country=c, decision_ref="36,55",
                status="REGISTERED" if (m["biomass_overflow_industry_to_gas_mwh"] + m["biomass_overflow_agriculture_to_gas_mwh"]) > 0 else "SOURCE_ZERO")
        reg.add(f"industry_coal_retained_2050_{c}", f"{c} coal still used in 2050 industry routes ({m['coal_retained_in'] or 'none'}); low = 0 if the pending PyPSA-Eur ratios electrify these sectors, high = value",
                m["coal_retained_2050_mwh"], "MWh/a", "C", "derived", "s2b_industry.py", cache_sha, country=c, decision_ref="55",
                sensitivity_low=0.0, sensitivity_high=m["coal_retained_2050_mwh"], status="REGISTERED" if m["coal_retained_2050_mwh"] > 0 else "SOURCE_ZERO")
        reg.add(f"industry_low_temperature_heat_2050_{c}", f"{c} industrial low-temperature heat demand from the ratio 'heat' rows = 0 (steel/cement technology-data rows carry no low-T heat; other sectors' ratio pending)",
                m["pe_heat_mwh"], "MWh/a", "C", "derived", "s2b_industry.py", pe_sha, country=c, decision_ref="55", status="SOURCE_ZERO")
    reg.write(REG_DIR / "fragments" / "industry_2050.csv")
    write_json(dict(script=SCRIPT, sources=dict(industry_cache=cache_sha, worldsteel=ws_sha, edgar=ed_sha, technology_data=td_sha, pypsa_eur_script=pe_sha, pypsa_eur_config=cfg_sha),
                    constants=dict(EF_CLINKER=EF_CLINKER, H2_DRI=H2_DRI, ELEC_DRI=ELEC_DRI, St_primary_fraction=st_primary, DRI_fraction=dri_frac, eaf_electricity=eaf_el, bf_bof_coal=bof_coal,
                                   clinker_heat=ck_heat, clinker_elec=ck_el, clinker_gas=ck_gas, finishing_elec=cf_el, finishing_clinker=cf_ck),
                    gaps=gaps, summary_main=outputs["aeo8_ats_relative"]["summary"]), DEMAND_DIR / "INDUSTRY_2050_EVIDENCE.json")
    s = pd.DataFrame(outputs["aeo8_ats_relative"]["summary"]).set_index("country")
    print((s[[f"bas_{c}_mwh" for c in CARRIERS] + [f"pe_{c}_mwh" for c in CARRIERS + ["hydrogen"]] + ["biomass_overflow_industry_to_gas_mwh", "biomass_overflow_agriculture_to_gas_mwh", "coal_retained_2050_mwh"]] / 1e6).round(2).to_string())
    print("gaps:", len(gaps))


if __name__ == "__main__":
    main()
