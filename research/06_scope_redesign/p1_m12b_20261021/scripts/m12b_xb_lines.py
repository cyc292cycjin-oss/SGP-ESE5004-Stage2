"""M12b section 4 (assessment only, no solve): cross-border AC lines (pypsa Line / Transformer between buses of two countries, part of the KVL
loops) and cross-border links (controllable, transport model) of the built network, by country pair.

    python m12b_xb_lines.py --network <integrated_2920_3h_unsolved.nc> --out <json>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd


def survey(path: Path) -> dict:
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(path))
    cty = n.buses.country.astype(str)
    out = {}
    for t in ("Line", "Transformer", "Link"):
        d = n.df(t)
        if not len(d):
            continue
        d = d.assign(c0=d.bus0.map(cty), c1=d.bus1.map(cty))
        x = d[d.c0 != d.c1].copy()
        if t == "Link":
            x = x.assign(car=x.carrier.astype(str))
        nom = "p_nom" if t == "Link" else "s_nom"
        x["pair"] = [("|".join(sorted((a, b)))) for a, b in zip(x.c0, x.c1)]
        rows = []
        for (pr, car), q in x.groupby(["pair", x.get("car", pd.Series("AC", index=x.index)) if t == "Link" else x.carrier.astype(str)]):
            rows.append(dict(pair=pr, carrier=car, count=int(len(q)), nom_mw=float(q[nom].sum()), nom_max_mw=float(q[nom + "_max"].replace(float("inf"), float("nan")).sum()),
                             extendable=int(q[nom + "_extendable"].sum()), length_km=float(q.length.sum()) if "length" in q else None))
        tot = dict(count=int(len(x)), nom_mw=float(x[nom].sum()), extendable=int(x[nom + "_extendable"].sum()),
                   nom_max_finite_mw=float(x[nom + "_max"][x[nom + "_max"] < float("inf")].sum()), nom_max_infinite=int((x[nom + "_max"] == float("inf")).sum()))
        if t == "Link":
            tot["by_carrier"] = {k: int(v) for k, v in x.carrier.astype(str).value_counts().items()}
        out[t] = dict(total=tot, by_pair=rows,
                      names=sorted(map(str, x.index))[:200])
    if len(n.lines):
        L = n.lines.assign(c0=n.lines.bus0.map(cty), c1=n.lines.bus1.map(cty))
        out["lines_all"] = dict(count=int(len(L)), cross_border=int((L.c0 != L.c1).sum()), domestic=int((L.c0 == L.c1).sum()),
                                carriers={k: int(v) for k, v in L.carrier.astype(str).value_counts().items()},
                                attrs_cross_border={k: sorted(map(str, L.loc[L.c0 != L.c1, k].astype(str).unique()))[:10] for k in ("type", "carrier") if k in L})
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    r = survey(a.network)
    a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(json.dumps(r, indent=1, default=str))
    print(json.dumps({k: v.get("total", v) for k, v in r.items()}, default=str))


if __name__ == "__main__":
    main()
