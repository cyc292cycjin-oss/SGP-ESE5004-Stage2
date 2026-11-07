"""V4 D2a (copy of W08 scripts/w08_ref_run.py; reference engine scripts/ref patched with the Fable F-02 overflow rule): cumulative steps S0-S7 of the reference engine (scripts/ref = I2 engine + decision 211, see w08_ref_setup.py) for one
configuration. Nothing is solved; the repository is never written.

    W08_REF_SCRATCH=/home/jin/v4w08/ref_main W08_ANCHOR_MODE=ras W08_ID_PAPER_FW=residue PYTHONHASHSEED=0 \
        /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_ref_run.py [--steps S1,S2]

Results: $W08_REF_SCRATCH/results/step_<S>.json (i2_chain.pack format) + meta.json + RUNS.json (timings, gate).
Every step is cached by the SHA256 of its case (resumable after a WSL recycle: a finished step is not run again).
"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "ref"))
import i2_common as cm   # noqa: E402
import i2_engine as E    # noqa: E402
import i2_chain as CH    # noqa: E402

OUT = cm.SCRATCH / "results"


def case_key(case: dict) -> str:
    return hashlib.sha256(pickle.dumps({k: case[k] for k in sorted(case)}, protocol=4)).hexdigest()


def main():
    only = None
    if "--steps" in sys.argv:
        only = set(sys.argv[sys.argv.index("--steps") + 1].split(","))
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    eng = E.Engine(); gate = eng.reproduce()
    I = CH.Inputs()
    steps = CH.build_steps(I, eng)
    runs = dict(config=dict(anchor_mode=CH.W08_ANCHOR_MODE, id_paper_fw=CH.W08_ID_PAPER_FW, scratch=str(cm.SCRATCH)), gate=gate, steps=[])
    meta = dict(gate=gate, anchor_mode=CH.W08_ANCHOR_MODE, id_paper_fw=CH.W08_ID_PAPER_FW,
                inputs=dict(check_id_bio=I.check_id_bio, a_tot=I.a_tot, fw=dict(factor_gj_m3=I.fw_factor, sdmx_km3=I.fw_sdmx_km3, sdmx_mwh=I.fw_sdmx_mwh,
                            mean_km3=CH.IT.ID_FW_MEAN_KM3, mean_mwh=I.fw_mean_mwh, paper_sdmx_mwh=I.paper_fw_sdmx_mwh, paper_sdmx_km3=I.paper_fw_sdmx_km3, sh_nes=I.sh_nes),
                            id_outside_balance=dict(sdmx=I.idb_sdmx, main=I.idb_main), gasoline=I.gas, captive=I.captive))
    (OUT / "meta.json").write_text(json.dumps(meta, default=float))
    jobs = [("S0", "v3", lambda c: {})] + steps
    case = {}
    for code, label, f in jobs:
        case = f(case) if code != "S0" else {}
        if only and code not in only:
            continue
        key = case_key(case)
        p = OUT / f"step_{code}.json"
        if p.exists() and json.loads(p.read_text()).get("case_sha256") == key:
            runs["steps"].append(dict(step=code, cached=True)); print(code, "cached", flush=True); continue
        r = eng.run(case)
        obj = CH.pack(r, f"{code} {label}", dict(case_sha256=key))
        p.write_text(json.dumps(obj, default=float))
        tot = sum(v["T"] for v in r["snap"].values()) / 1e6
        runs["steps"].append(dict(step=code, label=label, seconds=time.time() - t0, asean_T_v2_TWh=tot))
        print(code, label, round(time.time() - t0, 1), "s", round(tot, 6), flush=True)
    runs["m08b_runs"] = eng.n_m08b; runs["s30_runs"] = eng.n_s30; runs["seconds"] = time.time() - t0
    (OUT / "RUNS.json").write_text(json.dumps(runs, default=float, indent=1))
    print("done", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
