"""DFX v3: the complete v1 / v2 component differences (integrated 2920x3h), to list the derived changes explicitly. Read-only."""
import json
import sys
from pathlib import Path

import numpy as np
import pypsa

sys.path.insert(0, "/home/jin/wt_dfx_v3_20261026/tests/research")
from test_dfx_demand import _diff_networks  # noqa: E402

RES = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/dfx_v3")
for sc in ("integrated", "disconnected"):
    a = pypsa.Network(str(RES / "builds_v1" / sc / f"{sc}_2920_3h_unsolved.nc")); b = pypsa.Network(str(RES / "builds_v2" / sc / f"{sc}_2920_3h_unsolved.nc"))
    print(f"===== {sc}: loads v1 {len(a.loads)} v2 {len(b.loads)}; buses {len(a.buses)} -> {len(b.buses)}; links {len(a.links)} -> {len(b.links)}; generators {len(a.generators)} -> {len(b.generators)}")
    only_a = sorted(set(a.loads.index) - set(b.loads.index)); only_b = sorted(set(b.loads.index) - set(a.loads.index))
    print("loads only in v1:", only_a); print("loads only in v2:", only_b)
    for d in _diff_networks(a, b):
        name, kind, detail = d
        if kind == "index":
            full = sorted(set(a.df(name).index) ^ set(b.df(name).index))
            print(name, kind, len(full), "only_v1:", [x for x in full if x in a.df(name).index], "only_v2:", [x for x in full if x in b.df(name).index])
        else:
            print(name, kind, str(detail)[:400])
    meta_diff = {k for k in set(a.meta) | set(b.meta) if json.dumps(a.meta.get(k), sort_keys=True, default=str) != json.dumps(b.meta.get(k), sort_keys=True, default=str)}
    print("meta diff:", sorted(meta_diff))
    pe_a = a.generators[a.generators.carrier == "process emissions"].p_nom; pe_b = b.generators[b.generators.carrier == "process emissions"].p_nom
    print("process emission p_nom sum (t/h):", float(pe_a.sum()), "->", float(pe_b.sum()))
