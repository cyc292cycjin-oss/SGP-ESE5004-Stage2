"""Supplement 04, review section 2.3: capacity table before the solve. Per plant source bus: stock moved by carrier and status, what can run under the 2050 net-zero constraint, ratio to the contract capacity of its plant lines,
and the seasonal availability of the moved stock (the 56-snapshot week is the dry season). Thermal dispatch comes from the supplement 03 smoke (one-way, before decision 179): an indication, not a result of this network. Read-only, no solve."""
import json
import logging
import sys
from pathlib import Path

import pandas as pd
import pypsa

logging.disable(logging.WARNING)
pd.set_option("display.width", 240, "display.max_columns", 40, "display.max_rows", 200, "display.max_colwidth", 60)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
B = M / sys.argv[1]; E = Path(sys.argv[2]) if len(sys.argv) > 2 else None
n = pypsa.Network(str(B / "integrated/integrated_2920_3h_unsolved.nc"))
led = n.meta["research_dedicated_lines"]["sources"]
ident = pd.DataFrame(n.meta["existing_unit_components"]).T
hdr = ["node", "carrier", "class", "mw", "components"]
THERMAL = ("coal existing", "lignite existing")
sn = n.snapshots; dry = sn[:56]; sep = sn[sn.month == 9]; jan = sn[sn.month == 1]; rows = []; sea = []; status = []


def add_status(u):
    y = pd.to_numeric(u.commissioning_year, errors="coerce")
    st = u.gem_status.fillna("(tracker: no GIPT status)").astype(str) if "gem_status" in u else pd.Series("(none)", index=u.index)
    return u.assign(status=st, year=y)


for r in led:
    a, s = r["node"], r["bus"]
    g = n.generators[n.generators.bus == s]; u = n.storage_units[n.storage_units.bus == s]; k = n.links[n.links.bus1 == s]
    moved = pd.concat([g.assign(out=g.p_nom, typ="Generator")[["carrier", "out", "typ"]], u.assign(out=u.p_nom, typ="StorageUnit")[["carrier", "out", "typ"]], k.assign(out=k.p_nom * k.efficiency, typ="Link")[["carrier", "out", "typ"]]])
    by = moved.groupby("carrier").out.sum()
    thermal = float(by.reindex(THERMAL).fillna(0.0).sum()); total = float(by.sum()); clean = total - thermal; c = float(r["contract_mw"])
    avail = {}
    for lab, idx in (("dry_week", dry), ("jan", jan), ("sep", sep), ("year", sn)):
        ge = n.get_switchable_as_dense("Generator", "p_max_pu").loc[idx, g.index].mul(g.p_nom).sum(axis=1)
        inf = n.storage_units_t.inflow.reindex(columns=u.index).fillna(0.0).loc[idx]
        su = inf.clip(upper=u.p_nom, axis=1).sum(axis=1)
        avail[lab] = float((ge + su).mean())
    rows.append(dict(node=a, source_bus=s, contract_mw=c, moved_mw=total, **{f"mw_{x.replace(' existing', '')}": float(by.get(x, 0.0)) for x in ("hydro existing", "ror existing", "onwind existing", "coal existing", "lignite existing")},
                     non_thermal_mw=clean, ratio_moved=total / c, ratio_non_thermal=clean / c, avail_dry_week_mw=avail["dry_week"], avail_jan_mw=avail["jan"], avail_sep_mw=avail["sep"], avail_year_mw=avail["year"], ratio_dry_week=avail["dry_week"] / c, ratio_year=avail["year"] / c))
    z = add_status(ident[ident.node == a])
    z = z.assign(carrier=[n.df(t).at[c_, "carrier"] for t, c_ in zip(z.component_type, z.component)])
    for (cr, st, late), v in z.groupby(["carrier", "status", z.year.fillna(0) > 2025], sort=True):
        status.append(dict(node=a, carrier=cr, gem_status=st, commissioned_after_2025=bool(late), mw=float(pd.to_numeric(v.capacity_mw).sum()), units=int(len(v)), years=f"{int(v.year.min()) if v.year.notna().any() else 0}-{int(v.year.max()) if v.year.notna().any() else 0}"))
