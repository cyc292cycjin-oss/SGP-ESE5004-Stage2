"""W08: reference deduction logs (2019 product deductions: row, from-row, from-other, not found) and conservation data of the final product step
(S6c) of the reference runs main / iid -> tables/W08_REF_DEDUCTION_LOG.csv (used by tests/research/test_v4_products.py)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]


def main():
    rows = []
    for run in ("main", "iid"):
        d = json.loads(Path(f"/home/jin/v4w08/ref_{run}/results/step_S6c.json").read_text())
        for x in d["dlog"]:
            rows.append(dict(run=run, **x))
    pd.DataFrame(rows).to_csv(W / "tables/W08_REF_DEDUCTION_LOG.csv", index=False, float_format="%r", lineterminator="\n")
    print(len(rows))


if __name__ == "__main__":
    main()
