"""V4 D1 section 6: pumped hydro (PHS) as it stands in the model - StorageUnits of carrier PHS in a built network (existing stock, candidates), their
country, p_nom, extendability, max_hours, efficiencies, capital cost; the cost-table PHS rows; the S4B-2 candidate-cap rule. Read only; no solver.

    <env python> scripts/d1_phs_model.py <network.nc> <costs_active_research.csv> <repo> <out json>
"""
import json
import sys
from pathlib import Path

import pandas as pd
import pypsa

net, costs, repo, out = sys.argv[1:5]
n = pypsa.Network(net)
su = n.storage_units.copy()
su["country"] = su.bus.map(n.buses.country) if "country" in n.buses else ""
ph = su[su.carrier.astype(str).str.contains("PHS|pumped|hydro", case=False, regex=True)]
cols = [c for c in ["bus", "carrier", "country", "p_nom", "p_nom_extendable", "p_nom_max", "max_hours", "efficiency_store", "efficiency_dispatch", "capital_cost",
                    "marginal_cost", "cyclic_state_of_charge"] if c in ph.columns]
by = ph.groupby(["carrier", "country", "p_nom_extendable"]).agg(units=("p_nom", "size"), p_nom_MW=("p_nom", "sum"), p_nom_max_MW=("p_nom_max", "sum"),
                                                               max_hours_mean=("max_hours", "mean"), eff_store=("efficiency_store", "mean"),
                                                               eff_dispatch=("efficiency_dispatch", "mean"), capital_cost=("capital_cost", "mean")).reset_index()
c = pd.read_csv(costs, index_col=0) if costs.endswith(".csv") else None
crow = {}
if c is not None:
    z = c[c.index.astype(str).str.upper().str.contains("PHS")] if c.index.dtype == object else c
    crow = z.reset_index().to_dict("records")[:20]
meta_keys = {k: n.meta.get(k) for k in ("research_candidates_s4b2",) if k in n.meta}
res = dict(network=net, storage_units_phs=ph[cols].reset_index().to_dict("records"), by_country=by.to_dict("records"),
           totals=dict(existing_MW=float(ph[~ph.p_nom_extendable.astype(bool)].p_nom.sum()), extendable_units=int(ph.p_nom_extendable.astype(bool).sum()),
                       extendable_p_nom_max_MW=float(ph[ph.p_nom_extendable.astype(bool)].p_nom_max.replace(float("inf"), float("nan")).sum())),
           cost_rows=crow, candidate_meta=json.loads(json.dumps(meta_keys, default=str)))
Path(out).write_text(json.dumps(res, indent=1, default=float))
print(by.round(3).to_string(index=False)); print(res["totals"])
print(pd.DataFrame(crow).head(12).to_string() if crow else "no PHS cost rows")
