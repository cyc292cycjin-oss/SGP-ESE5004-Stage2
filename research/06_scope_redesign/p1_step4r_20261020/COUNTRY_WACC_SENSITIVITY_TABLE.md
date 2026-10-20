# R6 分国实际 WACC 表（只做表，不跑敏感性）

方法（11 国同一）：名义 WACC = IEA 资本成本观测站（2025 更新）2024 年 FID 光伏 50–100 MW 区间中点（ID / VN / PH / MY / TH）；其余国家 = 参照国 MY 中点 + (Damodaran 2026-01 国家风险溢价差)；实际 = (1 + 名义) / (1 + IMF WEO 2026-10 CPI 通胀 2028–2030 均值) − 1；TL 无 Damodaran 行 → DATA_PENDING。

| country | nominal_wacc_low | nominal_wacc_high | nominal_wacc_mid | damodaran_crp_pct | imf_inflation_2028_2030_avg | real_wacc_mid | delta_vs_model_pp | annuity_ratio_country_over_model_30y | method |
|---|---|---|---|---|---|---|---|---|---|
| BN | 0.052 | 0.062 | 0.057 | 0.780 | 0.010 | 0.047 | -2.317 | 0.778 | reference MY IEA midpoint 0.065 + (CRP_c - CRP_MY) Damodaran 2026-01 |
| ID | 0.085 | 0.110 | 0.098 | 2.460 | 0.025 | 0.071 | 0.073 | 1.007 | IEA Observatory 2024 solar PV range (midpoint) |
| KH | 0.116 | 0.126 | 0.121 | 7.120 | 0.028 | 0.091 | 2.053 | 1.214 | reference MY IEA midpoint 0.065 + (CRP_c - CRP_MY) Damodaran 2026-01 |
| LA | 0.161 | 0.171 | 0.166 | 11.660 | 0.083 | 0.076 | 0.640 | 1.065 | reference MY IEA midpoint 0.065 + (CRP_c - CRP_MY) Damodaran 2026-01 |
| MM | 0.200 | 0.210 | 0.205 | 15.540 | 0.085 | 0.110 | 4.017 | 1.429 | reference MY IEA midpoint 0.065 + (CRP_c - CRP_MY) Damodaran 2026-01 |
| MY | 0.060 | 0.070 | 0.065 | 1.550 | 0.020 | 0.044 | -2.588 | 0.754 | IEA Observatory 2024 solar PV range (midpoint) |
| PH | 0.070 | 0.085 | 0.078 | 2.460 | 0.031 | 0.045 | -2.456 | 0.766 | IEA Observatory 2024 solar PV range (midpoint) |
| SG | 0.045 | 0.054 | 0.050 | 0.000 | 0.020 | 0.029 | -4.108 | 0.624 | reference MY IEA midpoint 0.065 + (CRP_c - CRP_MY) Damodaran 2026-01 |
| TH | 0.060 | 0.080 | 0.070 | 2.070 | 0.017 | 0.052 | -1.754 | 0.830 | IEA Observatory 2024 solar PV range (midpoint) |
| TL |  |  |  |  | 0.020 |  |  |  | DATA_PENDING (no IEA entry, no Damodaran CRP) |
| VN | 0.085 | 0.100 | 0.092 | 3.900 | 0.045 | 0.045 | -2.455 | 0.766 | IEA Observatory 2024 solar PV range (midpoint) |
