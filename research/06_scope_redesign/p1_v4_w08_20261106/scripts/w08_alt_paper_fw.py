"""W08 pending question (decision 211 item 2): the implemented reading removes the paper-row share (76.4 %) of the 2010-2017 mean fuelwood (57.2 TWh
2019 at the mean basis) and keeps the non-paper share (23.6 %, 17.7 TWh) as the (b) item; the literal alternative removes the SDMX 2019 paper-row
quantity (41.59 TWh, 16,389 thousand m3) and keeps mean - 41.59 = 33.29 TWh as the (b) item. Both computed with the repository chain (no solver).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_alt_paper_fw.py
Writes tables/W08_ALT_PAPER_FUELWOOD.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "/home/jin/wt_v4_w08/scripts_project")
import v4_industry as V          # noqa: E402
import v4_industry_cache as VC   # noqa: E402
from v4_common import V4_MAIN    # noqa: E402

W = Path(__file__).resolve().parents[1]


def main():
    ch = V.Chain(Path("/home/jin/v4w08/work_alt"))
    rows = []
    for mode in ("ras", "iid"):
        s = dict(V4_MAIN, anchor_mode=mode)
        for reading in ("implemented", "sdmx_2019_paper_quantity"):
            I = V.Inputs()
            fw = I.fw
            if reading == "sdmx_2019_paper_quantity":
                keep = fw["mean_mwh"] - fw["paper_sdmx_mwh"]                       # (b) item = mean - SDMX paper-row quantity
                nonpaper_sdmx = fw["sdmx_mwh"] - fw["paper_sdmx_mwh"]
                I.cache_a_paper = VC.build_cache(I.cells, drop=set(I.a_drop) | {("ID", VC.FW_CODE, "1214G")}, scale={("ID", VC.FW_CODE): keep / nonpaper_sdmx})
                I.fw = dict(fw, share_non_paper=keep / I.idb_main)                   # ats_add = idb_main x share = keep
            snap = V.pack(ch.run(V.final_case(I, s)), reading)
            for c, x in snap["countries"].items():
                rows.append(dict(anchor_mode=mode, reading=reading, country=c, T_v2_TWh=x["T"] / 1e6, other_TWh=x["other"] / 1e6))
            print(mode, reading, round(sum(x["T"] for x in snap["countries"].values()) / 1e6, 3), round(snap["countries"]["ID"]["T"] / 1e6, 3), flush=True)
    t = pd.DataFrame(rows)
    p = t.pivot_table(index=["anchor_mode", "country"], columns="reading", values="T_v2_TWh").reset_index()
    p["alt_minus_implemented_TWh"] = p.sdmx_2019_paper_quantity - p.implemented
    p.to_csv(W / "tables/W08_ALT_PAPER_FUELWOOD.csv", index=False, float_format="%.6f", lineterminator="\n")
    print(p.groupby("anchor_mode").alt_minus_implemented_TWh.sum())


if __name__ == "__main__":
    main()
