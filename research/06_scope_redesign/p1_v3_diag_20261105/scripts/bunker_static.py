"""V3 DIAG step 5 (no solve): the bunker account structure of each package network - hook present, account Store contract, ports (all emission
ports, none removal: s4c_layers.validate_bunker_account), meters, final buses and their other feeders, the international aviation loads.
A network with the hook and only emission ports has the same zero-slack row (final level of a sum of non-negative terms <= 0).

    python bunker_static.py <out.json> <network.nc> [<network.nc> ...]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/jin/wt_v3_diag/scripts_project")
import logging  # noqa: E402

import pypsa  # noqa: E402

logging.getLogger("pypsa").setLevel(logging.ERROR)
from s4c_layers import BUNKER_CO2_BUS, BUNKER_HOOK, validate_bunker_account  # noqa: E402


def one(path):
    n = pypsa.Network(path)
    acc = validate_bunker_account(n)
    ports = acc.get("ports", [])
    meters = [p["link"] for p in ports]
    finals = sorted({str(n.links.at[x, "bus1"]) for x in meters})
    pset = n.get_switchable_as_dense("Load", "p_set"); w = n.snapshot_weightings.generators
    loads = n.loads.index[n.loads.bus.isin(finals)]
    twins = {fb: [str(x) for x in n.links.index[(n.links.bus1 == fb) & ~n.links.index.isin(meters)]] for fb in finals}
    st = n.stores.loc[BUNKER_CO2_BUS] if BUNKER_CO2_BUS in n.stores.index else None
    return dict(network=path, snapshots=int(len(n.snapshots)), hook=BUNKER_HOOK in n.meta.get("required_constraint_hooks", []), mode=(n.meta.get("research_bunkers") or {}).get("mode"),
                account_present=bool(acc.get("present")), ports=len(ports), removal_ports=sum(p["coefficient_t_per_mwh"] < 0 for p in ports),
                coefficients=sorted({round(p["coefficient_t_per_mwh"], 6) for p in ports}), port_carriers=sorted({p["carrier"] for p in ports}),
                final_buses=len(finals), twins_per_final=sorted({len(v) for v in twins.values()}), aviation_loads=int(len(loads)),
                aviation_annual_mwh=float((pset[loads].mul(w, axis=0)).sum().sum()) if len(loads) else 0.0,
                store=None if st is None else {k: str(st[k]) for k in ("e_nom_extendable", "e_min_pu", "e_initial", "e_cyclic", "capital_cost")})


def main(out, nets):
    res = [one(p) for p in nets]
    Path(out).write_text(json.dumps(res, indent=1) + "\n")
    for r in res:
        print(json.dumps({k: r[k] for k in ("network", "hook", "mode", "ports", "removal_ports", "coefficients", "final_buses", "aviation_annual_mwh")}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
