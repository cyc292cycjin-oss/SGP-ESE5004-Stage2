"""Supplement 04: what the plant lines can carry at most after decision 179: min(stock availability of the node, contract of its lines), snapshot by snapshot, without the thermal units. Read-only, no solve. Reservoirs have about 7 h of storage, so the 365x24h daily means are the reference for the screening."""
import json
import logging
from pathlib import Path

import pandas as pd
import pypsa

logging.disable(logging.WARNING)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_bound")
E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence")
out = {}
for lab, f in (("2920x3h", "integrated/integrated_2920_3h_unsolved.nc"), ("365x24h", "integrated/integrated_365_24h_unsolved.nc")):
    n = pypsa.Network(str(M / f)); w = n.snapshot_weightings.generators; rows = {}; contract = {}
    for r in n.meta["research_dedicated_lines"]["sources"]:
        s = r["bus"]; g = n.generators[n.generators.bus == s]; u = n.storage_units[n.storage_units.bus == s]
        ge = n.get_switchable_as_dense("Generator", "p_max_pu")[g.index].mul(g.p_nom).sum(axis=1)
        su = n.storage_units_t.inflow.reindex(columns=u.index).fillna(0.0).clip(upper=u.p_nom, axis=1).sum(axis=1)
        rows[r["node"]] = (ge + su); contract[r["node"]] = r["contract_mw"]
    a = pd.DataFrame(rows); c = pd.Series(contract); b = a.clip(upper=c, axis=1)
    m = pd.DataFrame(dict(stock_mw=a.sum(axis=1), line_bound_mw=b.sum(axis=1))).groupby(a.index.month).mean()
    res = dict(stock_twh=float(a.mul(w, axis=0).sum().sum()) / 1e6, line_bound_twh=float(b.mul(w, axis=0).sum().sum()) / 1e6, line_bound_share_of_contract=float(b.mul(w, axis=0).sum().sum() / (c.sum() * 8760)), by_node_twh={k: round(float(v) / 1e6, 2) for k, v in b.mul(w, axis=0).sum().items()},
               by_month=dict(stock_mw={int(k): round(float(v)) for k, v in m.stock_mw.items()}, line_bound_mw={int(k): round(float(v)) for k, v in m.line_bound_mw.items()}))
    out[lab] = res; print(lab, json.dumps(res, indent=0))
(E / "SOURCE_LINE_BOUND_V3.json").write_text(json.dumps(out, indent=1) + "\n")
