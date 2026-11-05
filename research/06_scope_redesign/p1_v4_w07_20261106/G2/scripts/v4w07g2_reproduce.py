"""G2-0: copy the data chain outside the repository and reproduce the repository VN rows with the unmodified copy (A1: deviation 0 MWh or stop).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/v4w07g2_reproduce.py

Checks: (1) the five s3_0 outputs of the main run are byte-identical to the repository files; (2) the v3 decomposition (APEC run + D163-6 a)
reproduces every VN row of INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv (case main) and the VN other scale of INDUSTRY_V3_EVIDENCE.json.
Writes evidence/_reproduction.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4w07g2_common as cm   # noqa: E402


def main():
    t0 = time.time()
    v3 = cm.import_v3(); fut = v3.future_vectors()
    ch = cm.Chain(); ch.copy()
    res = ch.run(keep_outputs=True)
    rd = cm.REPO / "research_inputs/demand_v5"
    same = {f: res["outs"][f] == (rd / f).read_bytes() for f in cm.S3_OUT}
    lay = cm.v3_layer(v3, res, fut)
    sub = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
    sub = sub[(sub.case == "main") & (sub.country == cm.CC)]
    mine = {}
    for k, v in lay["explicit_carriers"].items():
        for c, x in v.items():
            if abs(x) > 0:
                mine[(k, c)] = x
    for c, x in lay["other"].items():
        if abs(x) > 0:
            mine[("other", c)] = x
    repo = {(r.subsector, r.carrier): float(r.mwh_2050) for r in sub.itertuples()}
    keys = set(mine) | set(repo)
    devs = {f"{k[0]}|{k[1]}": mine.get(k, 0.0) - repo.get(k, 0.0) for k in keys}
    max_dev = max(abs(v) for v in devs.values())
    evj = json.loads((cm.REPO / "research_inputs/industry_v3/INDUSTRY_V3_EVIDENCE.json").read_text())
    scale_repo = float(evj["cases"]["main"]["by_country"][cm.CC]["other_scale"])
    by_sub = {k: sum(v for (s, _), v in repo.items() if s == k) / 1e6 for k in sorted({s for s, _ in repo})}
    out = dict(byte_identical_main_run=same, max_abs_dev_subsector_carrier_mwh=max_dev, n_cells=len(keys),
               T_v2_twh=lay["T"] / 1e6, T_apec_run_twh=lay["T_apec_run"] / 1e6, other_twh=lay["other_total"] / 1e6,
               other_scale=lay["scale"], other_scale_repo=scale_repo, by_subsector_repo_twh=by_sub,
               by_subsector_mine_twh={k: v / 1e6 for k, v in lay["by_sub"].items()}, e19_mwh=res["e19"],
               apec_matrix_sha256=cm.sha256(cm.REPO / cm.APEC_REL), cache_sha256=cm.sha256(cm.REPO / cm.CACHE_REL),
               ats_sha256=cm.sha256(cm.REPO / cm.ATS_REL), s30_sha256=cm.sha256(cm.REPO / cm.S30_REL),
               repo_head=(cm.REPO / ".git").read_text().strip() if (cm.REPO / ".git").is_file() else "", seconds=time.time() - t0)
    (cm.WORK / "evidence").mkdir(exist_ok=True)
    cm.jdump(out, cm.WORK / "evidence/_reproduction.json")
    print(json.dumps({k: v for k, v in out.items() if k not in ("e19_mwh",)}, indent=1, default=float))
    if not all(same.values()) or max_dev > 1e-6 or abs(lay["scale"] - scale_repo) > 1e-12:
        raise SystemExit("STOP: the unmodified copy does not reproduce the repository VN rows")


if __name__ == "__main__":
    main()
