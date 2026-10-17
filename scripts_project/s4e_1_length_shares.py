"""S4E-1: in-country length shares of every cross-border line / link of the S4E integrated build (ledger sensitivity of decision 91a; the method of
s4d_3_data.length_shares) -> research_inputs/corridors/XB_LENGTH_SHARES_S4E1.csv (superset of XB_LENGTH_SHARES_S4D3.csv for the new corridors).

    python scripts_project/s4e_1_length_shares.py --network <S4E-1 integrated build>
"""
from __future__ import annotations

import argparse
from pathlib import Path

from d1_common import ROOT, write_csv
from s4d_3_data import length_shares

OUT = ROOT / "research_inputs/corridors/XB_LENGTH_SHARES_S4E1.csv"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); a = ap.parse_args()
    sh = length_shares(a.network)
    write_csv(sh.to_dict("records"), OUT, list(sh.columns))
    print(len(sh), "components;", int((sh.samples_other > 50).sum()), "with > 50 of 401 samples outside the two end countries")


if __name__ == "__main__":
    main()
