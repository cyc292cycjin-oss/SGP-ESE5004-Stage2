"""S2-0.3: industrial process emissions, fugitive emissions and the chemical-feedstock boundary (EDGAR 2025).

Source: EDGAR_2025_GHG, IEA-EDGAR CO2 v4 (fossil CO2), sheet "IPCC 2006", 2019, kt CO2
(extraction/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv; raw zip raw5/IEA_EDGAR_CO2_1970_2024.zip).
Mapping (D1/S2 supplement 0.3): 2.A.1-2.A.4 -> non-metallic minerals; 2.B -> chemicals; 2.C -> metals.
Growth 2019 -> 2050: the D1 country industry multiplier (AEO8 BAS industry total; R3 AEO8 ATS relative allocation in the main table).
Fugitive 1.B: 2019 emission / UNSD 2019 domestic production (MWh) -> emission factor on endogenous
domestic production (countries without production: factor not applicable).
Boundary with the PyPSA-Eur feedstock-carbon accounting: 2.B (chemical industry process CO2),
2.D (non-energy products) and 4.C fossil (waste incineration) are the inventory categories that the
feedstock-carbon method covers; they are tabulated per country and NOT added to the process-emission
bus (method question for the user; Singapore 2.B = 10.36 Mt is the check).
1.A cross-check: EDGAR 1.A.2/1.A.3/1.A.4+1.A.5 vs UNSD-2019 final-energy combustion (D1 base x
technology-data CO2 intensities); 1.A.1 (power, refineries) has no D1 counterpart and is listed only.
"""
from __future__ import annotations

import zipfile

import pandas as pd

from d1_common import (ASEAN, DEMAND_DIR, INTAKE, ISO2_FROM_ISO3, REG_DIR, SRC_DIR, Registry, read_csv, sha256, src_sha,
                       write_csv, write_json)

SCRIPT = "scripts_project/s2_0_process_emissions.py"
EXT = "EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv"
EXT_MD = "EDGAR2025_USGS2025_PROCESS_EMISSIONS.md"
RAW_ZIP = INTAKE / "raw5" / "IEA_EDGAR_CO2_1970_2024.zip"
RAW_ZIP_SHA = "da129df69d608caa81d5079a1c291e93dd02d1406a44342c42bbacce685ed998"
LICENCE = "CC BY-NC-ND 4.0 (research use; cite JRC/IEA EDGAR_2025_GHG)"
GROUPS = {"minerals": ["2.A.1", "2.A.2", "2.A.3", "2.A.4"], "chemicals": ["2.B"], "metals": ["2.C"]}
REFERENCE = {"nonenergy_products_2D": ["2.D"], "waste_incineration_4C": ["4.C"], "fugitive_1B1_solid": ["1.B.1"], "fugitive_1B2_oilgas": ["1.B.2"]}
# technology-data v0.13.2 CO2 intensities (tCO2/MWh_th), identical in v0.15.0
EF = {"coal": 0.3361, "oil": 0.2571, "gas": 0.1980, "biomass": 0.0, "unclassified_fuel": 0.2571, "electricity": 0.0}
SECTOR_TO_1A = {"Industry": "1.A.2", "Transport": "1.A.3", "Residential": "1.A.4+1.A.5", "Commercial": "1.A.4+1.A.5", "AgricultureOthers": "1.A.4+1.A.5"}


def edgar_1a_from_zip():
    z = zipfile.ZipFile(RAW_ZIP)
    name = [n for n in z.namelist() if n.endswith(".xlsx")][0]
    d = pd.read_excel(z.open(name), "IPCC 2006", header=9)
    d = d[d.Country_code_A3.isin(ISO2_FROM_ISO3)]
    code = "ipcc_code_2006_for_standard_report"; nm = code + "_name"
    a = d[d[code].astype(str).str.startswith("1.A")][["Country_code_A3", code, nm, "Y_2019"]].copy()
    a["iso"] = a.Country_code_A3.map(ISO2_FROM_ISO3)
    a = a.rename(columns={code: "ipcc_code", nm: "ipcc_name", "Y_2019": "kt_CO2_2019"})
    return a[["iso", "Country_code_A3", "ipcc_code", "ipcc_name", "kt_CO2_2019"]].sort_values(["iso", "ipcc_code"])


