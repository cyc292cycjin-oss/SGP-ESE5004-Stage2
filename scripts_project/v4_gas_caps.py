"""V4 W08 checklist section 8 F1 (decision 209; W12 section 1): domestic natural-gas production caps on UNSD marketed production and the
fugitive factor on the same cap row.

    PYTHONHASHSEED=0 python scripts_project/v4_gas_caps.py

  cap_c    = UNSD 2019 'Natural gas (including LNG) - production' (TJ GCV) x 0.90 / 0.0036 (the d1_fossil_production.py conversion; W12 table
             research_inputs/gas_v5/W12_UNSD_GAS_2019.csv from the same UNdata export file as the v3.1 gross caps);
  factor_c = EDGAR 2019 1.B.2 (t CO2) / (oil production cap + marketed gas cap) (MWh) - the s2_0_process_emissions.py rule on the new cap row.
v3.1 (gross production, research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050.csv and the registry fugitive_factor_oilgas_* rows) is unchanged;
research.demand.v4.gas_caps = marketed selects GAS_PRODUCTION_CAPS_2050_V4.csv (fugitive_factor_oilgas_v4_* registry rows, fragment v4_w08.csv).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from v4_common import ASEAN, REG_DIR, ROOT, sha256   # noqa: E402

GAS_DIR = ROOT / "research_inputs/gas_v5"
V31 = GAS_DIR / "GAS_PRODUCTION_CAPS_2050.csv"
V4 = GAS_DIR / "GAS_PRODUCTION_CAPS_2050_V4.csv"
FUG = GAS_DIR / "FUGITIVE_FACTORS_V4.csv"
TJ_TO_MWH_NCV = 0.9 / 0.0036
EDGAR = REG_DIR / "sources/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv"


def compute() -> tuple[pd.DataFrame, pd.DataFrame]:
    u = pd.read_csv(GAS_DIR / "W12_UNSD_GAS_2019.csv").set_index("country")
    v31 = pd.read_csv(V31, keep_default_na=False).set_index("country")
    prod = pd.read_csv(REG_DIR / "FOSSIL_PRODUCTION_CAPS_2050.csv")
    oil = {r.country: float(r.cap_mwh_per_year) for r in prod.itertuples() if r.carrier == "oil"}
    ed = pd.read_csv(EDGAR)
    caps, fug = [], []
    for c in v31.index:
        mk = float(u.at[c, "marketed_tj"]) if c in u.index else 0.0
        cap = mk * TJ_TO_MWH_NCV
        e = float(ed[(ed.iso == c) & (ed.ipcc_code_2006_for_standard_report == "1.B.2")].kt_CO2_2019.sum()) * 1e3
        den = oil.get(c, 0.0) + cap
        f = e / den if den > 0 else None
        caps.append(dict(country=c, cap_mwh_per_year=cap, basis=("marketed production (UNSD 'Natural gas (including LNG) - production')" if cap > 0 else "production"),
                         node_allocation=v31.at[c, "node_allocation"], fugitive_factor_id=f"fugitive_factor_oilgas_v4_{c}",
                         note=f"V4 W08 F1 (decision 209): v3.1 gross cap {float(v31.at[c, 'cap_mwh_per_year']):.6g} MWh; marketed {mk:.6g} TJ GCV x 0.90 / 0.0036"))
        fug.append(dict(country=c, edgar_1B2_t=e, oil_cap_mwh=oil.get(c, 0.0), gas_cap_marketed_mwh=cap, gas_cap_gross_mwh=float(v31.at[c, "cap_mwh_per_year"]),
                        factor_t_per_mwh=f, delta_cap_mwh=cap - float(v31.at[c, "cap_mwh_per_year"])))
    return pd.DataFrame(caps), pd.DataFrame(fug)


def main():
    caps, fug = compute()
    caps.to_csv(V4, index=False, lineterminator="\n")
    fug.to_csv(FUG, index=False, lineterminator="\n")
    print(fug.assign(delta_TWh=fug.delta_cap_mwh / 1e6).round(4).to_string(), "\ntotal delta TWh", round(float(fug.delta_cap_mwh.sum()) / 1e6, 3))


if __name__ == "__main__":
    main()
