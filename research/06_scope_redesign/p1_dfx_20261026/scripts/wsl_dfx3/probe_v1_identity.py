"""DFX v3 F5: builds_v1 (base-commit rebuild in the DFX worktree) vs the registered ec80668f networks (results_project/m08b/builds_s01): expected to differ
only in n.meta path fields (s2_network.py:344 bus_mapping_source.path). Read-only."""
import json
import sys
from pathlib import Path

import pypsa

sys.path.insert(0, "/home/jin/wt_dfx_v3_20261026/tests/research")
from test_dfx_demand import _diff_networks  # noqa: E402

RES = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
out = {}
for sc in ("integrated", "disconnected"):
    for res in ("2920_3h", "365_24h"):
        a = pypsa.Network(str(RES / "m08b/builds_s01" / sc / f"{sc}_{res}_unsolved.nc")); b = pypsa.Network(str(RES / "dfx_v3/builds_v1" / sc / f"{sc}_{res}_unsolved.nc"))
        diffs = _diff_networks(a, b)
        loads_eq = set(a.loads.index) == set(b.loads.index) and (a.loads.sort_index().p_set.fillna(0) - b.loads.sort_index().p_set.fillna(0)).abs().max() < 1e-9
        meta_diff = {k for k in set(a.meta) | set(b.meta) if json.dumps(a.meta.get(k), sort_keys=True, default=str) != json.dumps(b.meta.get(k), sort_keys=True, default=str)}
        out[f"{sc}_{res}"] = dict(component_diffs=[list(map(str, d)) for d in diffs], loads_equal=loads_eq, meta_diff=sorted(meta_diff),
                                  meta_detail={k: (str(a.meta.get(k))[:300], str(b.meta.get(k))[:300]) for k in sorted(meta_diff)})
        print(sc, res, "component diffs:", len(diffs), "loads equal:", loads_eq, "meta diff keys:", sorted(meta_diff))
(RES / "dfx_v3/equivalence").mkdir(exist_ok=True)
(RES / "dfx_v3/equivalence/V1_REBUILD_VS_REGISTERED.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
