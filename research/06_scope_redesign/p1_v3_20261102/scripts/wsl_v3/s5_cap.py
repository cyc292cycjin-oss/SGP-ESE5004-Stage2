"""Supplement 05, review section 2 item 2: capacity table before the solve, operating units only, in the format of report 04 section 2; line bound; what went back to the nodes. Read-only, no solve. Writes evidence/SOURCE_CAPACITY_OP_V3.csv, SOURCE_CAPACITY_OP_V3.json, SOURCE_LINE_BOUND_OP_V3.json."""
import json
import logging
from pathlib import Path

import pandas as pd
import pypsa

logging.disable(logging.WARNING)
pd.set_option("display.width", 240, "display.max_columns", 40, "display.max_rows", 200, "display.max_colwidth", 60)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3"); B = M / "builds_op"
E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence")
THERMAL = ("coal existing", "lignite existing"); bound = {}
for lab, f in (("2920x3h", "integrated/integrated_2920_3h_unsolved.nc"), ("365x24h", "integrated/integrated_365_24h_unsolved.nc")):
    n = pypsa.Network(str(B / f)); w = n.snapshot_weightings.generators; sn = n.snapshots; led = n.meta["research_dedicated_lines"]["sources"]; rows = []; ser = {}; con = {}
    for r in led:
        a, s = r["node"], r["bus"]
        g = n.generators[n.generators.bus == s]; u = n.storage_units[n.storage_units.bus == s]; k = n.links[n.links.bus1 == s]
        by = pd.concat([g.groupby("carrier").p_nom.sum(), u.groupby("carrier").p_nom.sum(), (k.p_nom * k.efficiency).groupby(k.carrier).sum()]).groupby(level=0).sum()
        total = float(by.sum()); thermal = float(by.reindex(THERMAL).fillna(0.0).sum()); clean = total - thermal; c = float(r["contract_mw"])
        ge = n.get_switchable_as_dense("Generator", "p_max_pu")[g.index].mul(g.p_nom).sum(axis=1)
        su = n.storage_units_t.inflow.reindex(columns=u.index).fillna(0.0).clip(upper=u.p_nom, axis=1).sum(axis=1)
        av = ge + su; ser[a] = av; con[a] = c
        d = dict(node=a, source_bus=s, contract_mw=c, moved_mw=total, mw_hydro=float(by.get("hydro existing", 0.0)), mw_ror=float(by.get("ror existing", 0.0)), mw_coal=float(by.get("coal existing", 0.0)), mw_lignite=float(by.get("lignite existing", 0.0)), non_thermal_mw=clean, ratio_moved=total / c, ratio_non_thermal=clean / c)
        if lab == "2920x3h":
            d.update(avail_dry_week_mw=float(av.iloc[:56].mean()), avail_jan_mw=float(av[sn.month == 1].mean()), avail_sep_mw=float(av[sn.month == 9].mean()), avail_year_mw=float(av.mean())); d.update(ratio_dry_week=d["avail_dry_week_mw"] / c, ratio_year=d["avail_year_mw"] / c)
        rows.append(d)
    a_ = pd.DataFrame(ser); c_ = pd.Series(con); b_ = a_.clip(upper=c_, axis=1)
    m = pd.DataFrame(dict(stock_mw=a_.sum(axis=1), line_bound_mw=b_.sum(axis=1))).groupby(a_.index.month).mean()
    bound[lab] = dict(stock_twh=float(a_.mul(w, axis=0).sum().sum()) / 1e6, line_bound_twh=float(b_.mul(w, axis=0).sum().sum()) / 1e6, line_bound_share_of_contract=float(b_.mul(w, axis=0).sum().sum() / (c_.sum() * 8760)), by_node_twh={k: round(float(v) / 1e6, 2) for k, v in b_.mul(w, axis=0).sum().items()},
                      by_month=dict(stock_mw={int(k): round(float(v)) for k, v in m.stock_mw.items()}, line_bound_mw={int(k): round(float(v)) for k, v in m.line_bound_mw.items()}))
    if lab == "2920x3h":
        t = pd.DataFrame(rows)
print(t.round(2).T.to_string()); print(json.dumps(bound, indent=0)[:1900])
tot = {k: float(t[k].sum()) for k in ("contract_mw", "moved_mw", "mw_hydro", "mw_ror", "mw_coal", "mw_lignite", "non_thermal_mw", "avail_dry_week_mw", "avail_jan_mw", "avail_sep_mw", "avail_year_mw")}; print(tot)
res = dict(totals=tot, zero_non_thermal_nodes=list(t.node[t.non_thermal_mw <= 0]), non_thermal_below_contract=list(t.node[t.non_thermal_mw < t.contract_mw]), dry_week_below_contract=list(t.node[t.avail_dry_week_mw < t.contract_mw]), annual_mean_below_contract=list(t.node[t.avail_year_mw < t.contract_mw]), september_below_contract=list(t.node[t.avail_sep_mw < t.contract_mw]))
print(res)
t.to_csv(E / "SOURCE_CAPACITY_OP_V3.csv", index=False); (E / "SOURCE_CAPACITY_OP_V3.json").write_text(json.dumps(res, indent=1) + "\n"); (E / "SOURCE_LINE_BOUND_OP_V3.json").write_text(json.dumps(bound, indent=1) + "\n")