t = pd.DataFrame(rows); s = pd.DataFrame(status)
print(t.round(2).T.to_string())
print(s.to_string())
tot = {k: float(t[k].sum()) for k in ("contract_mw", "moved_mw", "mw_hydro", "mw_ror", "mw_onwind", "mw_coal", "mw_lignite", "non_thermal_mw", "avail_dry_week_mw", "avail_jan_mw", "avail_sep_mw", "avail_year_mw")}; print(tot)
print("zero stock nodes", list(t.node[t.moved_mw <= 0]), "| non-thermal below contract", list(t.node[t.non_thermal_mw < t.contract_mw]), "| dry week availability below contract", list(t.node[t.avail_dry_week_mw < t.contract_mw]), "| annual mean below contract", list(t.node[t.avail_year_mw < t.contract_mw]))
# dispatch of the thermal units in the supplement 03 smoke (one-way network, 56 snapshots)
for sc in ("integrated", "no_new_xb"):
    f = M / f"smoke_s3/{sc}/{sc}_SMOKE_TEST_ONLY_solved.nc"
    if f.exists():
        x = pypsa.Network(str(f)); w = x.snapshot_weightings.generators; L = x.links[x.links.carrier.isin(THERMAL) & x.links.index.str.contains("LA2")]
        p0 = x.links_t.p0.reindex(columns=L.index).fillna(0.0)
        print("smoke_s3", sc, {k: dict(p_out_mw=round(float(L.at[k, "p_nom"] * L.at[k, "efficiency"]), 1), mean_out_mw=round(float(p0[k].mean() * L.at[k, "efficiency"]), 3), max_out_mw=round(float(p0[k].max() * L.at[k, "efficiency"]), 3), annual_twh=round(float((p0[k] * L.at[k, "efficiency"]).mul(w).sum()) / 1e6, 4)) for k in L.index})
        c = x.buses.country.astype(str); ld = x.loads[x.loads.bus.map(c) == "LA"]; print("   LA load TWh (annualised)", round(float(x.get_switchable_as_dense("Load", "p_set")[ld.index].mul(w, axis=0).sum().sum()) / 1e6, 2), " all-LA annual co2 dual", x.global_constraints.filter(like="LA", axis=0).mu.to_dict() if len(x.global_constraints) else {})
la = n.buses[(n.buses.country == "LA") & (n.buses.carrier == "AC")].index
w = n.snapshot_weightings.generators; ld = n.loads[n.loads.bus.map(n.buses.country.astype(str)) == "LA"]; print("LA load TWh full year", round(float(n.get_switchable_as_dense("Load", "p_set")[ld.index].mul(w, axis=0).sum().sum()) / 1e6, 2))
print("LA2 0 stock MW", n.generators[(n.generators.bus == "LA2 0") & ~n.generators.p_nom_extendable].p_nom.sum(), n.storage_units[(n.storage_units.bus == "LA2 0") & ~n.storage_units.p_nom_extendable].p_nom.sum(), "AC buses", list(la))
if E:
    t.to_csv(E / "SOURCE_CAPACITY_V3.csv", index=False); s.to_csv(E / "SOURCE_CAPACITY_STATUS_V3.csv", index=False)
    (E / "SOURCE_CAPACITY_V3.json").write_text(json.dumps(dict(totals=tot, zero_stock_nodes=list(t.node[t.moved_mw <= 0]), non_thermal_below_contract=list(t.node[t.non_thermal_mw < t.contract_mw]), dry_week_below_contract=list(t.node[t.avail_dry_week_mw < t.contract_mw]), annual_mean_below_contract=list(t.node[t.avail_year_mw < t.contract_mw])), indent=1) + "\n")
