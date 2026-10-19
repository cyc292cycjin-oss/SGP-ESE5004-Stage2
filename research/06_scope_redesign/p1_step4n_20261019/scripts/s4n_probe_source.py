"""S4N: where does networks/integrated_56_3h_probe_unsolved.nc come from? (read only, no solve)
Compares the packaged probe network with the S4M-1 2920x3h integrated build truncated to 56 snapshots (as s2_solve.py --truncate 56 does for the
S4M-2 smoke) and reads the S4M-2 receipt input_network entry."""
import json, sys
import numpy as np
import pypsa
sys.path.insert(0, "/home/jin/s4n_local/pkg/repo/scripts_project")
RM = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"
probe = pypsa.Network("/home/jin/s4n_local/pkg/networks/integrated_56_3h_probe_unsolved.nc")
full = pypsa.Network(RM + "/results_project/s4m/s4m1/builds/integrated/integrated_2920_3h_unsolved.nc")
rec = json.load(open(RM + "/results_project/s4m/s4m2/solves/s4m_A_integrated/SOLVE_RECEIPT.json"))
res = dict(probe_meta_speed_probe=probe.meta.get("speed_probe"), probe_snapshots=len(probe.snapshots), probe_first=str(probe.snapshots[0]), probe_last=str(probe.snapshots[-1]),
           probe_weights_unique=sorted(set(map(float, probe.snapshot_weightings.objective))), full_snapshots=len(full.snapshots),
           s4m2_input_network=rec.get("input_network"))
full.set_snapshots(full.snapshots[:56])
res["snapshots_equal_first56"] = bool((probe.snapshots == full.snapshots).all())
# time series and static tables equal?
diff = []
for c in sorted(probe.all_components):
    if c in ("SubNetwork",):
        continue
    sp, sf = probe.df(c), full.df(c)
    if not sp.index.equals(sf.index):
        diff.append(f"{c}:static_index"); continue
    num = [k for k in sp.columns if k in sf.columns and sp[k].dtype.kind in "fi" and sf[k].dtype.kind in "fi"]
    if num and not np.array_equal(sp[num].to_numpy(dtype=float), sf[num].to_numpy(dtype=float), equal_nan=True):
        diff.append(f"{c}:static_numeric")
    for attr, dp in probe.pnl(c).items():
        df = full.pnl(c).get(attr)
        if dp.empty and (df is None or df.empty):
            continue
        if df is None or not dp.shape == df.shape or not np.allclose(dp.to_numpy(dtype=float), df[dp.columns].to_numpy(dtype=float), equal_nan=True, rtol=0, atol=0):
            diff.append(f"{c}:{attr}")
res["dynamic_or_index_differences_vs_first56"] = diff
from s2_solve import set_representative_weights
set_representative_weights(full)
res["full_truncated_weights_unique"] = sorted(set(map(float, full.snapshot_weightings.objective)))
print(json.dumps(res, indent=1, default=str))
