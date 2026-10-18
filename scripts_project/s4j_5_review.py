"""S4J-5 static review: the S4I audit (s4i_static_audit.py, s4i_followups.py) re-run on the four S4J networks, compared item by item with the S4I
audit of the S4H package, plus the S4J-specific checks (read only, no solve):

  * every A-section value that differs between S4I and S4J, by network (flattened keys) -> S4J5_AUDIT_DIFF.csv;
  * demand: the total change equals the S4J-1 base-load change and only electricity changes;
  * losses: DC efficiency, H2 / gas compression ports, reverse copies with equal p_nom data, CO2 pipelines lossless, by network;
  * TH-MY DC bidirectional (forward + reversed) in the integrated networks, absent in the disconnected ones; converter B2B rule;
  * scenario differences: NZE vs integrated, disconnected vs integrated (cross-border components removed, new count).

    python scripts_project/s4j_5_review.py --s4i <S4I evidence dir> --s4j <S4J audit dir> --networks <S4J networks dir> --out <dir>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from s4j_layers import LOSS_EFFICIENCY, REV

NETS = dict(integrated="integrated_365_24h_unsolved.nc", disconnected="disconnected_365_24h_unsolved.nc",
            integrated_nze="integrated_nze_365_24h_unsolved.nc", disconnected_gap="disconnected_gap_diagnostic_365_24h_unsolved.nc")
KNG = "Khlong Ngae – Gurun"


def flat(d, p=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, f"{p}/{k}" if p else str(k)))
    elif isinstance(d, list):
        out[p] = json.dumps(d, sort_keys=True, default=str)[:300]
    else:
        out[p] = d
    return out


def audit_diff(s4i: dict, s4j: dict) -> pd.DataFrame:
    rows = []
    for net in NETS:
        a, b = s4i["sections"].get(net, {}), s4j["sections"].get(net, {})
        for sec in sorted(set(a) | set(b)):
            if not sec[:2] in ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "B_", "C_", "D_", "co", "le"):
                continue
            fa, fb = flat(a.get(sec, {})), flat(b.get(sec, {}))
            for k in sorted(set(fa) | set(fb)):
                va, vb = fa.get(k), fb.get(k)
                same = (va == vb) or (isinstance(va, float) and isinstance(vb, float) and np.isclose(va, vb, rtol=1e-9, atol=1e-12))
                if not same:
                    rows.append(dict(network=net, section=sec, key=k, s4i=str(va)[:200], s4j=str(vb)[:200]))
    for k in sorted(set(flat(s4i.get("A10_scenario_differences", {}))) | set(flat(s4j.get("A10_scenario_differences", {})))):
        va, vb = flat(s4i.get("A10_scenario_differences", {})).get(k), flat(s4j.get("A10_scenario_differences", {})).get(k)
        if va != vb:
            rows.append(dict(network="all", section="A10_scenario_differences", key=k, s4i=str(va)[:200], s4j=str(vb)[:200]))
    return pd.DataFrame(rows, columns=["network", "section", "key", "s4i", "s4j"])


def loss_checks(n) -> dict:
    L = n.links; rev = L.reversed.astype(bool) if "reversed" in L else pd.Series(False, index=L.index)
    out = {}
    for car, par in LOSS_EFFICIENCY.items():
        d = L[L.carrier == car]
        if d.empty:
            continue
        Lo = d.length_original.astype(float)
        exp = par["efficiency_static"] * par["efficiency_per_1000km"] ** (Lo / 1e3)
        ok_eff = bool(np.allclose(d.efficiency, exp, rtol=0, atol=1e-12))
        if par["compression_per_1000km"] > 0:
            ok_comp = bool(np.allclose(d.efficiency2, -par["compression_per_1000km"] * Lo / 1e3, rtol=0, atol=1e-12)) and bool((d.bus2 != "").all())
            ok_bus2 = bool(all(n.buses.at[b, "carrier"] in ("AC", "DC") for b in d.bus2))
        else:
            ok_comp, ok_bus2 = bool((d.bus2.fillna("") == "").all()), True
        r = d[rev.reindex(d.index)]
        pair_ok = all((n.links.at[x, "bus0"], n.links.at[x, "bus1"]) == (n.links.at[x[: -len(REV)], "bus1"], n.links.at[x[: -len(REV)], "bus0"])
                      and n.links.at[x, "p_nom_max"] == n.links.at[x[: -len(REV)], "p_nom_max"] and n.links.at[x, "capital_cost"] == 0 for x in r.index)
        out[car] = dict(links=int(len(d)), reversed=int(len(r)), one_way=int(((d.p_min_pu >= 0) & ~rev.reindex(d.index) & ~d.index.map(lambda x: (x + REV) in L.index)).sum()),
                        p_min_pu_zero=bool((d.p_min_pu == 0).all()), efficiency_rule=ok_eff, compression_rule=ok_comp, compression_bus_is_electricity=ok_bus2, reverse_pairs_ok=bool(pair_ok),
                        loss_share_min=float(1 - d.efficiency.max()), loss_share_max=float(1 - d.efficiency.min()))
    co2 = L[L.carrier == "CO2 pipeline"]
    out["CO2 pipeline"] = dict(links=int(len(co2)), lossless=bool((co2.efficiency == 1).all()), bidirectional=bool((co2.p_min_pu == -1).all()), reversed=int(rev.reindex(co2.index).sum()))
    return out


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser()
    for k in ("s4i", "s4j", "networks", "out"):
        ap.add_argument(f"--{k}", type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    s4i = json.loads((a.s4i / "static/S4I_STATIC_AUDIT.json").read_text()); s4j = json.loads((a.s4j / "static/S4I_STATIC_AUDIT.json").read_text())
    D = audit_diff(s4i, s4j); D.to_csv(a.out / "S4J5_AUDIT_DIFF.csv", index=False)
    nets = {k: pypsa.Network(str(a.networks / f)) for k, f in NETS.items()}
    res = dict(audit_diff_rows=int(len(D)), audit_diff_by_section=D.groupby(["network", "section"]).size().reset_index().rename(columns={0: "rows"}).to_dict(orient="records"))
    # demand
    dem = {}
    for k, n in nets.items():
        load = n.get_switchable_as_dense("Load", "p_set").mul(n.snapshot_weightings.generators, axis=0).sum()
        dem[k] = dict(total_twh=float(load.sum() / 1e6), by_carrier_twh={str(c): float(v / 1e6) for c, v in load.groupby(n.loads.carrier).sum().items()})
    res["demand"] = dem
    s4i_tot = {k: s4i["sections"][k]["A5_demand"].get("total_twh") for k in NETS if "A5_demand" in s4i["sections"][k]}
    res["demand_change_vs_s4i_twh"] = {k: (dem[k]["total_twh"] - s4i_tot[k]) if s4i_tot.get(k) is not None else None for k in NETS}
    # losses and TH-MY
    res["losses"] = {k: loss_checks(n) for k, n in nets.items()}
    th = {}
    for k, n in nets.items():
        th[k] = dict(forward=KNG in n.links.index, reversed=(KNG + REV) in n.links.index,
                     b2b={c: dict(extendable=bool(n.links.at[c, "p_nom_extendable"]), capital_cost=float(n.links.at[c, "capital_cost"]), p_nom_min=float(n.links.at[c, "p_nom_min"]),
                                  p_nom_max=float(n.links.at[c, "p_nom_max"])) for c in ("convert_412_577", "convert_599_890", "convert_935_1501") if c in n.links.index},
                     hooks=sorted(h for h in n.meta.get("required_constraint_hooks", []) if h.startswith("research_lossy") or h.startswith("research_b2b")))
    res["th_my_dc"] = th
    # scenario differences
    xb = {k: dict(lines=int((n.lines.border_class == "cross_border").sum()), links=int((n.links.border_class == "cross_border").sum()),
                  links_forward=int(((n.links.border_class == "cross_border") & ~n.links.reversed.astype(bool)).sum()) if "reversed" in n.links else None)
          for k, n in nets.items()}
    res["cross_border_components"] = xb
    i, z = nets["integrated"], nets["integrated_nze"]; diff = {}
    for c in ["Generator", "Link", "Store", "StorageUnit", "Line", "Load", "Bus"]:
        x, y = i.df(c), z.df(c)
        if set(x.index) != set(y.index):
            diff[c] = "index differs"; continue
        cols = [col for col in sorted(set(x.columns) & set(y.columns)) if not x[col].equals(y[col])]
        if cols:
            diff[c] = {col: int((x[col] != y[col]).sum()) for col in cols}
    res["integrated_vs_nze_static"] = diff
    (a.out / "S4J5_REVIEW.json").write_text(json.dumps(res, indent=1, default=str))
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90); pd.set_option("display.max_rows", 400)
    print(D.to_string())
    print(json.dumps({k: res[k] for k in ("demand_change_vs_s4i_twh", "losses", "th_my_dc", "cross_border_components", "integrated_vs_nze_static")}, indent=1, default=str))


if __name__ == "__main__":
    main()
