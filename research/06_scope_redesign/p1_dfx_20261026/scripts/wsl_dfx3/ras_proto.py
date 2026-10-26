"""DFX v3 prototype (read-only, scratch): numbers for DFX_RULES.md before any code change.

F1 RAS sector split of the 10 AEO8 countries (NEU out of the seeds), the implied anchors and multipliers, the fuel anchors that turn negative;
F2 ammonia 2050 by the physical output rule (USGS 2019 x G^((2050-2019)/28 x 0.5)) and the NEU gas deduction at 10.8 MWh/t; F3 HVC scope.
Run: /home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/dfx3/ras_proto.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WT = Path("/home/jin/wt_dfx_v3_20261026")
sys.path.insert(0, str(WT / "scripts_project"))
from m08b_demand import SECTORS, FUEL_SECTORS, BASE_SECTORS, RES_ELEC_ATS_MTOE, aeo8_country, c3_ats, gdp_growth  # noqa: E402

C10 = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "VN"]
C11 = C10 + ["TL"]
dem = pd.read_csv(WT / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", dtype=str, keep_default_na=False)
base = pd.to_numeric(dem.base_2019_mwh, errors="coerce").fillna(0.0)
a8 = aeo8_country(); c3 = c3_ats(); g = gdp_growth()
A = {c: a8[c]["tfec_pc_kgoe"] * a8[c]["pop_2050_million"] * 1e3 * 11.63 for c in C11}
A_el = {c: a8[c]["elec_pc_kwh"] * a8[c]["pop_2050_million"] * 1e3 for c in C11}
t19 = {(c, s): float(base[(dem.country == c) & (dem.sector == s)].sum()) for c in C11 for s in SECTORS}
neu19 = {c: float(base[(dem.country == c) & (dem.sector == "NonEnergyUse")].sum()) for c in C11}
print("C.3 ATS 2050 (Mtoe):", {s: c3[s][1] for s in SECTORS}, "sum", round(sum(c3[s][1] for s in SECTORS), 1))
S = np.array([[t19[(c, s)] for s in SECTORS] for c in C10])
row = np.array([A[c] for c in C10])
col_print = np.array([c3[s][1] for s in SECTORS]) * 11.63e6
k = row.sum() / col_print.sum()
col = col_print * k
print(f"sum A_c (10) = {row.sum() / 1e6:,.3f} TWh; sum C.3 x 11.63 = {col_print.sum() / 1e6:,.3f} TWh; k = {k:.12f}")
print("zero seeds:", int((S == 0).sum()), [(C10[i], SECTORS[j]) for i, j in zip(*np.where(S == 0))])
X = S.copy().astype(float)
for it in range(1, 1001):
    r = row / X.sum(axis=1); X = X * r[:, None]
    cc = col / X.sum(axis=0); X = X * cc[None, :]
    er = np.abs(X.sum(axis=1) / row - 1).max(); ec = np.abs(X.sum(axis=0) / col - 1).max()
    if max(er, ec) <= 1e-10:
        break
print(f"RAS converged at iteration {it}: row err {er:.2e}, col err {ec:.2e}")
tfa = {(c, s): X[i, j] for i, c in enumerate(C10) for j, s in enumerate(SECTORS)}
# TL by the current normalised weights (NEU excluded)
g_t = {s: c3[s][1] / c3[s][0] for s in SECTORS}
wt = {s: t19[("TL", s)] * g_t[s] for s in SECTORS}; wsum = sum(wt.values())
for s in SECTORS:
    tfa[("TL", s)] = A["TL"] * wt[s] / wsum
print("sector anchors 10 countries (TWh):", {s: round(sum(tfa[(c, s)] for c in C10) / 1e6, 3) for s in SECTORS})
print("sector anchors 11 countries (TWh):", {s: round(sum(tfa[(c, s)] for c in C11) / 1e6, 3) for s in SECTORS})
# current (v1) anchors for comparison
an1 = pd.read_csv(WT / "research_inputs/demand_v5/DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
# electricity anchors unchanged
is_el = dem.carrier == "electricity"
g_el = dict(g_t); g_el["Residential"] = RES_ELEC_ATS_MTOE[1] / RES_ELEC_ATS_MTOE[0]
rows = []
m_ind_all = {c: (tfa[(c, "Industry")] / t19[(c, "Industry")] if t19[(c, "Industry")] > 0 else None) for c in C11}
for c in C11:
    el19 = {s: float(base[(dem.country == c) & is_el & (dem.sector == s)].sum()) for s in SECTORS}
    w_el = {s: el19[s] * g_el[s] for s in SECTORS}; sw = sum(w_el.values())
    el_anchor = {s: A_el[c] * w_el[s] / sw for s in SECTORS}
    tr_fuel = tfa[(c, "Transport")] - el_anchor["Transport"]
    m_ind = m_ind_all[c] if m_ind_all[c] is not None else float(np.mean([m_ind_all[p] for p in ("KH", "LA", "MM")]))   # TL: no 2019 industry energy -> peer mean (TL rule)
    fuel = {}
    for key, s in FUEL_SECTORS.items():
        raw = tfa[(c, s)] - el_anchor[s]; fb = float(base[(dem.country == c) & (dem.sector == s) & ~is_el].sum())
        fuel[key] = (raw, "negative" if raw < 0 else ("no_2019_fuel_rows" if (raw > 0 and fb <= 0) else ""))
    rows.append(dict(country=c, A_twh=A[c] / 1e6, ind_anchor_v1=an1.at[c, "industry_anchor_mwh"] / 1e6, ind_anchor_v2=tfa[(c, "Industry")] / 1e6,
                     m_ind_v1=an1.at[c, "industry_multiplier"], m_ind_v2=m_ind, tr_anchor_v1=an1.at[c, "transport_anchor_mwh"] / 1e6, tr_anchor_v2=tfa[(c, "Transport")] / 1e6,
                     tr_fuel_v2=tr_fuel / 1e6, res_v2=tfa[(c, "Residential")] / 1e6, com_v2=tfa[(c, "Commercial")] / 1e6, agr_v2=tfa[(c, "AgricultureOthers")] / 1e6,
                     neu_2019=neu19[c] / 1e6, neu_2050_v1=neu19[c] * an1.at[c, "industry_multiplier"] / 1e6, neu_2050_v2=neu19[c] * m_ind / 1e6,
                     **{f"{k}_raw": v[0] / 1e6 for k, v in fuel.items()}, **{f"{k}_zeroed": v[1] for k, v in fuel.items()}))
df = pd.DataFrame(rows).set_index("country")
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
print(df.round(3).to_string())
print("zeroed cells v2:", [(c, k, round(df.at[c, f"{k}_raw"], 3)) for c in C11 for k in FUEL_SECTORS if df.at[c, f"{k}_zeroed"]])
print("sum negative raw (TWh):", round(sum(df.at[c, f"{k}_raw"] for c in C11 for k in FUEL_SECTORS if df.at[c, f"{k}_zeroed"] == "negative"), 3))
# ---- F2 ammonia
amm = pd.read_csv(WT / "research_inputs/registry_v5/sources/jrc_idees_2021/ammonia_production.csv", index_col=0)
F_GAS = 10.8; MWH_NH3 = 5.166
out = []
for c in C11:
    b = float(amm.at[c, "2019"]) if c in amm.index and pd.notna(amm.at[c, "2019"]) else 0.0   # kt NH3
    gf = max(g[c], 1.0) ** ((2050 - 2019) / 28.0 * 0.5)
    nh3 = b * gf   # kt
    neu_gas = float(base[(dem.country == c) & (dem.sector == "NonEnergyUse") & (dem.carrier == "gas")].sum()) * df.at[c, "m_ind_v2"]
    ded = nh3 * 1e3 * F_GAS
    out.append(dict(country=c, G=g[c], growth_factor=gf, nh3_2019_kt=b, nh3_2050_kt=nh3, nh3_2050_twh=nh3 * 1e3 * MWH_NH3 / 1e6, neu_gas_2050_v2_twh=neu_gas / 1e6,
                    deduction_twh=ded / 1e6, neu_gas_after_twh=max(0.0, neu_gas - ded) / 1e6, truncated_twh=max(0.0, ded - neu_gas) / 1e6))
o = pd.DataFrame(out).set_index("country")
print(o.round(4).to_string())
print("ammonia 2050 total Mt:", round(o.nh3_2050_kt.sum() / 1e3, 3), "TWh:", round(o.nh3_2050_twh.sum(), 3))
# v1 ammonia for comparison
s1 = pd.read_csv(WT / "research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country")
print("v1 ammonia TWh by country:", (s1.pe_ammonia_mwh / 1e6).round(3).to_dict(), "total", round(s1.pe_ammonia_mwh.sum() / 1e6, 3))
# ---- F3 HVC scope
HVC = ["NonEnergy:Naphtha", "NonEnergy:Ethane", "NonEnergy:Liquefied petroleum gas (LPG)", "NonEnergy:Natural gas liquids"]
ne = dem[(dem.sector == "NonEnergyUse") & (dem.carrier == "oil")].copy(); ne["b"] = pd.to_numeric(ne.base_2019_mwh, errors="coerce").fillna(0.0)
print("NEU oil accounts:", sorted(ne.account.unique()))
hv = ne[ne.account.isin(HVC)].groupby("country").b.sum(); nh = ne[~ne.account.isin(HVC)].groupby("country").b.sum()
print("NEU oil 2019 HVC feedstock TWh:", round(hv.sum() / 1e6, 3), "non-HVC TWh:", round(nh.sum() / 1e6, 3))
import hashlib  # noqa: E402
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
SRC = WT / "research_inputs/registry_v5/sources"
files = {"aeo8_pdf": Path("/mnt/d/ResearchWorkspaces/ASEAN/research/02_sector_coupling/buildings_heat_alignment/data/raw/buildings/aeo8.pdf"),
         "aeo8_totals_csv": SRC / "AEO8_2050_ASEAN_TOTALS.csv", "aeo8_country_csv": SRC / "AEO8_2050_BY_COUNTRY.csv",
         "d2_gdp_csv": WT / "research_inputs/demand_v5/sources/m08b/AEO8_TABLE_D2_REAL_GDP_PPP2017.csv", "wpp_csv": WT / "research_inputs/demand_v5/sources/m08b/unpopulation_dataportal_20261020224306.csv",
         "ratio_table": WT / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "usgs_xlsx": MAIN / "research_inputs/registry_v5/sources/pypsa_eur_data/usgs_myb1-2022-nitro-ert.xlsx",
         "ammonia_production_csv": SRC / "jrc_idees_2021/ammonia_production.csv", "pe_build_ammonia_script": SRC / "pypsa_eur_data/pypsa_eur_v2025.07.0_build_ammonia_production.py",
         "pypsa_eur_config": SRC / "pypsa_eur_v2025.07.0_config.default.yaml", "pe_ratio_script": SRC / "pypsa_eur_v2025.07.0_build_industry_sector_ratios.py",
         "ratios_2050": WT / "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", "td_costs_2050": WT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv",
         "idees_xlsx": MAIN / "research_inputs/registry_v5/sources/jrc_idees_2021/EU27/JRC-IDEES-2021_Industry_EU27.xlsx", "registry_v1": WT / "research_inputs/registry_v5/DATA_REGISTRY.csv"}
shas = {k: (hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "MISSING") for k, p in files.items()}
print("SHA256:", json.dumps(shas, indent=1))
json.dump(dict(k=k, iterations=it, sum_A10_mwh=float(row.sum()), sum_c3_printed_mwh=float(col_print.sum()), c3_ats_2050_mtoe={s: c3[s][1] for s in SECTORS},
               sector_anchors_10_twh={s: sum(tfa[(c, s)] for c in C10) / 1e6 for s in SECTORS}, sector_anchors_11_twh={s: sum(tfa[(c, s)] for c in C11) / 1e6 for s in SECTORS},
               countries=df.round(6).to_dict("index"), ammonia=o.round(6).to_dict("index"), hvc_accounts=HVC, neu_oil_accounts=sorted(ne.account.unique()),
               sha256={k: v for k, v in shas.items()}, files={k: str(p) for k, p in files.items()}), open("/home/jin/dfx3/ras_proto.json", "w"), indent=1, default=float)
