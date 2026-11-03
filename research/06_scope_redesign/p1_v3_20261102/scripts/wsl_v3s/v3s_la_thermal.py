"""V3 screening (read-only): annual output of the stock thermal Links on the Lao plant source buses (Hongsa lignite on LA2 5, the LA2 4 coal unit) and the
total output of everything on each source bus, from the solved networks of the recovered full pack (review SUPP05: the LA2 5 note in the screening report).
    python v3s_la_thermal.py <full_unpacked/export dir> <out json> [runs, default V1,V2,V4,V5]"""
import json
import sys
from pathlib import Path

import pypsa

ex, outp = Path(sys.argv[1]), Path(sys.argv[2]); runs = (sys.argv[3] if len(sys.argv) > 3 else "V1,V2,V4,V5").split(","); res = {}
for rid in runs:
    nc = sorted((ex / rid).glob("*_solved.nc"))
    if not nc:
        continue
    n = pypsa.Network(str(nc[0])); w = n.snapshot_weightings.generators
    src = [b for b in n.buses.index if b.endswith(" dedicated src")]
    T = n.links[n.links.bus1.isin(src) & n.links.carrier.astype(str).str.contains("lignite|coal", case=False)]
    r = dict(thermal={k: dict(bus1=str(T.at[k, "bus1"]), carrier=str(T.at[k, "carrier"]), output_mw=float(T.at[k, "p_nom"] * T.at[k, "efficiency"]),
                              output_twh=float((-n.links_t.p1[k]).mul(w).sum()) / 1e6, max_output_mw=float((-n.links_t.p1[k]).max())) for k in T.index})
    gen = {b: float(n.generators_t.p[n.generators.index[n.generators.bus == b]].sum(axis=1).mul(w).sum()) / 1e6 for b in src}
    su = {b: float(n.storage_units_t.p[n.storage_units.index[n.storage_units.bus == b]].sum(axis=1).mul(w).sum()) / 1e6 for b in src}
    r["source_bus_twh"] = {b: dict(generators=gen[b], storage_units=su[b], thermal=sum(v["output_twh"] for v in r["thermal"].values() if v["bus1"] == b)) for b in src}
    res[rid] = r; print(rid, json.dumps(r, default=str)[:1800], flush=True)
outp.write_text(json.dumps(res, indent=1, default=str) + "\n")
