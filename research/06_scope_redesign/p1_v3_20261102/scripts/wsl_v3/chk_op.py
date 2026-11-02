"""Supplement 05 review item 3: the operating-only networks against the networks of supplement 04, component by component, every attribute and series: only decision 180 may differ (construction units back on their node, source link p_nom, the two split components). Read-only."""
import json, logging, sys
from pathlib import Path
import numpy as np, pandas as pd, pypsa
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
from v3_static import ATTR
logging.disable(logging.WARNING)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3"); E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence")
SFX = " operating"; SPLIT = {"Generator": "existing_survivor::LA2 5::ror existing::S4A", "StorageUnit": "existing_survivor::LA2 1::hydro existing::S4A"}
rows, out = [], {}
for lab, f in (("integrated_2920", "integrated/integrated_2920_3h_unsolved.nc"), ("no_new_xb_2920", "no_new_xb/no_new_xb_2920_3h_unsolved.nc"), ("integrated_365", "integrated/integrated_365_24h_unsolved.nc"), ("no_new_xb_365", "no_new_xb/no_new_xb_365_24h_unsolved.nc")):
    a, b = pypsa.Network(str(M / "builds_bound" / f)), pypsa.Network(str(M / "builds_op" / f)); bad = []
    for typ in ATTR:
        x, y = a.df(typ), b.df(typ); both = x.index.intersection(y.index)
        gone, new = list(x.index.difference(y.index)), list(y.index.difference(x.index))
        if gone:
            bad.append(f"{typ} removed {gone[:3]}")
        for k in new:
            rows.append(dict(network=lab, type=typ, change="added", carrier=str(y.at[k, "carrier"]), count=1, example=str(k)))
            if not (typ in SPLIT and k == SPLIT[typ] + SFX):
                bad.append(f"{typ} added {k}")
        for col in x.columns.intersection(y.columns):
            p, q = x.loc[both, col], y.loc[both, col]
            ne = (p.astype(str).to_numpy() != q.astype(str).to_numpy()) if (p.dtype == object or q.dtype == object) else ~np.isclose(p.astype(float), q.astype(float), rtol=0.0, atol=0.0, equal_nan=True)
            if ne.any():
                ch = both[ne]; rows.append(dict(network=lab, type=typ, change=f"attr:{col}", carrier=";".join(sorted(set(y.loc[ch].carrier.astype(str)))), count=int(ne.sum()), example=str(ch[0])))
                if typ in ("Generator", "StorageUnit", "Link") and col in ("bus", "bus1"):   # back on the node: from the source bus to the node of the same name
                    if not (x.loc[ch, col].astype(str).str.replace(" dedicated src$", "", regex=True) == y.loc[ch, col].astype(str)).all() or not x.loc[ch, col].astype(str).str.endswith(" dedicated src").all():
                        bad.append(f"{typ}.{col} changed otherwise: {list(ch[:3])}")
                elif typ == "Link" and col in ("p_nom", "p_nom_min", "p_nom_max"):
                    if set(y.loc[ch].carrier.astype(str)) != {"dedicated plant source"}:
                        bad.append(f"Link.{col} changed on another carrier: {list(ch[:3])}")
                elif typ in SPLIT and col in ("p_nom", "existing_annual_fixed_om_eur"):
                    if list(ch) != [SPLIT[typ]]:
                        bad.append(f"{typ}.{col} changed beyond the split: {list(ch[:3])}")
                else:
                    bad.append(f"{typ}.{col} changed: {list(ch[:3])}")
        for typ2, k in SPLIT.items():
            if typ == typ2:
                for col in ("p_nom", "existing_annual_fixed_om_eur"):
                    if not np.isclose(float(y.at[k, col]) + float(y.at[k + SFX, col]), float(x.at[k, col]), rtol=1e-12):
                        bad.append(f"split {k} {col} does not add up")
        for attr, fa in a.pnl(typ).items():
            fb = b.pnl(typ).get(attr)
            if fb is None:
                bad.append(f"{typ} series {attr} lost"); continue
            extra = [c for c in fb.columns.difference(fa.columns)]; part = SPLIT.get(typ)
            if len(fa.columns.difference(fb.columns)) or any(c != (part or "") + SFX for c in extra):
                bad.append(f"{typ} series {attr} columns differ")
            cm = list(fa.columns.intersection(fb.columns)); same = [c for c in cm if not (attr == "inflow" and c == part)]
            if same and not np.array_equal(fa[same].to_numpy(), fb[same].to_numpy(), equal_nan=True):
                bad.append(f"{typ} series {attr} differs")
            if attr == "inflow" and part in cm and not np.allclose(fb[part] + fb[part + SFX], fa[part], rtol=1e-12, atol=1e-9):
                bad.append("split inflow does not add up")
            if attr == "p_max_pu" and part in cm and part + SFX in fb and not np.array_equal(fb[part].to_numpy(), fb[part + SFX].to_numpy()):
                bad.append("split p_max_pu differs")
    out[lab] = dict(passed=not bad, problems=bad[:12], snapshots=int(len(b.snapshots)), objective_constants_same=bool(a.meta.get("existing_cross_border_fom_eur") == b.meta.get("existing_cross_border_fom_eur") and a.meta.get("existing_annual_fixed_om_eur") == b.meta.get("existing_annual_fixed_om_eur")), identities=int(len(b.meta["existing_unit_components"])), same_identity_set=bool(set(a.meta["existing_unit_components"]) == set(b.meta["existing_unit_components"])))
pd.DataFrame(rows).to_csv(E / "OP_VS_BOUND_DIFF.csv", index=False); (E / "OP_VS_BOUND_DIFF.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=0)); print(pd.DataFrame(rows)[lambda d: d.network == "integrated_2920"].to_string())
