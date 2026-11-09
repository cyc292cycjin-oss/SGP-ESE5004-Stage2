"""V4 W20: KVL loops of the coalition networks (as M12b scripts/m12b_loops.py: cycle rank E - V + C of the passive-branch graph = AC lines; it equals
the number of KVL rows per snapshot of the LP). For a coalition S: loops of the base, loops of the S network, loops internal to the non-members
(the base restricted to non-member buses), loops 'through the boundary' = base - S network - non-member internal. No solver.

    python w20_loops.py --base56 <w14_integrated_56.nc> --nets <results_project/v4w20/nets56> --out <evidence/W20_KVL_LOOPS.json>
"""
import argparse
import json
import sys
from pathlib import Path


def cycle_rank(buses, edges) -> int:
    parent = {b: b for b in buses}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    comps = len(parent)
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb; comps -= 1
    return len(edges) - len(parent) + comps


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--base56", type=Path, required=True); ap.add_argument("--nets", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, "/home/jin/wt_v4_w20/scripts_project")
    import logging
    import pypsa
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    from v4_coalition import COALITION_ORDER, COUNTRIES, coalitions
    n0 = pypsa.Network(str(a.base56)); bc = n0.buses.country.astype(str)
    E0 = [(str(z.bus0), str(z.bus1)) for _, z in n0.lines.iterrows()]
    V0 = sorted({b for e in E0 for b in e})
    base = cycle_rank(V0, E0)
    xb_lines = sum(1 for u, v in E0 if bc[u] != bc[v])
    out = dict(script="work/p1_v4_w20_20261109/scripts/w20_loops.py", base_loops=base, base_lines=len(E0), base_cross_border_lines=xb_lines, coalitions={})
    for name in COALITION_ORDER:
        S = set(coalitions()[name]); NS = set(COUNTRIES) - S
        n = pypsa.Network(str(a.nets / f"{name}_56_unsolved.nc"))
        E = [(str(z.bus0), str(z.bus1)) for _, z in n.lines.iterrows()]; V = sorted({b for e in E for b in e})
        loops = cycle_rank(V, E)
        En = [(u, v) for u, v in E0 if bc[u] in NS and bc[v] in NS]; Vn = sorted({b for e in En for b in e})
        inner_ns = cycle_rank(Vn, En) if En else 0
        out["coalitions"][name] = dict(loops=loops, loops_removed=base - loops, loops_internal_non_members=inner_ns, loops_through_boundary=base - loops - inner_ns,
                                       lines=len(E), cross_border_lines_kept=sum(1 for u, v in E if bc[u] != bc[v]))
        print(name, out["coalitions"][name], flush=True)
    a.out.write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
