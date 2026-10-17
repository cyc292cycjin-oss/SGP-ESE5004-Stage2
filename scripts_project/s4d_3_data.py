"""S4D-3 data (decision 91a): in-country length shares of the cross-border components (ledger sensitivity), ledger rules and the read-only
trial on the three S4C-6 smoke solutions; registry fragment s4d_3.

Length shares: for every cross-border line / link of the S4D-2 integrated build (border_class cross_border), the straight segment between its
two end buses (lon / lat) is sampled at 401 points; each point is assigned to the land or EEZ of a country (author country_shapes and
offshore_shapes); share_a = points in country a / points in the two end countries (points in a third country or outside all shapes are spread
in proportion). Components are keyed by type and name (the names are stable across the S4D builds).

    python scripts_project/s4d_3_data.py --network <S4D-2 integrated build> --trial results_project/s4c/s4c6/solves_main --out results_project/s4d/ledger_trial_s4c
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.ops import unary_union

import s4d_1_coastline as C
from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv
from s4d_ledger import REL_TOL, country_cost_ledger, ledger_gate, ledger_table, nodal_prices

SCRIPT = "scripts_project/s4d_3_data.py"
INSTRUCTION_SHA = "a35fa7d52c0d645830562e57fb242563b864994682eeb1ce6a2a8d59f73b2586"
SHARES = ROOT / "research_inputs/corridors/XB_LENGTH_SHARES_S4D3.csv"
SAMPLES = 401
RULES = ("Decision 91a ledger rules (both scenarios): (1) every objective term is a direct cost of the owner of its component - new capacity "
         "(p_nom_opt - p_nom) x capital_cost, marginal cost x flow x weight, fixed-once constants (existing asset FOM, existing cross-border FOM) - "
         "as in gate A5; own facilities, fuels and extra-ASEAN imports -> own country; domestic gas at the decision-43 price is the producing "
         "country's generator cost; one-port components belong to the country of their country column (e.g. national ammonia demand on the regional "
         "ammonia bus) else to the entity of their bus; (2) cross-border lines / links (incl. existing) -> the corridor, its costs and its congestion "
         "rent (settlement surplus) split half / half between the two countries (main) or by in-country length (sensitivity, XB_LENGTH_SHARES_S4D3.csv); "
         "(3) every component port on a bus of another entity is settled at that bus's dual (marginal_price x weight): cross-border electricity / H2 / "
         "gas / CO2 exchanges at each end's nodal dual, liquid-fuel purchases and sales of a country at the regional bus dual, bunker fuel at the "
         "regional dual into the separate 'ASEAN bunker account' subject (no country), CO2 shipping freight -> exporter and the storage service at the "
         "receiver's 'co2 sequestered <j>' dual (exporter pays, receiver is paid), Lao transit freight -> LA; (4) the regional liquid pool has no "
         "owner: its surplus (rents of binding limits on regional supply; zero by LP duality when none binds) is the difference term; (5) gate "
         "B16_LEDGER: |countries + bunker account - objective (incl. constants)| <= 1e-6 x |objective|, in both acceptance sets")


def length_shares(network: Path) -> pd.DataFrame:
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(network))
    land = gpd.read_file(C.LAND).to_crs("EPSG:4326"); eez = gpd.read_file(C.EEZ).to_crs("EPSG:4326")
    geo = {c: unary_union(list(land.geometry[land.name == c]) + list(eez.geometry[eez.name == c])) for c in sorted(set(land.name) | set(eez.name))}
    nodes = n.buses.index[n.buses.carrier.isin(["AC", "DC"])]
    by_len = sorted(nodes, key=len, reverse=True)

    def node_of(bus):   # carrier buses ('<node> co2 stored', '<node> gas') carry no coordinates: use their geographical node
        if bus in nodes:
            return bus
        loc = str(n.buses.at[bus, "location"]) if "location" in n.buses else ""
        if loc in nodes:
            return loc
        hit = next((g for g in by_len if bus.startswith(g + " ")), None)
        if hit is None:
            raise ValueError(f"no geographical node for {bus}")
        return hit
    rows = []
    for t in ("Line", "Link"):
        d = n.df(t)
        for name, z in d[d.border_class == "cross_border"].iterrows():
            b0, b1 = z.bus0, z.bus1
            a, b = str(n.buses.at[b0, "country"]), str(n.buses.at[b1, "country"])
            g0, g1 = node_of(b0), node_of(b1)
            x0, y0, x1, y1 = (float(n.buses.at[g0, "x"]), float(n.buses.at[g0, "y"]), float(n.buses.at[g1, "x"]), float(n.buses.at[g1, "y"]))
            s = np.linspace(0, 1, SAMPLES)
            pts = [Point(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u) for u in s]
            na = sum(geo[a].contains(p) for p in pts) if a in geo else 0
            nb = sum(geo[b].contains(p) for p in pts) if b in geo else 0
            other = SAMPLES - na - nb
            sa = na / (na + nb) if na + nb else 0.5
            ca, cb = sorted([a, b]); sh = {a: sa, b: 1 - sa}
            rows.append(dict(component_type=t, component=name, carrier=z.carrier, bus0=b0, bus1=b1, node0=g0, node1=g1, country_a=ca, country_b=cb, share_a=round(sh[ca], 4), share_b=round(sh[cb], 4),
                             samples_a=na if ca == a else nb, samples_b=nb if ca == a else na, samples_other=other))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", type=Path, required=True); ap.add_argument("--trial", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    sh = length_shares(a.network)
    SHARES.parent.mkdir(parents=True, exist_ok=True)
    write_csv(sh.to_dict("records"), SHARES, list(sh.columns))
    import pypsa
    logging.disable(logging.WARNING)
    a.out.mkdir(parents=True, exist_ok=True)
    trial = {}
    for s in ("integrated", "disconnected", "integrated_nze"):
        sc = "integrated" if s.startswith("integrated") else "disconnected"
        f = a.trial / s / f"{sc}_SMOKE_TEST_ONLY_solved.nc"
        n = pypsa.Network(str(f))
        L, ident, diag = country_cost_ledger(n, sh)
        T = ledger_table(L)
        (a.out / s).mkdir(exist_ok=True)
        T.to_csv(a.out / s / "COUNTRY_COST_LEDGER.csv"); L.to_csv(a.out / s / "COUNTRY_COST_LEDGER_DETAIL.csv", index=False)
        nodal_prices(n).to_csv(a.out / s / "NODAL_PRICES.csv", float_format="%.6g")
        g = ledger_gate(ident)
        trial[s] = dict(solution=str(f), solution_sha256=sha256(f), gate=g, identity=ident, corridors=diag["corridors"], pool=diag["pool"],
                        one_port_owned_by_country_column=diag["one_port_owned_by_country_column"], length_shares_missing=diag["length_shares_missing"],
                        totals_bn_eur={k: round(float(v) / 1e9, 4) for k, v in T["total"].items()},
                        totals_length_split_bn_eur={k: round(float(v) / 1e9, 4) for k, v in T["total_length_split"].items()})
    (a.out / "S4D3_LEDGER_TRIAL.json").write_text(json.dumps(trial, indent=1, default=float))
    reg = Registry(SCRIPT); ins = "work/p1_step4d_20261017/S4D_CLAUDE_CODE_INSTRUCTION.md"
    reg.add("s4d3_ledger_rules", RULES, "rules", "flag", "B", "S4D instruction S4D-3 item 1", "scripts_project/s4d_ledger.py", INSTRUCTION_SHA, decision_ref="91", status="REFERENCE_ONLY")
    reg.add("s4d3_ledger_identity_tolerance", "Gate B16_LEDGER: relative tolerance of the identity countries + bunker account = objective (incl. the fixed-once constants)", REL_TOL,
            "relative", "B", "S4D instruction S4D-3 item 2", ins, INSTRUCTION_SHA, decision_ref="91", status="REFERENCE_ONLY")
    reg.add("s4d3_xb_length_shares", f"In-country length shares of the {len(sh)} cross-border lines / links (sensitivity of the corridor split; straight segment between the end buses, "
            f"{SAMPLES} samples, author land + EEZ shapes)", "table", "flag", "B", "derived (scripts_project/s4d_3_data.py)", "research_inputs/corridors/XB_LENGTH_SHARES_S4D3.csv",
            sha256(SHARES), decision_ref="91", status="REFERENCE_ONLY")
    reg.add("s4d3_nodal_prices_aggregation", "NODAL_PRICES.csv (wide, one row per bus = node x carrier): the dual price (buses_t.marginal_price, EUR per MWh or t) aggregated to calendar days as the "
            "snapshot-weighted mean (one column per day), plus the weighted mean, min and max over the run", "daily_weighted_mean", "flag", "B", "S4D instruction S4D-3 item 3",
            "scripts_project/s4d_ledger.nodal_prices", INSTRUCTION_SHA, decision_ref="91", status="REFERENCE_ONLY")
    tr = "; ".join(f"{s}: relative error {v['identity']['relative_error']:.2e}, pool surplus {-v['identity']['difference_sources']['asean_pool_surplus']:.2f} EUR" for s, v in trial.items())
    reg.add("s4d3_trial_s4c_smokes", "Read-only trial on the three S4C-6 smoke solutions (no re-solve): " + tr + "; first draft booked the 77 national industry ammonia loads on "
            "the regional ammonia bus to the pool (relative error 0.8-0.9 %), fixed by the country-column ownership of one-port components", "B16_pass", "flag", "B",
            "results_project/s4c/s4c6/solves_main", "results_project/s4d/ledger_trial_s4c/S4D3_LEDGER_TRIAL.json", sha256(a.out / "S4D3_LEDGER_TRIAL.json"), decision_ref="91",
            status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4d_3.csv")
    print(json.dumps({s: dict(passed=v["gate"]["passed"], rel=v["identity"]["relative_error"], rel_len=v["identity"]["relative_error_length_split"],
                              pool=v["identity"]["difference_sources"]["asean_pool_surplus"], missing=v["length_shares_missing"]) for s, v in trial.items()}, indent=1, default=float))
    print(sh[["component_type", "component", "country_a", "country_b", "share_a", "share_b", "samples_other"]].to_string())
    for s, v in trial.items():
        print(s, {k: (v["totals_bn_eur"][k], v["totals_length_split_bn_eur"][k]) for k in v["totals_bn_eur"]})


if __name__ == "__main__":
    main()
