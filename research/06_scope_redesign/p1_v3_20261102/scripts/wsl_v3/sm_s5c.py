"""Supplement 04: on the solved smoke networks: at every snapshot the stock output on a source bus equals what leaves it (no new wind or solar on a plant line); the existing wind unit; B1 of the integrated run. Writes evidence/SOURCE_BALANCE_OP_SMOKE.json. Read-only."""
import json, logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3"); E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence"); out = {}
for sc in ("integrated", "no_new_xb"):
    n = pypsa.Network(str(M / f"smoke_s5/{sc}/{sc}_SMOKE_TEST_ONLY_solved.nc")); w = n.snapshot_weightings.generators; res = {}
    S = n.buses.index[n.buses["role"].astype(str) == "dedicated_plant_source"]
    for s in S:
        g = n.generators.index[n.generators.bus == s]; u = n.storage_units.index[n.storage_units.bus == s]; ki = n.links.index[n.links.bus1 == s]; ko = n.links.index[n.links.bus0 == s]
        inn = n.generators_t.p.reindex(columns=g).fillna(0.0).sum(axis=1) + n.storage_units_t.p.reindex(columns=u).fillna(0.0).sum(axis=1) - n.links_t.p1.reindex(columns=ki).fillna(0.0).sum(axis=1)
        out_ = n.links_t.p0.reindex(columns=ko).fillna(0.0).sum(axis=1); plant = n.links_t.p0.reindex(columns=[k for k in ko if n.links.at[k, "carrier"] == "dedicated plant line"]).fillna(0.0).sum(axis=1)
        res[s] = dict(stock_twh=round(float(inn.mul(w).sum()) / 1e6, 3), plant_lines_twh=round(float(plant.mul(w).sum()) / 1e6, 3), max_abs_residual_mw=float((inn - out_).abs().max()), plant_above_stock_max_mw=float((plant - inn).max()), new_units_on_bus=int(n.generators.p_nom_extendable[g].sum() + n.storage_units.p_nom_extendable[u].sum()))
    out[sc] = res; print(sc, json.dumps(res)[:900])
    if sc == "no_new_xb":
        k = "existing_survivor::LA2 1::onwind existing::S4B1"; pm = n.get_switchable_as_dense("Generator", "p_max_pu")[k]; print("wind stock", n.generators.at[k, "bus"], n.generators.at[k, "p_nom"], "mean p_max_pu", round(float(pm.mean()), 3), "p mean", round(float(n.generators_t.p[k].mean()), 3), "mc", n.generators.at[k, "marginal_cost"])
b = json.loads((M / "smoke_s5/integrated/V5_GATES.json").read_text())["B1"]; print("B1 keys", list(b)[:8], {k: b[k] for k in list(b) if k in ("passed", "tolerance", "tolerance_t", "worst", "max_excess", "max_excess_t")}, str(b)[:600])
(E / "SOURCE_BALANCE_OP_SMOKE.json").write_text(json.dumps(out, indent=1) + "\n")
