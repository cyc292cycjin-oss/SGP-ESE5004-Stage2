"""S4J-3 data (decision 105 b, S4I U2; rewritten by S4J supplement 01, decision 107 a): TH-MY DC link and the converter B2B.

  * DC_CONVERTERS_S4J3.csv: every DC link of the built network (forward links; the '-reversed' copies of S4J-2 listed with their forward link) with
    direction before / after, and every DC bus with its DC links, B2B converters and the action (converter-station pair: B2B bidirectional, not
    extendable, p_nom fixed at the DC extension limit; other structure reported only).
  * model-build check (no solve, first 56 snapshots): rows of research_lossy_bidirectional_sync; no research_b2b_* rows any more.
  * registry fragment s4j_3 (replaces the S4J-3 version of the fragment).

    python scripts_project/s4j_3_data.py --network <integrated build> --noloss <build with network.transmission_losses=none>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv
from s4j_layers import REV, SYNC_HOOK

SCRIPT = "scripts_project/s4j_3_data.py"
INSTRUCTION_SHA = "c20957448c69128c05eaf4e271bcca7f98eecc7ccd3121cd37f3581daff3348f"
SUPPLEMENT_SHA = "188743eb4c139d40453f2d0a6f6a12b09daffdb84b5da4826b7273f4389fac55"
LOC = "work/p1_step4j_20261018/S4J_SUPPLEMENT_01.md"
OUT = ROOT / "research_inputs/corridors/DC_CONVERTERS_S4J3.csv"


def model_rows(network: Path) -> dict:
    import pypsa
    from assembly_components import install_research_constraint_hooks
    n = pypsa.Network(str(network)); n.set_snapshots(n.snapshots[:56])
    n.meta.update(solver_allowed=True, artifact_role="S4J3_MODEL_CHECK_UNSOLVED", s2_solve_label="S4J3_MODEL_CHECK")
    m = n.optimize.create_model(transmission_losses=int(n.meta["research_transmission_losses"]["ac_transmission_losses"])); install_research_constraint_hooks(n)
    return dict(b2b_rows=sum(1 for k in m.constraints if k.startswith("research_b2b")), sync_rows=sum(1 for k in m.constraints if k.startswith(SYNC_HOOK)),
                num_col=int(m.nvars), num_row=int(m.ncons))


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--noloss", type=Path, required=True); a = ap.parse_args()
    n = pypsa.Network(str(a.network)); z = pypsa.Network(str(a.noloss))
    led = n.meta["research_dc_converters"]
    if led.get("mode") != "bidirectional_fixed_b2b":
        raise ValueError("--network is not a th_my_hvdc = bidirectional_fixed_b2b build")
    L = n.links; dc = L[(L.carrier == "DC") & ~L.reversed.astype(bool)]
    pair_by_link = {}
    for p in led["pairs"]:
        pair_by_link.setdefault(p["dc_link"], []).append(p["b2b"])
    rows = []
    for k, r in dc.iterrows():
        rows.append(dict(kind="dc_link", name=k, bus0=r.bus0, bus1=r.bus1, border_class=r.border_class, direction_before=("one-way" if k in led["one_way_made_bidirectional"] else "bidirectional"),
                         direction_after=("bidirectional (lossy forward + reversed)" if (k + REV) in L.index else "bidirectional"), reversed_copy=((k + REV) if (k + REV) in L.index else ""),
                         efficiency=float(r.efficiency), p_nom=float(r.p_nom), p_nom_max=float(r.p_nom_max), p_nom_extendable=bool(r.p_nom_extendable), converter_b2b=";".join(pair_by_link.get(k, [])),
                         noloss_p_min_pu=float(z.links.at[k, "p_min_pu"]), action=("made bidirectional" if k in led["one_way_made_bidirectional"] else "unchanged")))
    for p in led["pairs"]:
        c = n.links.loc[p["b2b"]]
        if bool(c.p_nom_extendable) or float(c.p_min_pu) != -1.0 or float(c.efficiency) != 1.0 or abs(float(c.p_nom) - p["dc_p_nom_max"]) > 1e-9:
            raise ValueError(f"B2B {p['b2b']} not set as the rule says")
        rows.append(dict(kind="b2b_pair", name=p["b2b"], bus0=c.bus0, bus1=c.bus1, border_class=c.border_class, direction_before="bidirectional", direction_after="bidirectional",
                         reversed_copy="", efficiency=float(c.efficiency), p_nom=float(c.p_nom), p_nom_max=float(c.p_nom_max), p_nom_extendable=bool(c.p_nom_extendable), converter_b2b=p["dc_link"],
                         noloss_p_min_pu=float(z.links.at[p["b2b"], "p_min_pu"]),
                         action=(f"converter of {p['dc_link']}: p_nom {p['b2b_p_nom_before']:.0f} -> {p['b2b_p_nom_after']:.0f} MW (DC extension limit), not extendable, bidirectional, "
                                 f"efficiency 1; capital cost {p['b2b_capital_cost']:.0f} EUR/MW/a not in the objective (non-extendable)")))
    for r in led["reported"]:
        for c in r["b2b"]:
            b = n.links.loc[c]
            rows.append(dict(kind="b2b_reported", name=c, bus0=b.bus0, bus1=b.bus1, border_class=b.border_class, direction_before="bidirectional", direction_after="bidirectional",
                             reversed_copy="", efficiency=float(b.efficiency), p_nom=float(b.p_nom), p_nom_max=float(b.p_nom_max), p_nom_extendable=bool(b.p_nom_extendable), converter_b2b="",
                             noloss_p_min_pu=float(z.links.at[c, "p_min_pu"]), action=f"reported only ({r['reason']}; DC links at {r['dc_bus']}: {', '.join(r['dc_links'])})"))
    T = pd.DataFrame(rows); write_csv(T.to_dict("records"), OUT, list(T.columns))
    mr = model_rows(a.network)
    if mr["b2b_rows"] != 0:
        raise ValueError("research_b2b rows still in the model")
    js = dict(network=str(a.network), noloss=str(a.noloss), meta=led, model=mr, supplement_sha256=SUPPLEMENT_SHA)
    OUT.with_suffix(".json").write_text(json.dumps(js, indent=1, default=str))
    reg = Registry(SCRIPT)
    reg.add("s4j3_th_my_hvdc_switch", "Decisions 105 b, 107 a: research.network.th_my_hvdc = bidirectional_fixed_b2b (main) | s4h (S4H state: one-way Khlong Ngae - Gurun, "
            "B2B 2,000 MW; comparison, default when absent)", "bidirectional_fixed_b2b|s4h", "flag", "B", "S4J supplement 01 (a) 3", LOC, SUPPLEMENT_SHA, decision_ref="105,107",
            status="REFERENCE_ONLY")
    reg.add("s4j3_dc_bidirectional", "Decision 105 b: one-way DC links made bidirectional (" + ", ".join(led["one_way_made_bidirectional"]) + "; p_min_pu 0 -> -1; with "
            "transmission_losses = pypsa_eur split into a lossy forward / reverse pair, without losses p_min_pu = -1)", "bidirectional", "flag", "B", "S4J instruction S4J-3; supplement 01 (a) 1",
            LOC, SUPPLEMENT_SHA, decision_ref="105,107", status="REFERENCE_ONLY")
    reg.add("s4j3_b2b_fixed_at_dc_limit", "Decision 107 a (rewrite of the S4J-3 B2B rule): converter-station B2B (DC bus with exactly one DC link and one B2B: "
            + ", ".join(f"{p['b2b']} at {p['dc_bus']}" for p in led["pairs"]) + ") bidirectional, NOT extendable, efficiency 1, p_nom fixed at the DC link's extension limit "
            f"({', '.join(sorted({str(round(p['dc_p_nom_max'])) for p in led['pairs']}))} MW = stock 300 + 20,000); no zero-cost capacity variable, no coupling equality (hook "
            "research_b2b_follows_dc withdrawn: the zero-cost variable + equality failed the solver-tolerance gates, S4J_STOP_01 section 7). Reasons: the converter-station "
            "cost is part of the DC link cost; a B2B fixed at the DC extension limit never binds before the DC link, so the feasible DC flows equal those of the S4J-3 form. "
            "Difference recorded: generation candidates at the two DC buses (CCGT / OCGT / FT duplicates of the AC-bus candidates, 34 MW offshore wind at CF 0.037; no load, "
            "no existing capacity) may now export up to 20,300 MW instead of 2,000 + the DC increment. Disconnected: the DC link is removed, the B2B keeps the S4H state. "
            "Other structures reported: " + "; ".join(f"{r['dc_bus']} ({r['reason']})" for r in led["reported"]), "table", "flag", "B", "derived (scripts_project/s4j_3_data.py)",
            "research_inputs/corridors/DC_CONVERTERS_S4J3.csv", sha256(OUT), decision_ref="105,107", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4j_3.csv")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 140)
    print(T[["kind", "name", "bus0", "bus1", "direction_before", "direction_after", "p_nom", "p_nom_max", "p_nom_extendable", "action"]].to_string()); print(json.dumps(mr))


if __name__ == "__main__":
    main()
