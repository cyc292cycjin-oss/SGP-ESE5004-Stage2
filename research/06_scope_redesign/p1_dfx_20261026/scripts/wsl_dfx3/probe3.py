"""DFX v3 probe 3 (read-only): new vs committed (834a0f19) demand tables and registry spot checks after the data chain."""
import subprocess
from io import StringIO
from pathlib import Path

import pandas as pd

WT = Path("/home/jin/wt_dfx_v3_20261026")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)


def old(rel):
    return subprocess.run(["git", "show", f"834a0f19:{rel}"], cwd=WT, check=True, capture_output=True, text=True).stdout


S = "research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
n = pd.read_csv(WT / S).set_index("country"); o = pd.read_csv(StringIO(old(S))).set_index("country")
print("== industry summary (anchor, useful_heat_bands): columns that differ (max rel diff) ==")
for col in o.columns:
    if col not in n.columns:
        print("  dropped column", col); continue
    if o[col].dtype.kind in "fi" and n[col].dtype.kind in "fi":
        d = (n[col] - o[col]).abs() / o[col].abs().clip(lower=1.0)
        if d.max() > 1e-9:
            print(f"  {col}: max rel {d.max():.3g}; old sum {o[col].sum() / 1e6:,.3f} -> new {n[col].sum() / 1e6:,.3f} (x1e6)")
    elif not (o[col].astype(str) == n[col].astype(str)).all():
        print(f"  {col}: text differs")
print("  new columns:", [c for c in n.columns if c not in o.columns])
print("== ammonia TWh by country (old -> new) ==")
print(pd.DataFrame({"old": o.pe_ammonia_mwh / 1e6, "new": n.pe_ammonia_mwh / 1e6, "dropped_eu27": n.pe_ammonia_eu27_share_dropped_mwh / 1e6, "t_2050": n.ammonia_2050_t / 1e6}).round(3).to_string())
A = "research_inputs/demand_v5/DEMAND_ANCHOR_AEO8_ATS.csv"
an = pd.read_csv(WT / A).set_index("country"); ao = pd.read_csv(StringIO(old(A))).set_index("country")
print("== anchors: industry multiplier / transport anchor / NEU gas (old -> new) ==")
print(pd.DataFrame({"m_ind_old": ao.industry_multiplier, "m_ind_new": an.industry_multiplier, "tr_old": ao.transport_anchor_mwh / 1e6, "tr_new": an.transport_anchor_mwh / 1e6,
                    "neu_gas_before": an.neu_gas_2050_before_deduction_mwh / 1e6, "ded": an.ammonia_feedstock_gas_deduction_mwh / 1e6, "trunc": an.ammonia_feedstock_gas_truncated_mwh / 1e6,
                    "neu_gas_new": an.neu_gas_2050_mwh / 1e6, "neu_old": ao.get("industry_anchor_mwh", 0) * 0}).round(3).to_string())
T = "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
t = pd.read_csv(WT / T, keep_default_na=False); t["v"] = pd.to_numeric(t.value_2050_mwh, errors="coerce").fillna(0.0)
to = pd.read_csv(StringIO(old(T)), keep_default_na=False); to["v"] = pd.to_numeric(to.value_2050_mwh, errors="coerce").fillna(0.0)
print("== anchor table totals by sector (TWh, old -> new) ==")
print(pd.DataFrame({"old": to.groupby("sector").v.sum() / 1e6, "new": t.groupby("sector").v.sum() / 1e6}).round(3).to_string())
print("rows equal structure:", list(t.country + t.sector + t.carrier + t.account) == list(to.country + to.sector + to.carrier + to.account))
print("== NEU gas rows (ID, MY, VN) ==")
print(t[(t.sector == "NonEnergyUse") & (t.carrier == "gas") & t.country.isin(["ID", "MY", "VN"])][["country", "account", "value_2050_mwh", "growth_method"]].to_string())
R = "research_inputs/registry_v5/DATA_REGISTRY.csv"
r = pd.read_csv(WT / R, dtype=str, keep_default_na=False).set_index("param_id")
for pid in ("industry_ammonia_2050_MY", "industry_ammonia_2050_ID", "industry_ammonia_2050_SG", "industry_ammonia_output_2050_VN", "industry_ammonia_feedstock_gas_deducted_VN", "hvc_primary_fraction_scope",
            "demand_tfec_2050_ID", "demand_sector_split_ras", "demand_sector_fuel_anchor_zeroed", "industry_output_base_year", "cookstove_efficiency_basic_TH", "industry_low_temperature_heat_2050_ID", "shipping_demand_domestic_2050"):
    x = r.loc[pid]
    print(f"-- {pid}: value={x.value[:40]!r} unit={x.unit} tier={x.tier} status={x.status} sens=({x.sensitivity_low[:12]},{x.sensitivity_high[:12]})\n   {x.description[:260]}")
cl = pd.read_csv(WT / "research_inputs/registry_v5/REGISTRY_CHANGELOG_DFX.csv", dtype=str, keep_default_na=False)
print("== changelog by reason ==")
print(cl.reason.str.slice(0, 70).value_counts().to_string())
P = "research_inputs/demand_v5/INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"
pe = pd.read_csv(WT / P)
print("== PYPSA_EUR anchor rows mentioning Ammonia (ID) ==")
print(pe[(pe.country == "ID") & pe.method.str.contains("Ammonia|production rule")][["subsector", "carrier", "mwh_2050", "method"]].to_string())
