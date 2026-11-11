"""X20 Q12（决策 246，补记 §3 第 2 条）：Ember 国别光伏观测 CF。算法逐行沿用 s4b_3_wind_calibration.observed（L65-86），只把电源换成 Solar：
CF = 发电 / (8760 x 当年与上年装机均值)，2019-2025，剔除装机增长 > 50 % 的年份；VN 2020-2022 同样不进主值（沿用该函数的 used_in_main）；
取有效年份中位数；只用最大装机 >= 0.2 GW 且有效年份 >= 2 的国家。"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

EMBER = Path(r"D:\ResearchWorkspaces\ASEAN\work\p1_step4b_20261016\sources_s4b\ember\release_generation_yearly_global.csv")
OUT = Path(r"D:\ResearchWorkspaces\ASEAN\work\p1_v5_x20_20261111\cache\q12"); OUT.mkdir(parents=True, exist_ok=True)
ISO3 = {"BRN": "BN", "KHM": "KH", "IDN": "ID", "LAO": "LA", "MMR": "MM", "MYS": "MY", "PHL": "PH", "SGP": "SG", "THA": "TH", "TLS": "TL", "VNM": "VN"}
e = pd.read_csv(EMBER); w = e[(e["Electricity source"] == "Solar") & e["ISO 3 code"].isin(ISO3)].copy()
w["country"] = w["ISO 3 code"].map(ISO3); w = w.sort_values(["country", "Year"])
rows = []
for c, d in w.groupby("country"):
    d = d.set_index("Year")
    for y in range(2019, 2026):
        if y not in d.index:
            continue
        g = d.at[y, "Generation (TWh)"]; cap = d.at[y, "Capacity (GW)"]; cap0 = d.at[y - 1, "Capacity (GW)"] if (y - 1) in d.index else np.nan
        valid, why = True, ""
        if pd.isna(cap) or pd.isna(cap0) or pd.isna(g):
            valid, why = False, "capacity or generation missing"
        elif cap0 <= 0 or cap <= 0:
            valid, why = False, "no capacity"
        elif cap / cap0 - 1 > 0.5:
            valid, why = False, f"capacity growth {cap / cap0 - 1:.0%} > 50 %"
        cf = (g * 1e3) / (8760.0 * (cap + cap0) / 2) if (not pd.isna(cap) and not pd.isna(cap0) and (cap + cap0) > 0 and not pd.isna(g)) else np.nan
        curt = (c == "VN" and 2020 <= y <= 2022)
        rows.append(dict(country=c, year=y, generation_twh=g, capacity_gw=cap, capacity_prev_gw=cap0, cf=cf, valid_growth_rule=valid, exclusion_reason=why,
                         vn_curtailment_period=curt, used_in_main=bool(valid and not curt)))
obs = pd.DataFrame(rows)
obs.to_csv(OUT / "EMBER_SOLAR_CF_YEARS.csv", index=False)
summ = []
for c, d in obs.groupby("country"):
    maxcap = float(d.capacity_gw.max(skipna=True)) if d.capacity_gw.notna().any() else 0.0
    m = d[d.used_in_main]
    summ.append(dict(country=c, max_capacity_gw=maxcap, valid_years_main=int(len(m)), years_main=";".join(map(str, m.year)),
                     cf_obs_median_main=float(m.cf.median()) if len(m) else np.nan, usable=bool(maxcap >= 0.2 and len(m) >= 2)))
S = pd.DataFrame(summ)
S.to_csv(OUT / "EMBER_SOLAR_CF_SUMMARY.csv", index=False)
print(S.to_string(index=False))
json.dump(dict(ember=str(EMBER), ember_sha256=hashlib.sha256(EMBER.read_bytes()).hexdigest(), rows=int(len(obs))), open(OUT / "EMBER_SOLAR_CF_LOG.json", "w"), indent=1)
