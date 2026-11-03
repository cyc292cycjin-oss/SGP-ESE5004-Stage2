"""V3 screening: capacity duals of every ship / transit link (decision D161-10, V3_RULES.md section 3.3: listed in the screening report, any non-zero value
reported) for each solved run of the recovered full pack, with the smoke evaluation's own function (scripts_project/v3_smoke_eval.py ship_duals). Read-only.
    PYTHONHASHSEED=0 python v3s_ship_duals.py <repo> <full_unpacked/export dir> <out dir>"""
import json
import sys
from pathlib import Path

import pypsa

repo, ex, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(repo / "scripts_project"))
import v3_smoke_eval as ev  # noqa: E402

frames, res = [], {}
for rid in ("V1", "V2", "V4", "V5", "V3"):
    nc = sorted((ex / rid).glob("*_solved.nc"))
    if not nc:
        res[rid] = dict(solved_network=None); continue
    n = pypsa.Network(str(nc[0])); d = ev.ship_duals(n, rid); frames.append(d)
    nz = d[d.mu_upper_max_abs.fillna(0.0) > ev.DUAL_TOL]
    res[rid] = dict(solved_network=nc[0].name, links=int(len(d)), dual_available=bool(d.mu_available.all()), above_tolerance=int(len(nz)), tolerance_eur_per_mwh=ev.DUAL_TOL,
                    max_abs_dual=float(d.mu_upper_max_abs.max()) if len(d) else None, max_utilisation=float(d.max_utilisation.max()) if len(d) else None,
                    max_utilisation_link=str(d.loc[d.max_utilisation.idxmax(), "link"]) if len(d) and d.max_utilisation.notna().any() else None, flow_twh_by_carrier={str(k): float(v) for k, v in d.groupby("carrier").flow_twh.sum().items()})
    print(rid, json.dumps(res[rid]), flush=True)
if frames:
    import pandas as pd
    pd.concat(frames).sort_values(["scenario", "mu_upper_max_abs"], ascending=[True, False]).to_csv(out / "V3_SCREEN_SHIP_CAPACITY_DUALS.csv", index=False)
(out / "V3_SCREEN_SHIP_DUALS.json").write_text(json.dumps(res, indent=1) + "\n")
