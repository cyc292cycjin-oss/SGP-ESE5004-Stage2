"""S4F report section (record only, no model change): the cross-border AC lines whose s_nom the author's readjust_existing_interconnections changed
(research/00_source_provenance/official/author_run/scripts/final_asean_adjustment.py lines 296-347; configs/config.asean.yaml line 208).

The author selection is reproduced on the frozen electric base: lines with country0 != country1, country0 in the first and country1 in the second
column of AIMS_exist_data, build_year <= 2024; then per (country0, country1) pair (orientation as in the author's code) s_nom = AIMS total x
length share, s_nom_min = s_nom. Per line: s_nom, sqrt3 x v_nom x i_nom x num_parallel (PyPSA line-type rating, v_nom of bus0, i_nom of the line
type) and their ratio, x, r, length; AC loop: the line lies on a cycle of the AC line graph (not a bridge; parallel lines between the same buses
count), parallel AC lines of the same country pair, and an AC path between its two buses that avoids every AC line of its country pair (i.e.
through a third country).

    python scripts_project/s4f_2_readjust_audit.py --out research_inputs/corridors/AUTHOR_READJUST_LINES_S4F2.csv
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from pathlib import Path

import networkx as nx
import pandas as pd

from d1_common import ROOT, sha256

AUTHOR_SCRIPT = Path("/mnt/d/ResearchWorkspaces/ASEAN/research/00_source_provenance/official/author_run/scripts/final_asean_adjustment.py")
AIMS_EXIST = [("ID", "MY", 230), ("KH", "LA", 300), ("KH", "TH", 250), ("KH", "VN", 200), ("MY", "SG", 525), ("MY", "TH", 380), ("LA", "TH", 955), ("LA", "MM", 30),
              ("LA", "VN", 1)]   # final_asean_adjustment.py lines 303-313


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--base", type=Path, default=ROOT / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc"); a = ap.parse_args()
    if AUTHOR_SCRIPT.exists():
        txt = AUTHOR_SCRIPT.read_text()
        for c0, c1, v in AIMS_EXIST:
            if f'("{c0}", "{c1}", {v})' not in txt:
                raise ValueError(f"author AIMS_exist_data changed: {c0}-{c1} {v}")
    n = pypsa.Network(str(a.base)); L = n.lines.copy(); bc = n.buses.country
    L["country0"] = L.bus0.map(bc); L["country1"] = L.bus1.map(bc)
    ex = pd.DataFrame(AIMS_EXIST, columns=["country0", "country1", "s_nom_aims"])
    aims = {(c0, c1): v for c0, c1, v in AIMS_EXIST}
    sel = L[(L.country0 != L.country1) & L.country0.isin(ex.country0) & L.country1.isin(ex.country1) & (L.build_year <= 2024)]
    sel = sel[[(c0, c1) in aims for c0, c1 in zip(sel.country0, sel.country1)]].copy()   # author loop: orientation-specific pairs
    sel["s_nom_aims"] = [aims[(c0, c1)] for c0, c1 in zip(sel.country0, sel.country1)]
    # AC line graph of the frozen base (all AC lines)
    G = nx.MultiGraph(); G.add_edges_from((z.bus0, z.bus1, dict(name=k)) for k, z in L.iterrows())
    S = nx.Graph(G); bridges = {frozenset(e) for e in nx.bridges(S)}
    pair_of = {k: frozenset((z.country0, z.country1)) for k, z in L.iterrows()}
    xb_all = L[L.country0 != L.country1]
    rows = []
    for k, z in sel.iterrows():
        t = str(z.type); i_nom = float(n.line_types.at[t, "i_nom"]) if t in n.line_types.index else float("nan"); v_nom = float(n.buses.at[z.bus0, "v_nom"])
        rating = math.sqrt(3) * v_nom * i_nom * float(z.num_parallel)
        parallel_same_buses = G.number_of_edges(z.bus0, z.bus1) > 1
        in_loop = parallel_same_buses or frozenset((z.bus0, z.bus1)) not in bridges
        same_pair = [x for x in xb_all.index if x != k and pair_of[x] == pair_of[k]]
        H = nx.MultiGraph([(u, v) for u, v, d in G.edges(data=True) if pair_of[d["name"]] != pair_of[k]])
        third = H.has_node(z.bus0) and H.has_node(z.bus1) and nx.has_path(H, z.bus0, z.bus1)
        rows.append(dict(country_pair=f"{z.country0}-{z.country1}", line=k, bus0=z.bus0, bus1=z.bus1, aims_total_mw=float(z.s_nom_aims), s_nom_mw=float(z.s_nom),
                         s_nom_min_mw=float(z.s_nom_min), v_nom_kv=v_nom, line_type=t, i_nom_ka=i_nom, num_parallel=float(z.num_parallel), type_rating_mw=rating,
                         ratio_s_nom_to_rating=(float(z.s_nom) / rating if rating else float("nan")), x_ohm=float(z.x), r_ohm=float(z.r), length_km=float(z.length),
                         in_ac_loop=bool(in_loop), parallel_ac_same_buses=bool(parallel_same_buses), other_ac_lines_same_country_pair=";".join(map(str, same_pair)),
                         ac_path_via_third_country=bool(third), s4f_change=("set to 80 MW (decision 97 a)" if k == "91" else "")))
    out = pd.DataFrame(rows).sort_values(["country_pair", "line"])
    chk = out.groupby("country_pair").agg(s_nom=("s_nom_mw", "sum"), aims=("aims_total_mw", "first"))
    out.to_csv(a.out, index=False)
    summ = dict(base=str(a.base), base_sha256=sha256(a.base), author_script=str(AUTHOR_SCRIPT), author_script_sha256=(sha256(AUTHOR_SCRIPT) if AUTHOR_SCRIPT.exists() else None),
                lines=len(out), pair_sums={k: dict(s_nom=float(v.s_nom), aims=float(v.aims)) for k, v in chk.iterrows()},
                in_ac_loop=int(out.in_ac_loop.sum()), via_third_country=int(out.ac_path_via_third_country.sum()),
                ratio_range=[float(out.ratio_s_nom_to_rating.min()), float(out.ratio_s_nom_to_rating.max())])
    a.out.with_suffix(".json").write_text(json.dumps(summ, indent=1))
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(out[["country_pair", "line", "s_nom_mw", "type_rating_mw", "ratio_s_nom_to_rating", "x_ohm", "num_parallel", "in_ac_loop", "other_ac_lines_same_country_pair",
               "ac_path_via_third_country"]].round(4).to_string())
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
