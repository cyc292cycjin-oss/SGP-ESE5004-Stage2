"""Supplement 05, basis of the predictions (read-only, existing smoke of supplement 04): plant-line flow per snapshot by node, mean and peak, against the operating stock availability of the same snapshots; what the operating-only rule would cut if flows stayed."""
import logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 220, "display.max_columns", 30)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
op = pypsa.Network(str(M / "builds_op/integrated/integrated_2920_3h_unsolved.nc")); sn = op.snapshots[:56]; av = {}
for r in op.meta["research_dedicated_lines"]["sources"]:
    s = r["bus"]; g = op.generators[op.generators.bus == s]; u = op.storage_units[op.storage_units.bus == s]
    av[r["node"]] = op.get_switchable_as_dense("Generator", "p_max_pu").loc[sn, g.index].mul(g.p_nom).sum(axis=1) + op.storage_units_t.inflow.reindex(columns=u.index).fillna(0.0).loc[sn].clip(upper=u.p_nom, axis=1).sum(axis=1)
av = pd.DataFrame(av)
for sc in ("integrated", "no_new_xb"):
    n = pypsa.Network(str(M / f"smoke_s4/{sc}/{sc}_SMOKE_TEST_ONLY_solved.nc")); w = n.snapshot_weightings.generators; K = n.links[n.links.carrier == "dedicated plant line"]
    f = n.links_t.p0[K.index].T.groupby(K.bus0.str.replace(" dedicated src", "", regex=False)).sum().T
    cut = (f - av[f.columns].to_numpy()).clip(lower=0.0)
    t = pd.DataFrame(dict(line_mean_mw=f.mean(), line_peak_mw=f.max(), op_avail_mean_mw=av[f.columns].mean(), op_avail_peak_mw=av[f.columns].max(), snapshots_above=(cut > 1e-3).sum(), energy_above_twh=cut.mul(w, axis=0).sum() / 1e6, line_twh=f.mul(w, axis=0).sum() / 1e6))
    print(sc); print(t.round(2).to_string()); print("lines TWh", round(float(t.line_twh.sum()), 2), "above the operating availability TWh", round(float(t.energy_above_twh.sum()), 2))
