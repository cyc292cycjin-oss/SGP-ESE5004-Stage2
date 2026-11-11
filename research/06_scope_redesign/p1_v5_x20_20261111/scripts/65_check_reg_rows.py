import pandas as pd
r = pd.read_csv("/home/jin/wt_v5_x20/research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
for p in ["demand_neu_2050_ID", "geothermal_existing_lifetime", "fleet_lifetime_rule_s1", "onwind_gwa_crosscheck_s4b3", "renewable_capacity_per_sqkm_solar", "hydro_inflow_normalization_main",
          "candidate_cap_geothermal_ID", "s4j2_link_losses", "co2_storage_unified_table", "co2_injection_cap_unified_ID", "co2_injection_cap_ID"]:
    print(p, p in r.index, (r.loc[p, ["value", "unit", "tier", "status"]].tolist() if p in r.index else ""))
print([k for k in r.index if k.startswith("co2_injection_cap")][:30])
