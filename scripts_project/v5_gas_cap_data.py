"""V5 X20 revision 2-3 (decision 244; X20_SPEC.md 1.10): national gas production cap fractions GAS_CAP_FRACTIONS_V5.csv.

The v4 cap table (GAS_PRODUCTION_CAPS_2050_V4.csv, UNSD 2019 marketed production) is not changed; the build multiplies each country's cap by
  rule B field_status (v5 main): MM 0.20 (World Bank 2023: 2030 output < 1/5 of 2022; Yadana contract ends 2028), PH 0 (Malampaya extended to
    about 2034, no proven successor), TL 0 (Bayu-Undan ceased production 2025-06), TH = rule A (31 years at the 2019 rate = 7.8 x proven reserves),
    other countries 1;
  rule A reserve_average: min(1, proven reserves / (31 x 2019 production)), BP 2021 reserves (secondary, via X10), TL 0.
Values copied from the X10 check (work/p1_v5_x10_checks_20261111/GAS_CAPS_BY_COUNTRY.csv columns ruleA_fraction_reserve_average /
ruleB_fraction_field_status; REPORT.md section 2, SHA256 d0a8cb01...), with the X10 sources.
    python scripts_project/v5_gas_cap_data.py --x10 <GAS_CAPS_BY_COUNTRY.csv> --x10-report <REPORT.md>
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_inputs/gas_v5/GAS_CAP_FRACTIONS_V5.csv"
NOTE = {"MM": "World Bank 2023: 2030 production below 1/5 of 2022; Yadana contract to 2028 (X10 LIT_A)",
        "PH": "Malampaya extended to about 2034, no proven successor field (X10 LIT_A)",
        "TL": "Bayu-Undan ceased production 2025-06-04; Greater Sunrise at the earliest 2034 (X10 LIT_A)",
        "TH": "rule B = rule A: 31 years at the 2019 rate = 7.8 x proven reserves (X10)"}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--x10", type=Path, required=True); ap.add_argument("--x10-report", type=Path, required=True)
    a = ap.parse_args(argv)
    g = pd.read_csv(a.x10); g = g[g.country != "ASEAN"]
    h_csv = hashlib.sha256(a.x10.read_bytes()).hexdigest(); h_rep = hashlib.sha256(a.x10_report.read_bytes()).hexdigest()
    t = pd.DataFrame(dict(country=g.country, rule_a_reserve_average=g.ruleA_fraction_reserve_average, rule_b_field_status=g.ruleB_fraction_field_status)   # full precision of the X10 table)
    t["note"] = t.country.map(NOTE).fillna("")
    t["source"] = f"X10 GAS_CAPS_BY_COUNTRY.csv sha256 {h_csv}; X10 REPORT.md sha256 {h_rep} section 2"
    t = t.sort_values("country")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT, index=False, lineterminator="\n")
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
