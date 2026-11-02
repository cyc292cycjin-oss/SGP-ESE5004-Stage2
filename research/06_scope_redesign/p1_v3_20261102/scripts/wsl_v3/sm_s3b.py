"""Supplement 03: where the Lao export of the one-way smoke comes from: LA generation and capacity by carrier in no_new_xb, three cases; TH side. Read-only."""
import logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 200, "display.max_columns", 30)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
N = {k: pypsa.Network(M / d / "no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc") for k, d in (("none", "smoke_s1"), ("two_way", "smoke_s2"), ("one_way", "smoke_s3"))}


def tab(n, cc):
    w = n.snapshot_weightings.generators; c = n.buses.country.astype(str); g = n.generators[n.generators.bus.map(c) == cc]
    e = n.generators_t.p[g.index.intersection(n.generators_t.p.columns)].mul(w, axis=0).sum().groupby(g.carrier.astype(str)).sum() / 1e6; p = g.groupby(g.carrier.astype(str)).p_nom_opt.sum() / 1e3
    u = n.storage_units[n.storage_units.bus.map(c) == cc]; ue = n.storage_units_t.p_dispatch[u.index.intersection(n.storage_units_t.p_dispatch.columns)].mul(w, axis=0).sum().groupby(u.carrier.astype(str)).sum() / 1e6
    return e, p, ue


for cc in ("LA", "TH"):
    E = pd.DataFrame({k: tab(n, cc)[0] for k, n in N.items()}).fillna(0.0); P = pd.DataFrame({k: tab(n, cc)[1] for k, n in N.items()}).fillna(0.0); U = pd.DataFrame({k: tab(n, cc)[2] for k, n in N.items()}).fillna(0.0)
    print(cc, "TWh"); print(E[(E.max(axis=1) > 3) & E.index.str.contains("wind|solar|ror|LNG|gas|coal|geothermal")].round(1).to_string()); print(cc, "GW"); print(P[(P.max(axis=1) > 1) & P.index.str.contains("wind|solar|ror")].round(1).to_string()); print(U[U.max(axis=1) > 0.5].round(1).to_string())
for k, n in N.items():
    c = n.buses.country.astype(str); w = n.snapshot_weightings.generators; ld = n.loads[n.loads.bus.map(c) == "LA"]; print(k, "LA load TWh", round(float(n.get_switchable_as_dense("Load", "p_set")[ld.index].mul(w, axis=0).sum().sum()) / 1e6, 2))
    L = n.links[(n.links.bus0.map(c) == "LA") & (n.links.carrier.astype(str).isin(["H2 Electrolysis", "methanolisation", "Haber-Bosch", "BEV charger"]))]
    print("   LA conversion in TWh", (n.links_t.p0[L.index.intersection(n.links_t.p0.columns)].mul(w, axis=0).sum().groupby(L.carrier.astype(str)).sum() / 1e6).round(1).to_dict())
