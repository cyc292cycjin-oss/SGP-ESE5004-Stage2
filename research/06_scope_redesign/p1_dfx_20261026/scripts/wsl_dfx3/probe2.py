"""DFX v3 probe 2 (read-only): USGS T12 ASEAN rows, reproduced ammonia_production.csv ASEAN rows, NEU accounts, registry anchor rows."""
from pathlib import Path

import pandas as pd

MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
WT = Path("/home/jin/wt_b4p_20261026")
SRC = MAIN / "research_inputs/registry_v5/sources"
usgs = SRC / "pypsa_eur_data/usgs_myb1-2022-nitro-ert.xlsx"
t = pd.read_excel(usgs, "T12", header=None)
print("== T12 shape", t.shape)
print(t.head(7).iloc[:, :7].to_string())
m = t.astype(str).apply(lambda r: r.str.contains("Indonesia|Malaysia|Vietnam|Viet Nam|Burma|Myanmar|Brunei|Philippines|Thailand|Singapore|Cambodia|Laos|Timor", regex=True).any(), axis=1)
print(t[m].iloc[:, :7].to_string())
print("-- tail (footnotes):")
print(t.tail(9).iloc[:, :2].to_string())
amm = pd.read_csv(WT / "research_inputs/registry_v5/sources/jrc_idees_2021/ammonia_production.csv", index_col=0)
print("== reproduced ammonia_production.csv (ktNH3/a) ASEAN rows:")
print(amm.reindex(["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]).to_string())

dem = pd.read_csv(WT / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", dtype=str, keep_default_na=False)
ne = dem[dem.sector == "NonEnergyUse"].copy()
ne["b"] = pd.to_numeric(ne.base_2019_mwh, errors="coerce").fillna(0.0) / 1e6
ne["v"] = pd.to_numeric(ne.value_2050_mwh, errors="coerce").fillna(0.0) / 1e6
print("== NEU accounts (all countries), 2019 base TWh / 2050 TWh:")
print(ne.groupby(["carrier", "account"])[["b", "v"]].sum().round(3).to_string())
print("== NEU gas by country (2019 / 2050 TWh):")
print(ne[ne.carrier == "gas"].groupby("country")[["b", "v"]].sum().round(3).to_string())
print("== NEU oil by country x account 2050 TWh (nonzero):")
x = ne[(ne.carrier == "oil") & (ne.v > 0)].groupby(["country", "account"]).v.sum().round(3)
print(x.to_string())

reg = pd.read_csv(WT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False)
for pat in ("ats_anchor", "feedstock_process_2B_2D", "cookstove", "clean_cooking", "boiler_efficiency", "useful_heat", "node_allocation", "hvc", "HVC",
            "demand_tfec_2050_", "shipping_demand_domestic", "share_land_transport", "share_transport_", "share_bev", "share_agriculture", "demand_aeo8_c3", "aeo8_c3", "demand_anchor", "demand_base_load_rule", "demand_transport_anchor_rule", "demand_sector_fuel_anchor_zeroed", "industry_output_rule_2050", "industry_output_elasticity", "ammonia"):
    hit = reg[reg.param_id.str.contains(pat, regex=False)]
    print(f"== registry param_ids containing {pat!r}: {len(hit)}")
    print(hit.param_id.head(14).tolist())
r = reg.set_index("param_id")
for pid in ("share_HVC_primary_fraction_2050", "demand_sector_fuel_anchor_zeroed", "demand_transport_anchor_rule", "demand_base_load_rule", "demand_anchor_tl_rule", "industry_output_rule_2050"):
    if pid in r.index:
        print(f"== {pid}: value={r.at[pid, 'value'][:80]!r} status={r.at[pid, 'status']} tier={r.at[pid, 'tier']}")
        print("   desc:", r.at[pid, "description"][:700])
