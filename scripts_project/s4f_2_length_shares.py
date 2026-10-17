"""S4F-2: in-country length shares of every cross-border line / link of the S4F integrated build with the optional SG-VN / SG-KH candidates (superset:
new APG #4 end, optional candidates; ledger sensitivity of decision 91a, method of s4d_3_data.length_shares) -> research_inputs/corridors/XB_LENGTH_SHARES_S4F2.csv.

    python scripts_project/s4f_2_length_shares.py --network <S4F-2 integrated build with corridors.optional_sg_vn_kh=on>
"""
from __future__ import annotations

import argparse
from pathlib import Path

from d1_common import ROOT, write_csv
from s4d_3_data import length_shares

OUT = ROOT / "research_inputs/corridors/XB_LENGTH_SHARES_S4F2.csv"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); a = ap.parse_args()
    sh = length_shares(a.network)
    write_csv(sh.to_dict("records"), OUT, list(sh.columns))
    print(len(sh), "components;", int((sh.samples_other > 50).sum()), "with > 50 of 401 samples outside the two end countries")


if __name__ == "__main__":
    main()
