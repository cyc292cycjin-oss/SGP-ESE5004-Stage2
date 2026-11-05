"""V3 DIAG step 4 (static, no model, no solver): every constraint written as an annual sum, a last-snapshot level or an annual cap, with its
right-hand side in the full-year path (s2_solve.py without --truncate: weights as stored, meta as stored) and in the truncated path
(set_representative_weights: weights 8760/N, research_co2_storage.horizon_fraction = 1.0, annual caps unscaled). Also the Store attributes that
make a last-snapshot level depend on the horizon (e_initial, e_cyclic, e_nom, e_min_pu / e_max_pu, standing_loss).

    python annual_rhs.py <network.nc> <out.json>
"""
import json
import sys

import numpy as np
import pandas as pd
import pypsa
import logging

logging.getLogger("pypsa").setLevel(logging.ERROR)


def jsafe(x):
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    if isinstance(x, dict):
        return {str(k): jsafe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsafe(v) for v in x]
    return x


def store_rows(n, names):
    st = n.stores
    cols = [c for c in ("bus", "carrier", "country", "e_nom", "e_nom_extendable", "e_nom_max", "e_nom_min", "e_min_pu", "e_max_pu", "e_initial", "e_cyclic",
                        "standing_loss", "marginal_cost", "research_role") if c in st.columns]
    out = {}
    for s in names:
        if s in st.index:
            row = {c: jsafe(st.at[s, c]) for c in cols}
            for att in ("e_min_pu", "e_max_pu"):
                if att in n.stores_t and s in n.stores_t[att].columns:
                    v = n.stores_t[att][s]
                    row[att + "_t"] = dict(min=float(v.min()), max=float(v.max()), first=float(v.iloc[0]), last=float(v.iloc[-1]))
            out[s] = row
    return out


def main(net, out):
    n = pypsa.Network(net)
    w = n.snapshot_weightings
    N = len(n.snapshots)
    meta = n.meta
    res = dict(network=net, snapshots=N, weights={c: dict(sum=float(w[c].sum()), first=float(w[c].iloc[0])) for c in w.columns})
    res["required_constraint_hooks"] = list(meta.get("required_constraint_hooks", []))
    rc = meta.get("research_carbon", {})
    res["research_country_net_zero"] = dict(constraint_scope=rc.get("constraint_scope"), country_cap_tco2=jsafe(rc.get("country_cap_tco2")), asean_total_cap_tco2=jsafe(rc.get("asean_total_cap_tco2")),
                                            rows="Store-e(last snapshot, co2 atmosphere <c>) <= cap (unscaled in both paths)")
    cs = meta.get("research_co2_storage", {})
    res["research_co2_storage_cap"] = dict(caps_t_per_year=jsafe(cs.get("caps_t_per_year")), horizon_fraction_full_year_path=jsafe(cs.get("horizon_fraction", 1.0)),
                                           horizon_fraction_truncated_path=1.0, rows="Store-e(last, co2 sequestered <c>) <= cap x horizon_fraction")
    res["external_annual_caps"] = dict(caps=jsafe(meta.get("external_annual_caps", {})), rows="sum_t Generator-p x weight_generators <= cap (unscaled in both paths)")
    res["store_power_rules"] = jsafe(meta.get("store_power_rules", {}))
    atm = [s for s in n.stores.index if s.startswith("co2 atmosphere")]
    seq = [s for s in n.stores.index if n.stores.at[s, "carrier"] == "co2 sequestered"] if "carrier" in n.stores else []
    bunker = [s for s in n.stores.index if "bunker" in s.lower()]
    res["atmosphere_stores"] = store_rows(n, atm)
    res["sequestration_stores"] = store_rows(n, seq)
    res["bunker_stores"] = store_rows(n, bunker)
    st = n.stores
    noncyc = st.index[~st.e_cyclic.astype(bool)] if "e_cyclic" in st else st.index
    init = st.index[(st.e_initial.astype(float) != 0)] if "e_initial" in st else st.index[:0]
    res["stores_noncyclic_count"] = int(len(noncyc)); res["stores_cyclic_count"] = int(len(st) - len(noncyc))
    res["stores_with_e_initial"] = store_rows(n, list(init))
    if "research_role" in st:
        res["finite_resource_stores"] = store_rows(n, list(st.index[st.research_role == "FINITE_RESOURCE"]))
    # time-dependent store bounds that pin a level at a snapshot (e_min_pu > 0 or e_max_pu < 1 at some snapshot)
    pins = {}
    for att in ("e_min_pu", "e_max_pu"):
        if att in n.stores_t and len(n.stores_t[att].columns):
            df = n.stores_t[att]
            sel = df.columns[(df.max() > 0)] if att == "e_min_pu" else df.columns[(df.min() < 1)]
            pins[att] = dict(count=int(len(sel)), carriers=jsafe(st.loc[sel, "carrier"].value_counts().to_dict()) if len(sel) else {})
    res["time_varying_store_bounds"] = pins
    res["global_constraints"] = jsafe(n.global_constraints.reset_index().to_dict("records")) if len(n.global_constraints) else []
    json.dump(jsafe(res), open(out, "w"), indent=1, default=str)
    print(json.dumps(dict(snapshots=N, atmosphere=len(atm), sequestration=len(seq), bunker=bunker, noncyclic=res["stores_noncyclic_count"], with_e_initial=len(init),
                          external_annual_caps=len(res["external_annual_caps"]["caps"] or {}), horizon_fraction_full=res["research_co2_storage_cap"]["horizon_fraction_full_year_path"])))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
