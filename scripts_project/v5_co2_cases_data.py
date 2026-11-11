"""V5 X20 revision 3-1 (decision 244; X20_SPEC.md 1.14): annual CO2 injection caps of the two low cases (ii) of research.s2.co2.storage_potential_case
(research_inputs/co2_v5/CO2_STORAGE_CASES_V5.csv, Mt CO2 per year, read directly as annual caps - not potentials divided by years):
  iea_anchor_200    (ii-a) ASEAN 200 Mt/a with ID 90 Mt/a, the rest by the P50 shares (X10 case_ii_a_iea_anchor_mt)
  project_ramp_377  (ii-b) upper end of the announced project capacity x 1.10^20 (X10 case_ii_b_project_ramp_mt)
Values copied from the X10 check (work/p1_v5_x10_checks_20261111/CO2_STORAGE_CASES.csv, X10 REPORT section 3), every country present, no blank cell.
    python scripts_project/v5_co2_cases_data.py --x10 <CO2_STORAGE_CASES.csv> --x10-report <REPORT.md>
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_inputs/co2_v5/CO2_STORAGE_CASES_V5.csv"
COUNTRIES = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--x10", type=Path, required=True); ap.add_argument("--x10-report", type=Path, required=True); a = ap.parse_args(argv)
    x = pd.read_csv(a.x10).set_index("country")
    t = pd.DataFrame(dict(country=COUNTRIES, iea_anchor_200_mt=[float(x.at[c, "case_ii_a_iea_anchor_mt"]) if c in x.index else 0.0 for c in COUNTRIES],
                          project_ramp_377_mt=[float(x.at[c, "case_ii_b_project_ramp_mt"]) if c in x.index else 0.0 for c in COUNTRIES]))
    if t[["iea_anchor_200_mt", "project_ramp_377_mt"]].isna().any().any():
        raise SystemExit("blank cell in the X10 case columns")
    t["source"] = (f"X10 CO2_STORAGE_CASES.csv sha256 {hashlib.sha256(a.x10.read_bytes()).hexdigest()}; X10 REPORT.md sha256 "
                   f"{hashlib.sha256(a.x10_report.read_bytes()).hexdigest()} section 3; IEA 2021 ASEAN CCUS anchor / project list (X10 SOURCES)")
    t["note"] = ["country absent from the X10 table: 0" if c not in x.index else "" for c in COUNTRIES]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT, index=False, lineterminator="\n")
    print(t.drop(columns=["source"]).to_string(index=False)); print("totals", round(t.iea_anchor_200_mt.sum(), 6), round(t.project_ramp_377_mt.sum(), 6))


if __name__ == "__main__":
    main()