def main():
    ext = pd.read_csv(SRC_DIR / EXT)
    ext_sha = src_sha(EXT)
    sha = f"extraction:{ext_sha}; raw zip:{RAW_ZIP_SHA}"
    dem = pd.read_csv(DEMAND_DIR / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv")
    mult = dem[dem.sector == "Industry"].groupby("country").multiplier_total.first().to_dict()
    mult_pop = None
    pop_path = DEMAND_DIR / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_POP_SENSITIVITY.csv"
    if pop_path.exists():
        dp = pd.read_csv(pop_path); mult_pop = dp[dp.sector == "Industry"].groupby("country").multiplier_total.first().to_dict()
    prod = pd.read_csv(REG_DIR / "FOSSIL_PRODUCTION_CAPS_2050.csv")
    prod_mwh = {(r.country, r.carrier): float(r.cap_mwh_per_year) for r in prod.itertuples()}
    reg = Registry(SCRIPT)
    proc_rows, fug_rows, bound_rows = [], [], []
    for c in ASEAN:
        e = ext[ext.iso == c]
        val = lambda codes: float(e[e.ipcc_code_2006_for_standard_report.isin(codes)].kt_CO2_2019.sum()) * 1e3  # t CO2
        for g, codes in GROUPS.items():
            v19 = val(codes); v50 = v19 * mult[c]
            comp = "; ".join(f"{r.ipcc_code_2006_for_standard_report} {r.kt_CO2_2019:.3f} kt" for r in e[e.ipcc_code_2006_for_standard_report.isin(codes)].itertuples()) or "no EDGAR row (0)"
            status = "REGISTERED" if v19 > 0 else "SOURCE_ZERO"
            in_bus = g != "chemicals"
            proc_rows.append(dict(country=c, group=g, ipcc_codes="+".join(codes), tco2_2019=v19, industry_multiplier=mult[c], tco2_2050=v50,
                                  tco2_2050_pop_sensitivity=(v19 * mult_pop[c]) if mult_pop else "", components=comp,
                                  model_treatment="process emission bus (capturable by process CC)" if in_bus else "covered by feedstock-carbon accounting (not added to the process bus; method question)"))
            reg.add(f"process_emissions_{g}_2019_{c}", f"{c} {g} process CO2 2019 (EDGAR 2025 IPCC 2006 {'+'.join(codes)}: {comp})", v19, "tCO2/a", "B",
                    "EDGAR_2025_GHG IEA-EDGAR CO2 v4, sheet IPCC 2006, 2019; " + LICENCE, f"extraction {EXT} rows {c} {'/'.join(codes)}", sha, country=c,
                    decision_ref="10, L19, S2-0.3", status=status)
            reg.add(f"process_emissions_{g}_2050_{c}", f"{c} {g} process CO2 2050 = 2019 x D1 industry multiplier {mult[c]:.4f} (AEO8 BAS industry; country allocation per research.demand.country_allocation, R3 = AEO8 ATS relative factor)" +
                    ("" if in_bus else "; chemicals (2.B) are covered by the feedstock-carbon accounting and are not loaded on the process bus (user to confirm)"),
                    v50, "tCO2/a", "B", "EDGAR 2025 x D1 DEMAND_2050 industry multiplier", "process_emissions_*_2019 x multiplier_total(Industry)", sha, country=c,
                    sensitivity_low=v19, sensitivity_high=(v19 * mult_pop[c]) if mult_pop else None, decision_ref="10, L19, S2-0.3",
                    status=(status if in_bus else "REFERENCE_ONLY") if v19 > 0 else "SOURCE_ZERO")
        for key, codes in REFERENCE.items():
            v = val(codes)
            reg.add(f"edgar_{key}_2019_{c}", f"{c} EDGAR 2019 {'+'.join(codes)} ({e[e.ipcc_code_2006_for_standard_report.isin(codes)].ipcc_code_2006_for_standard_report_name.iloc[0] if len(e[e.ipcc_code_2006_for_standard_report.isin(codes)]) else 'no row'})",
                    v, "tCO2/a", "A", "EDGAR_2025_GHG IEA-EDGAR CO2 v4 2019; " + LICENCE, f"extraction {EXT}", sha, country=c, decision_ref="10, S2-0.3",
                    status="REFERENCE_ONLY" if v > 0 else "SOURCE_ZERO")
        # fugitive factors on domestic production
        for key, codes, carriers in [("coal", ["1.B.1"], ["coal"]), ("oilgas", ["1.B.2"], ["oil", "gas"])]:
            emis = val(codes); p = sum(prod_mwh.get((c, k), 0.0) for k in carriers)
            if p > 0:
                f = emis / p
                reg.add(f"fugitive_factor_{key}_{c}", f"{c} fugitive CO2 per MWh of domestic {'/'.join(carriers)} production = EDGAR 2019 {'+'.join(codes)} {emis:,.0f} t / UNSD 2019 production {p:,.0f} MWh",
                        f, "tCO2/MWh_production", "B", "EDGAR 2025 1.B / UNSD 2019 production (FOSSIL_PRODUCTION_CAPS_2050.csv)", "1.B divided by production cap row", sha, country=c,
                        sensitivity_low=f * 0.5, sensitivity_high=f * 1.5, decision_ref="10, S2-0.3")
                fug_rows.append(dict(country=c, carriers="+".join(carriers), edgar_codes="+".join(codes), tco2_2019=emis, production_mwh_2019=p, factor_tco2_per_mwh=f, applicable=True))
            else:
                fug_rows.append(dict(country=c, carriers="+".join(carriers), edgar_codes="+".join(codes), tco2_2019=emis, production_mwh_2019=0.0, factor_tco2_per_mwh="", applicable=False))
                if emis > 0:
                    reg.add(f"fugitive_factor_{key}_{c}", f"{c} EDGAR 1.B {'+'.join(codes)} = {emis:,.0f} t but no UNSD domestic {'/'.join(carriers)} production -> factor not applicable (emission listed as reference)",
                            emis, "tCO2/a (not a factor)", "A", "EDGAR 2025", f"extraction {EXT}", sha, country=c, decision_ref="10, S2-0.3", status="REFERENCE_ONLY")
        # feedstock-carbon boundary
        ne = dem[(dem.sector == "NonEnergyUse") & (dem.country == c)]
        feed_c = float(sum(r.base_2019_mwh * EF.get(r.carrier, 0.0) for r in ne.itertuples()))
        b2, d2, c4 = val(["2.B"]), val(["2.D"]), val(["4.C"])
        bound_rows.append(dict(country=c, nonenergy_use_2019_mwh=float(ne.base_2019_mwh.sum()), feedstock_carbon_potential_tco2=feed_c, edgar_2B_chemicals_tco2=b2,
                               edgar_2D_nonenergy_products_tco2=d2, edgar_4C_waste_incineration_fossil_tco2=c4, edgar_2B_2D_4C_total_tco2=b2 + d2 + c4,
                               ratio_edgar_to_feedstock=((b2 + d2 + c4) / feed_c) if feed_c else "",
                               covered_by_feedstock_accounting="2.B, 2.D, 4.C(fossil)", loaded_on_process_bus="2.A (minerals), 2.C (metals)"))
    reg.add("process_emissions_boundary_rule", "EDGAR 2.B (chemical industry), 2.D (non-energy products) and 4.C fossil (waste incineration) are covered by the "
            "feedstock-carbon accounting of the non-energy use (PyPSA-Eur method: naphtha for industry -> process emission from feedstock + non-sequestered HVC -> "
            "HVC to air); only 2.A and 2.C enter the process-emission bus. Singapore check: 2.B 10.36 Mt vs feedstock-carbon potential 20.2 Mt", 1, "flag", "C",
            "S2 supplement 0.3; PyPSA-Eur v2025.07.0 scripts/prepare_sector_network.py add_industry (lines 4690-4800)", "FEEDSTOCK_CARBON_BOUNDARY_2019.csv", sha,
            sensitivity_low=0, sensitivity_high=1, decision_ref="10, S2-0.3 (method question for user)")
    reg.add("steel_process_structure_2019", "Steel base-year process structure (BF-BOF / EAF shares) needed only if S2 models steel routes explicitly; worldsteel Steel "
            "Statistical Yearbook 2019 not in intake", None, "fraction", "A", "worldsteel Steel Statistical Yearbook", "download list", sha, decision_ref="L19", status="DATA_PENDING")
    # 1.A cross-check
    a1 = edgar_1a_from_zip()
    write_csv(a1.to_dict("records"), SRC_DIR / "EDGAR2025_1A_ASEAN11_2019.csv", list(a1.columns))
    chk = []
    tf = dem[dem.sector.isin(SECTOR_TO_1A)]
    for c in ASEAN:
        e = a1[a1.iso == c]
        ed = {k: float(e[e.ipcc_code.str.startswith(k)].kt_CO2_2019.sum()) * 1e3 for k in ["1.A.1", "1.A.2", "1.A.3", "1.A.4", "1.A.5"]}
        model = {}
        for s, k in SECTOR_TO_1A.items():
            d = tf[(tf.country == c) & (tf.sector == s)]
            model[k] = model.get(k, 0.0) + float(sum(r.base_2019_mwh * EF.get(r.carrier, 0.0) for r in d.itertuples()))
        chk.append(dict(country=c, edgar_1A1_power_refining_tco2=ed["1.A.1"], edgar_1A2_industry_tco2=ed["1.A.2"], model_industry_tco2=model["1.A.2"],
                        dev_industry_pct=((model["1.A.2"] / ed["1.A.2"] - 1) * 100) if ed["1.A.2"] else "",
                        edgar_1A3_transport_tco2=ed["1.A.3"], model_transport_domestic_tco2=model["1.A.3"],
                        dev_transport_pct=((model["1.A.3"] / ed["1.A.3"] - 1) * 100) if ed["1.A.3"] else "",
                        edgar_1A4_1A5_other_tco2=ed["1.A.4"] + ed["1.A.5"], model_buildings_agri_tco2=model["1.A.4+1.A.5"],
                        dev_other_pct=((model["1.A.4+1.A.5"] / (ed["1.A.4"] + ed["1.A.5"]) - 1) * 100) if (ed["1.A.4"] + ed["1.A.5"]) else "",
                        edgar_1A_final_sectors_total=ed["1.A.2"] + ed["1.A.3"] + ed["1.A.4"] + ed["1.A.5"], model_final_sectors_total=sum(model.values()),
                        note="model = UNSD 2019 final-energy base x technology-data CO2 intensity (coal 0.3361, oil 0.2571, gas 0.1980); international bunkers excluded on both sides; 1.A.1 not modelled in the D1 base"))
    write_csv(proc_rows, REG_DIR / "PROCESS_EMISSIONS_2019_2050.csv", list(proc_rows[0].keys()))
    write_csv(fug_rows, REG_DIR / "FUGITIVE_EMISSION_FACTORS_2019.csv", list(fug_rows[0].keys()))
    write_csv(bound_rows, REG_DIR / "FEEDSTOCK_CARBON_BOUNDARY_2019.csv", list(bound_rows[0].keys()))
    write_csv(chk, REG_DIR / "EDGAR_1A_VS_UNSD_2019.csv", list(chk[0].keys()))
    reg.write(REG_DIR / "fragments" / "process_emissions.csv")
    write_json(dict(script=SCRIPT, extraction_sha256=ext_sha, raw_zip_sha256=RAW_ZIP_SHA, raw_zip_sha256_actual=sha256(RAW_ZIP) if RAW_ZIP.exists() else None,
                    md_sha256=src_sha(EXT_MD), licence=LICENCE, asean_totals_mt={g: sum(r["tco2_2019"] for r in proc_rows if r["group"] == g) / 1e6 for g in GROUPS},
                    boundary=bound_rows, crosscheck_1A=chk), REG_DIR / "fragments" / "process_emissions.json")
    pd.set_option("display.width", 250)
    p = pd.DataFrame(proc_rows); print((p.pivot_table(index="country", columns="group", values="tco2_2019", aggfunc="sum") / 1e6).round(2).to_string())
    print("2050 minerals+metals Mt:", (p[p.group != "chemicals"].groupby("country").tco2_2050.sum() / 1e6).round(2).to_dict())
    print(pd.DataFrame(fug_rows)[["country", "carriers", "tco2_2019", "production_mwh_2019", "factor_tco2_per_mwh"]].to_string(index=False))
    b = pd.DataFrame(bound_rows); print((b[["country", "feedstock_carbon_potential_tco2", "edgar_2B_chemicals_tco2", "edgar_2D_nonenergy_products_tco2", "edgar_4C_waste_incineration_fossil_tco2"]].set_index("country") / 1e6).round(2).to_string())
    k = pd.DataFrame(chk); print(k[["country", "edgar_1A2_industry_tco2", "model_industry_tco2", "dev_industry_pct", "edgar_1A3_transport_tco2", "model_transport_domestic_tco2", "dev_transport_pct", "edgar_1A4_1A5_other_tco2", "model_buildings_agri_tco2", "dev_other_pct"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
