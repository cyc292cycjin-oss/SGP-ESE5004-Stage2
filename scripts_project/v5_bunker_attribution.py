"""V5 X20 revision 3-5 (decision 244; X20_SPEC.md 1.18): post-solve attribution of the methanol synthesis carbon to its uses (report only, no change to
the optimisation). Method (X10 scripts/08_x16_bunker.py with two corrections):
  (1) synthesis carbon: the atmosphere port p4 of the methanolisation links of each country (origin_neutral: the synthesis releases the carbon in the
      producing country, s3_layers.py), t CO2, by producer;
  (2) destinations: annual proportional mixing on the national methanol buses (INFERENCE): the methanol of a country bus is a mix of its own synthetic,
      biomass-based and extra-ASEAN imported methanol and of the methanol shipped in from other buses ('methanol ship' links, a linear system solved for
      the origin shares); every use of a bus (bunker shipping methanol, domestic shipping methanol, OCGT methanol, other) takes the bus mix - X10 counted
      only the own bunker of the producer; transport losses and the net store change are reported as 'unattributed';
  (3) carbon source of the synthesis carbon: the inflow shares of the producer's 'co2 stored' pools by capture carrier (CO2 pipeline / ship / transit
      excluded, X10 L36-50), classes fossil point source / process / DAC / biogenic / waste / other.
Output: rows producer x destination country x use x source class (Mt CO2); totals check: sum = synthesis carbon (relative 1e-6).
s2_solve writes BUNKER_CARBON_ATTRIBUTION.json / .csv after BUNKER_ACCOUNT.json for networks with a v5_x20 record; the CLI reads a solved file.
    python scripts_project/v5_bunker_attribution.py --network <solved .nc> --output <dir>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SRC_CLASS = {"DAC": "DAC (atmospheric)", "SMR CC": "fossil point source", "CCGT CC": "fossil point source", "process emissions CC": "process (mineral / feedstock) point source",
             "industry biomass CC": "biogenic", "biomass EOP CC": "biogenic", "industry direct firing biomass CC": "biogenic", "industry biomass boiler CC": "biogenic",
             "BtL": "biogenic", "biogas upgrading": "biogenic", "waste incineration": "waste (mixed)"}
TRANSFER = ("CO2 pipeline", "CO2 ship", "CO2 transit ship", "CO2 transit rail")


def tables_from_network(n):
    """(links static, annual positive / negative port flows, buses, loads, generators, generator annual p) of a solved pypsa Network."""
    w = n.snapshot_weightings.generators.values
    K = n.links.copy(); flows = {}
    for j in range(5):
        a = f"p{j}"
        if a in n.links_t and len(n.links_t[a].columns):
            P = n.links_t[a]
            flows[j] = pd.DataFrame(dict(pos=(P.clip(lower=0).mul(w, axis=0)).sum(), neg=(P.clip(upper=0).mul(w, axis=0)).sum()))
    gp = (n.generators_t.p.mul(w, axis=0)).sum() if len(n.generators_t.p.columns) else pd.Series(dtype=float)
    sp = {}
    for comp in ("stores",):
        if "p" in n.stores_t and len(n.stores_t.p.columns):
            sp = (n.stores_t.p.mul(w, axis=0)).sum().to_dict()
    return K, flows, n.buses, n.loads, n.generators, gp, n.stores, sp


def tables_from_file(nc: Path):
    import xarray as xr
    ds = xr.open_dataset(nc)
    def static(comp, cols):
        idx = ds[f"{comp}_i"].values.astype(str)
        return pd.DataFrame({c: (ds[f"{comp}_{c}"].values.astype(str) if ds[f"{comp}_{c}"].dtype.kind in "OSU" else ds[f"{comp}_{c}"].values) for c in cols if f"{comp}_{c}" in ds}, index=idx)
    K = static("links", ["carrier", "bus0", "bus1", "bus2", "bus3", "bus4", "efficiency"])
    B = static("buses", ["carrier", "country"]); L = static("loads", ["bus", "carrier", "country"]); G = static("generators", ["bus", "carrier"]); S = static("stores", ["bus", "carrier"])
    w = ds["snapshots_generators"].values.astype(float)
    flows = {}
    for j in range(5):
        v = f"links_t_p{j}"
        if v in ds:
            P = pd.DataFrame(ds[v].values, columns=ds[f"{v}_i"].values.astype(str))
            flows[j] = pd.DataFrame(dict(pos=(P.clip(lower=0).mul(w, axis=0)).sum(), neg=(P.clip(upper=0).mul(w, axis=0)).sum()))
    gp = pd.DataFrame(ds["generators_t_p"].values, columns=ds["generators_t_p_i"].values.astype(str)).mul(w, axis=0).sum() if "generators_t_p" in ds else pd.Series(dtype=float)
    sp = pd.DataFrame(ds["stores_t_p"].values, columns=ds["stores_t_p_i"].values.astype(str)).mul(w, axis=0).sum().to_dict() if "stores_t_p" in ds else {}
    ds.close()
    return K, flows, B, L, G, gp, S, sp


def attribute(K, flows, B, L, G, gp, S, sp) -> dict:
    def f(nm, j):
        d = flows.get(j)
        return (float(d.at[nm, "pos"]), float(d.at[nm, "neg"])) if (d is not None and nm in d.index) else (0.0, 0.0)
    K = K.copy()
    for c in ("bus0", "bus1", "bus2", "bus3", "bus4"):
        if c not in K:
            K[c] = ""
        K[c] = K[c].astype(str)
    cty = B["country"].astype(str)
    # (3) co2 stored pools: inflow by capture carrier
    pool_in = {}
    for nm, k in K.iterrows():
        if k.carrier in TRANSFER:
            continue
        for j in range(5):
            b = k["bus0" if j == 0 else f"bus{j}"]
            if b.endswith(" co2 stored"):
                pos, neg = f(nm, j)
                if neg < 0:
                    c = cty.get(b, ""); pool_in.setdefault(c, {}); pool_in[c][k.carrier] = pool_in[c].get(k.carrier, 0.0) - neg
    src_share = {}
    for c, d in pool_in.items():
        tot = sum(d.values())
        sh = {}
        for car, v in d.items():
            cl = SRC_CLASS.get(car, "other"); sh[cl] = sh.get(cl, 0.0) + (v / tot if tot > 0 else 0.0)
        src_share[c] = sh
    # (1) / (2) methanol buses
    mbus = sorted({b for b in K.bus1.tolist() + K.bus0.tolist() if b.endswith(" methanol") and b in cty.index})
    own, syn_c, meoh_syn, uses, ship = {}, {}, {}, {}, []
    for mb in mbus:
        c = cty[mb]
        ml = K.index[(K.carrier == "methanolisation") & (K.bus1 == mb)]
        meoh_syn[mb] = sum(-f(nm, 1)[1] for nm in ml); syn_c[mb] = sum(-f(nm, 4)[1] for nm in ml)
        bm = K.index[(K.carrier == "biomass-to-methanol") & (K.bus1 == mb)]
        imp = float(gp.reindex(G.index[G.bus.astype(str) == mb]).fillna(0).sum()) if len(gp) else 0.0
        own[mb] = {("synthetic", c): meoh_syn[mb], ("biomass", c): sum(-f(nm, 1)[1] for nm in bm), ("import", "extra-ASEAN"): imp}
        tr = K.index[(K.bus0 == mb) & (K.bus1 != mb) & K.bus1.isin(mbus)]   # transfers between methanol buses: ships and the Lao rail transit
        for nm in tr:
            ship.append((mb, K.at[nm, "bus1"], f(nm, 0)[0], -f(nm, 1)[1]))
        u = {}
        for nm in K.index[(K.bus0 == mb) & ~K.index.isin(tr)]:
            car = K.at[nm, "carrier"]; v = f(nm, 0)[0]
            key = ("bunker shipping" if "bunker" in K.at[nm, "bus1"] else "domestic shipping") if car == "shipping methanol" else ("OCGT methanol" if car == "OCGT methanol" else f"other ({car})")
            u[key] = u.get(key, 0.0) + v
        ld = L.index[L.bus.astype(str) == mb]
        for nm in ld:
            u[f"load ({L.at[nm, 'carrier']})"] = u.get(f"load ({L.at[nm, 'carrier']})", 0.0)
        uses[mb] = u
    origins = sorted({o for d in own.values() for o in d})
    idx = {mb: i for i, mb in enumerate(mbus)}; nb, no = len(mbus), len(origins)
    # total inflow T_i = own_i + ship in_i ; composition x_i (origin shares): T_i x_i = own_i + sum_j in_ji x_j
    A = np.zeros((nb, nb)); rhs = np.zeros((nb, no)); Tin = np.zeros(nb)
    for mb in mbus:
        i = idx[mb]
        for o, v in own[mb].items():
            rhs[i, origins.index(o)] += v; Tin[i] += v
    for a, b, out_, in_ in ship:
        if b in idx:
            Tin[idx[b]] += in_
    for i in range(nb):
        A[i, i] = Tin[i] if Tin[i] > 0 else 1.0
    for a, b, out_, in_ in ship:
        if b in idx and a in idx:
            A[idx[b], idx[a]] -= in_
    X = np.linalg.solve(A, rhs)   # origin shares per bus (rows sum to 1 where the bus has inflow)
    rows = []
    for mb in mbus:
        i = idx[mb]; c = cty[mb]
        for use, v in uses[mb].items():
            if v <= 0:
                continue
            for k, o in enumerate(origins):
                if o[0] != "synthetic" or X[i, k] <= 0:
                    continue
                pb = f"{o[1]} methanol"
                cpm = syn_c[pb] / meoh_syn[pb] if meoh_syn.get(pb, 0) > 0 else 0.0
                mt = v * X[i, k] * cpm / 1e6
                for cl, s in (src_share.get(o[1]) or {"unknown": 1.0}).items():
                    rows.append(dict(producer=o[1], destination=c, use=use, source_class=cl, carbon_mt=mt * s))
    T = pd.DataFrame(rows, columns=["producer", "destination", "use", "source_class", "carbon_mt"])
    syn_tot = sum(syn_c.values()) / 1e6
    per_prod = T.groupby("producer").carbon_mt.sum().to_dict() if len(T) else {}
    for mb in mbus:   # unattributed = synthesis carbon not reaching a use (ship losses, net store change, solver tolerance)
        c = cty[mb]; un = syn_c[mb] / 1e6 - per_prod.get(c, 0.0)
        if abs(un) > 0:
            T.loc[len(T)] = dict(producer=c, destination="", use="unattributed (transport loss / store change)", source_class="", carbon_mt=un)
    tot = float(T.carbon_mt.sum())
    to_uses = float(T[~T.use.str.startswith("unattributed")].carbon_mt.sum())
    rel = abs(to_uses - syn_tot) / syn_tot if syn_tot > 0 else 0.0   # the uses carry the whole synthesis carbon (the unattributed row is not counted)
    bunker = float(T[T.use == "bunker shipping"].carbon_mt.sum())
    own_bunker = float(T[(T.use == "bunker shipping") & (T.producer == T.destination)].carbon_mt.sum())
    return dict(rule=__doc__.split("\n\n")[0], synthesis_carbon_mt=syn_tot, attributed_total_mt=tot, relative_difference=rel, check_passed=bool(rel < 1e-6),
                bunker_attributed_mt=bunker, bunker_own_producer_mt=own_bunker, unattributed_mt=float(T[T.use.str.startswith("unattributed")].carbon_mt.sum()),
                by_use=T.groupby("use").carbon_mt.sum().round(6).to_dict(), by_producer=T.groupby("producer").carbon_mt.sum().round(6).to_dict(),
                pool_source_shares=src_share, origin_shares={mb: {f"{o[0]}:{o[1]}": float(X[idx[mb], k]) for k, o in enumerate(origins) if X[idx[mb], k] > 1e-12} for mb in mbus},
                table=T.to_dict("records"))


def write(rep: dict, out: Path, name: str = "BUNKER_CARBON_ATTRIBUTION"):
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rep["table"]).to_csv(out / f"{name}.csv", index=False, lineterminator="\n")
    (out / f"{name}.json").write_text(json.dumps({k: v for k, v in rep.items() if k != "table"}, indent=1, default=float) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--name", default="BUNKER_CARBON_ATTRIBUTION"); a = ap.parse_args(argv)
    rep = attribute(*tables_from_file(a.network)); rep["network"] = str(a.network)
    write(rep, a.output, a.name)
    print(json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in rep.items() if k in ("synthesis_carbon_mt", "attributed_total_mt", "relative_difference",
                                                                                                    "check_passed", "bunker_attributed_mt", "bunker_own_producer_mt", "unattributed_mt", "by_use")}, indent=1))


if __name__ == "__main__":
    main()
