"""W08: dump the reference engine's inputs that the repository implementation must reproduce (cells, caches, residue records, step cases'
scalar inputs) to tables/W08_REF_INPUTS.json - the repository tests compare against this file (no I2 scratch access needed in the tests).

    W08_REF_SCRATCH=/home/jin/v4w08/ref_main PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_ref_dump.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "ref"))
import i2_chain as CH   # noqa: E402

W = Path(__file__).resolve().parents[1]


def main():
    I = CH.Inputs()
    out = dict(cells=I.cells.to_dict("records"), cache_full=I.cache_full, cache_a=I.cache_a, cache_a_paper=I.cache_a_paper,
               a_tot=I.a_tot, a_drop=sorted(list(x) for x in I.a_drop), fw=dict(factor=I.fw_factor, sdmx_km3=I.fw_sdmx_km3, sdmx_mwh=I.fw_sdmx_mwh,
               mean_mwh=I.fw_mean_mwh, scale=I.fw_scale, idb_sdmx=I.idb_sdmx, idb_main=I.idb_main, sh_nes=I.sh_nes, paper_sdmx_mwh=I.paper_fw_sdmx_mwh),
               gasoline=I.gas, captive=I.captive, m_v3=I.m_v3,
               pp={k: v for k, v in I.pp.items()}, pp_new={k: v for k, v in I.pp_new.items()}, hvc=I.hvc, hvc_s2=I.hvc_s2, meoh=I.meoh, oth=I.oth,
               vn_el_rows=I.S["vn_el_rows"])
    (W / "tables").mkdir(exist_ok=True)
    (W / "tables/W08_REF_INPUTS.json").write_text(json.dumps(out, default=float) + "\n")
    print("cells", len(I.cells), "a_tot", {k: round(v / 1e6, 4) for k, v in I.a_tot.items()})


if __name__ == "__main__":
    main()
