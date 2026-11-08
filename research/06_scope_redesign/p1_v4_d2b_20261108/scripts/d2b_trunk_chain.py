"""D2b 2.1: oil palm trunk - implied trunk mass per replanted hectare and per tonne FFB from the v3 potential chain (FAOSTAT QCL 2019-2023 means).
Reads the repository tables only; prints a CSV-ready table. No solver."""
import re
import sys
import pandas as pd

R = sys.argv[1] if len(sys.argv) > 1 else "/home/jin/wt_v4_d2b"
q = pd.read_csv(f"{R}/research_inputs/registry_v5/sources/FAOSTAT_QCL_ASEAN11_2019_2024.csv")
bp = pd.read_csv(f"{R}/research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv")
yrs = [f"Y{y}" for y in range(2019, 2024)]
op = q[q.Item == "Oil palm fruit"]
rows = []
for cc in ["ID", "MY", "TH", "PH", "KH"]:
    a = op[(op.ISO2 == cc) & (op.Element == "Area harvested")][yrs].astype(float).mean(axis=1).iloc[0]
    p = op[(op.ISO2 == cc) & (op.Element == "Production")][yrs].astype(float).mean(axis=1).iloc[0]
    t = bp[(bp.country == cc) & (bp.category == "oil_palm_trunk")].iloc[0]
    m = re.search(r"harvested ([0-9,]+) ha x ([0-9.]+) replanting x ([0-9.]+) trees/ha x ([0-9.]+) t OPT.*harvest cap ([0-9.]+)", t.potential_method)
    area, rep, trees, tpt, cap = float(m.group(1).replace(",", "")), float(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5))
    felled = area * rep * trees * tpt                      # t per year (reported mass)
    pot_mass = float(t.mass_main_t)
    eff = efb = None
    rows.append(dict(country=cc, area_harvested_ha_2019_2023=a, area_in_method_ha=area, ffb_t_2019_2023=p, ffb_yield_t_ha=p / a,
                     replant_rate=rep, trees_per_ha=trees, t_per_trunk=tpt, harvest_cap=cap,
                     trunk_t_per_replanted_ha=trees * tpt, trunk_t_per_harvested_ha_yr=rep * trees * tpt,
                     felled_t_yr=felled, potential_mass_t=pot_mass, potential_mass_check=pot_mass / (felled * cap),
                     trunk_t_per_t_ffb_before_cap=felled / p, trunk_t_per_t_ffb_after_cap=pot_mass / p,
                     potential_twh=float(t.potential_main_mwh) / 1e6, lhv_gj_t=float(t.lhv_gj_per_t),
                     potential_low_twh=float(t.potential_low_mwh) / 1e6, potential_high_twh=float(t.potential_high_mwh) / 1e6))
df = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(df.T.to_string())
df.to_csv(sys.argv[2] if len(sys.argv) > 2 else "/home/jin/v4d2b/TRUNK_CHAIN_CHECK.csv", index=False, float_format="%.6g", lineterminator="\n")
