"""M12b section 3: KVL loop counts of the full network and the leave-one-out variants (network topology only; no LP, no solve).

Number of independent KVL loops per snapshot = cycle-space dimension of the passive-branch graph (lines + transformers, parallel branches
included): E - V + C. For a removed country i (basis independent):
    loops(N) - loops(N - i) = domestic loops of i (cycle space of the subgraph on i's lines) + loops through i's border,
    so loops through i's border = loops(N) - loops(N - i) - domestic loops of i (the KVL loops that join i's lines with other owners' lines;
    these are the rows the physical coalition N - i loses while the matrix game keeps them). loops(N - i) is counted on the variant network
    and checked against the full network without i's buses (variant_equals_rest_of_full).
The LP's own count (Kirchhoff-Voltage-Law rows / snapshots of the M12 audit) is compared in m12b_analysis.py.

    python m12b_loops.py --full <integrated_2920_3h_unsolved.nc> --variants <dir with integrated_minus<CC>_2920_3h_unsolved.nc> --out <json>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import networkx as nx
import pandas as pd

COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")


def branches(n) -> pd.DataFrame:
    parts = [n.lines[["bus0", "bus1"]].assign(component="Line")]
    if len(n.transformers):
        parts.append(n.transformers[["bus0", "bus1"]].assign(component="Transformer"))
    return pd.concat(parts)


def cycle_dim(br: pd.DataFrame) -> tuple[int, int, int, int]:
    """E - V + C of the multigraph spanned by the branches (isolated buses do not count): (loops, E, V, C)."""
    G = nx.MultiGraph()
    G.add_edges_from(zip(br.bus0, br.bus1))
    e, v, c = G.number_of_edges(), G.number_of_nodes(), nx.number_connected_components(G)
    return e - v + c, e, v, c


def loops(full: Path, variants: Path) -> dict:
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(full))
    country = n.buses.country.astype(str)
    B = branches(n)
    B = B.assign(c0=B.bus0.map(country), c1=B.bus1.map(country))
    tot, E, V, C = cycle_dim(B)
    res = dict(full=dict(network=str(full), loops=tot, branches=E, buses=V, components=C,
                         cross_border_branches=int((B.c0 != B.c1).sum()), domestic_loops={c: cycle_dim(B[(B.c0 == c) & (B.c1 == c)])[0] for c in COUNTRIES}),
               countries={})
    for c in COUNTRIES:
        f = variants / f"integrated_minus{c}_2920_3h_unsolved.nc"
        if not f.exists():
            res["countries"][c] = dict(missing=str(f)); continue
        m = pypsa.Network(str(f))
        Bv = branches(m)
        lv, Ev, Vv, Cv = cycle_dim(Bv)
        dom = cycle_dim(B[(B.c0 == c) & (B.c1 == c)])[0]
        x = B[(B.c0 == c) ^ (B.c1 == c)]
        lr, Er = cycle_dim(B[(B.c0 != c) & (B.c1 != c)])[:2]
        through = tot - lv - dom
        xs = []
        for name, r in x.iterrows():
            row = n.lines.loc[name] if r.component == "Line" else n.transformers.loc[name]
            xs.append(dict(component=r.component, name=str(name), countries=f"{r.c0}-{r.c1}", s_nom=float(row.get("s_nom", 0.0)),
                           s_nom_max=float(row.get("s_nom_max", float("nan"))), s_nom_extendable=bool(row.get("s_nom_extendable", False)),
                           length_km=float(row.get("length", float("nan")))))
        res["countries"][c] = dict(variant=str(f), loops_variant=lv, loops_removed=tot - lv, domestic_loops=dom, loops_through_border=through,
                                   loops_rest_of_full=lr, variant_equals_rest_of_full=bool(lv == lr and Ev == Er),
                                   crossing_branches=len(xs), crossing=xs, neighbours=sorted({s for b in xs for s in b["countries"].split("-")} - {c}))
        del m
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", type=Path, required=True); ap.add_argument("--variants", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    r = loops(a.full, a.variants)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(r, indent=1))
    print(json.dumps(dict(full=r["full"]["loops"], **{c: (v.get("loops_variant"), v.get("loops_through_border")) for c, v in r["countries"].items()})))


if __name__ == "__main__":
    main()
