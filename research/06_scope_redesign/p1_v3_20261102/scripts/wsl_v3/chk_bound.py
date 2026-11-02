"""Supplement 04: the bound networks against the one-way networks of supplement 03, component by component, every attribute and series: only decision 179 may differ. Read-only."""
import json, logging, sys
from pathlib import Path
import numpy as np, pandas as pd, pypsa
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
from v3_static import ATTR
logging.disable(logging.WARNING)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3"); E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence")
rows, out = [], {}
for lab, f in (("integrated_2920", "integrated/integrated_2920_3h_unsolved.nc"), ("no_new_xb_2920", "no_new_xb/no_new_xb_2920_3h_unsolved.nc"), ("integrated_365", "integrated/integrated_365_24h_unsolved.nc"), ("no_new_xb_365", "no_new_xb/no_new_xb_365_24h_unsolved.nc")):
    a, b = pypsa.Network(str(M / "builds_oneway" / f)), pypsa.Network(str(M / "builds_bound" / f)); bad = []
    for typ in ATTR:
        x, y = a.df(typ), b.df(typ); both = x.index.intersection(y.index)
        gone, new = list(x.index.difference(y.index)), list(y.index.difference(x.index))
        if gone:
            bad.append(f"{typ} removed {gone[:3]}")
        for k, v in y.loc[new].carrier.astype(str).value_counts().items():
            rows.append(dict(network=lab, type=typ, change="added", carrier=k, count=int(v), example=str(y.loc[new][y.loc[new].carrier == k].index[0])))
        for col in x.columns.intersection(y.columns):
            p, q = x.loc[both, col], y.loc[both, col]
            if p.dtype == object or q.dtype == object:
                ne = p.astype(str).to_numpy() != q.astype(str).to_numpy()
            else:
                ne = ~np.isclose(p.astype(float), q.astype(float), rtol=0.0, atol=0.0, equal_nan=True)
            if ne.any():
                ch = both[ne]; rows.append(dict(network=lab, type=typ, change=f"attr:{col}", carrier=";".join(sorted(set(y.loc[ch].carrier.astype(str)))), count=int(ne.sum()), example=str(ch[0])))
                ok = (typ, col) in (("Generator", "bus"), ("StorageUnit", "bus"), ("Link", "bus1"), ("Link", "bus0"))
                if not ok or not y.loc[ch, col].astype(str).str.endswith(" dedicated src").all() or not x.loc[ch, col].astype(str).str.startswith("LA2 ").all():
                    bad.append(f"{typ}.{col} changed: {list(ch[:3])}")
                if col == "bus0" and set(y.loc[ch].carrier.astype(str)) != {"dedicated plant line"}:
                    bad.append("bus0 changed on another carrier")
        for attr, fa in a.pnl(typ).items():
            fb = b.pnl(typ).get(attr)
            if fb is None:
                bad.append(f"{typ} series {attr} lost"); continue
            cm = fa.columns.intersection(fb.columns)
            if len(fa.columns.difference(fb.columns)) or len(fb.columns.difference(fa.columns)) or (len(cm) and not np.array_equal(fa[cm].to_numpy(), fb[cm].to_numpy(), equal_nan=True)):
                bad.append(f"{typ} series {attr} differs")
    out[lab] = dict(passed=not bad, problems=bad[:12], snapshots=int(len(b.snapshots)), objective_constant_same=bool(a.meta.get("existing_cross_border_fom_eur") == b.meta.get("existing_cross_border_fom_eur")), source_links=int((b.links.carrier == "dedicated plant source").sum()))
pd.DataFrame(rows).to_csv(E / "BOUND_VS_ONEWAY_DIFF.csv", index=False); (E / "BOUND_VS_ONEWAY_DIFF.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=0)); print(pd.DataFrame(rows)[lambda d: d.network == "integrated_2920"].to_string())
