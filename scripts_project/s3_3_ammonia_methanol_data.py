"""S3-3 (decision 44): registry fragment for the ammonia / methanol layer parameters (PyPSA-Eur v2025.07.0 defaults, technology-data v0.15.0 rows).

    python scripts_project/s3_3_ammonia_methanol_data.py
"""
from __future__ import annotations

import pandas as pd

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, write_json

SCRIPT = "scripts_project/s3_3_ammonia_methanol_data.py"
PE_CONFIG = SRC_DIR / "pypsa_eur_v2025.07.0_config.default.yaml"
PE_SCRIPT = SRC_DIR / "pypsa_eur_v2025.07.0_prepare_sector_network.py"
TD = ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv"


def td_value(td, tech, param):
    r = td[(td.technology == tech) & (td.parameter == param)]
    return float(r.value.iloc[0]) if len(r) else None


def main():
    cfg_sha, pe_sha, td_sha = sha256(PE_CONFIG), sha256(PE_SCRIPT), sha256(TD)
    td = pd.read_csv(TD)
    reg = Registry(SCRIPT)
    reg.add("ammonia_methanol_bus_structure", "Single regional ammonia bus (ASEAN ammonia) and methanol bus (ASEAN methanol), country tag ASEAN (decision 44); stores: NH3 (l) storage tank incl. liquefaction, General liquid hydrocarbon storage (product)",
            "regional_single_bus", "method", "B", "S3 instruction S3-3.1 / PyPSA-Eur add_ammonia (spatial.ammonia.nodes) and add_carrier_buses", "prepare_sector_network.py lines 1419-1462, 511-625", pe_sha, decision_ref="44")
    for pid, val, desc, line in [("MWh_MeOH_per_MWh_H2", 0.8787, "methanol output per MWh hydrogen (methanolisation)", "607"), ("MWh_MeOH_per_tCO2", 4.0321, "methanol output per t CO2 input", "608"),
                                 ("MWh_MeOH_per_MWh_e", 3.6907, "methanol output per MWh electricity input", "609"), ("MWh_NH3_per_MWh_H2_cracker", 1.46, "ammonia input per MWh hydrogen from the cracker", "854"),
                                 ("min_part_load_methanolisation", 0.3, "minimum part load of methanolisation links (p_min_pu)", "736")]:
        reg.add(f"ammonia_methanol_{pid}", f"PyPSA-Eur sector option {pid}: {desc}", val, "as in config", "B", "PyPSA-Eur v2025.07.0 config.default.yaml", f"line {line}", cfg_sha, decision_ref="44")
    for tech, params, lines in [("Haber-Bosch", ["electricity-input", "hydrogen-input", "investment", "FOM", "VOM", "lifetime"], "rows 382-389"), ("Ammonia cracker", ["ammonia-input", "investment", "FOM", "lifetime"], "rows 17-20"),
                                ("methanolisation", ["hydrogen-input", "electricity-input", "carbondioxide-input", "heat-output", "investment", "FOM", "lifetime"], "rows 1139-1146"),
                                ("biomass-to-methanol", ["efficiency", "CO2 stored", "investment", "FOM", "VOM", "lifetime"], "rows biomass-to-methanol"), ("methanol", ["CO2 intensity"], "row 1125"),
                                ("NH3 (l) storage tank incl. liquefaction", ["investment", "lifetime"], "row 507"), ("General liquid hydrocarbon storage (product)", ["investment", "lifetime"], "row 256")]:
        for p in params:
            v = td_value(td, tech, p)
            if v is not None:
                reg.add(f"ammonia_methanol_td_{tech.replace(' ', '_').replace('(', '').replace(')', '').replace('.', '').lower()}_{p.replace(' ', '_').replace('-', '_')}", f"technology-data v0.15.0 {tech} {p} (EUR2020 layer, S2-0)", v, "technology-data unit", "B",
                        "technology-data v0.15.0 costs_2050 (EUR2020 layer)", lines, td_sha, decision_ref="44", status="REFERENCE_ONLY")
    reg.add("ammonia_methanol_defaults_built", "PyPSA-Eur default switches reproduced: ammonia true (config line 734: Haber-Bosch, cracker, store), biomass_to_methanol true (731), methanol_to_power ocgt true (728); not built: methanol CCGT/CCGT CC/Allam (false), methanol reforming (false), waste-heat use (no district heat buses), relocation",
            "haber_bosch;ammonia_cracker;ammonia_store;methanolisation;biomass_to_methanol;methanol_ocgt;methanol_store", "list", "B", "PyPSA-Eur v2025.07.0 config.default.yaml lines 722-736; prepare_sector_network.py add_ammonia 1372-1470, add_methanol 3575-3660, add_biomass_to_methanol 983-1002, add_methanol_to_power 1031-1137, methanolisation 4628-4645",
            "see description", f"config:{cfg_sha}|script:{pe_sha}", decision_ref="44", status="REFERENCE_ONLY")
    reg.add("ammonia_methanol_industry_methanol_carbon", "Industrial methanol use releases the methanol carbon in the consuming country (PyPSA-Eur industry methanol link, efficiency2 = 1/MWh_MeOH_per_tCO2 = 0.2482 t/MWh); origin-neutral split follows in S3-5",
            0.2482, "tCO2/MWh_MeOH", "B", "PyPSA-Eur v2025.07.0 prepare_sector_network.py", "lines 4617-4626", pe_sha, decision_ref="44,64")
    reg.write(REG_DIR / "fragments" / "ammonia_methanol.csv")
    write_json(dict(script=SCRIPT, sources=dict(pe_config=cfg_sha, pe_script=pe_sha, technology_data=td_sha)), REG_DIR / "AMMONIA_METHANOL_EVIDENCE.json")
    print("fragment written")


if __name__ == "__main__":
    main()
