"""S4J-3 data (decision 105 b, S4I U2): DC links and B2B converters.

  * DC_CONVERTERS_S4J3.csv: every DC link of the built network (forward links; the '-reversed' copies of S4J-2 listed with their forward link) with
    direction before / after, and every DC bus with its DC links, B2B converters and the action (converter-station pair handled, other structure
    reported only).
  * model-build check (no solve, first 56 snapshots): rows of the hooks research_b2b_follows_dc and research_lossy_bidirectional_sync.
  * registry fragment s4j_3.

    python scripts_project/s4j_3_data.py --network <S4J-3 integrated build> --noloss <S4J-3 build with network.transmission_losses=none>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv
from s4j_layers import B2B_HOOK, REV, SYNC_HOOK

SCRIPT = "scripts_project/s4j_3_data.py"
INSTRUCTION_SHA = "c20957448c69128c05eaf4e271bcca7f98eecc7ccd3121cd37f3581daff3348f"
LOC = "work/p1_step4j_20261018/S4J_CLAUDE_CODE_INSTRUCTION.md"
OUT = ROOT / "research_inputs/corridors/DC_CONVERTERS_S4J3.csv"


def model_rows(network: Path) -> dict:
    import pypsa
    from assembly_components import install_research_constraint_hooks
    n = pypsa.Network(str(network)); n.set_snapshots(n.snapshots[:56])
    n.meta.update(solver_allowed=True, artifact_role="S4J3_MODEL_CHECK_UNSOLVED", s2_solve_label="S4J3_MODEL_CHECK")
    m = n.optimize.create_model(transmission_losses=int(n.meta["research_transmission_losses"]["ac_transmission_losses"])); install_research_constraint_hooks(n)
    return dict(b2b_rows=sum(1 for k in m.constraints if k.startswith(B2B_HOOK)), sync_rows=sum(1 for k in m.constraints if k.startswith(SYNC_HOOK)),
                num_col=int(m.nvars), num_row=int(m.ncons))


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--noloss", type=Path, required=True); a = ap.parse_args()
    n = pypsa.Network(str(a.network)); z = pypsa.Network(str(a.noloss))
    led = n.meta["research_dc_converters"]
    L = n.links; dc = L[(L.carrier == "DC") & ~L.reversed.astype(bool)]
    pair_by_link = {}
    for p in led["pairs"]:
        pair_by_link.setdefault(p["dc_link"], []).append(p["b2b"])
    rows = []
    for k, r in dc.iterrows():
        rows.append(dict(kind="dc_link", name=k, bus0=r.bus0, bus1=r.bus1, border_class=r.border_class, direction_before=("one-way" if k in led["one_way_made_bidirectional"] else "bidirectional"),
                         direction_after=("bidirectional (lossy forward + reversed)" if (k + REV) in L.index else "bidirectional"), reversed_copy=((k + REV) if (k + REV) in L.index else ""),
                         efficiency=float(r.efficiency), p_nom=float(r.p_nom), p_nom_max=float(r.p_nom_max), b2b_following=";".join(pair_by_link.get(k, [])),
                         noloss_p_min_pu=float(z.links.at[k, "p_min_pu"]), action=("made bidirectional" if k in led["one_way_made_bidirectional"] else "unchanged")))
    for p in led["pairs"]:
        c = n.links.loc[p["b2b"]]
        rows.append(dict(kind="b2b_pair", name=p["b2b"], bus0=c.bus0, bus1=c.bus1, border_class=c.border_class, direction_before="bidirectional", direction_after="bidirectional",
                         reversed_copy="", efficiency=float(c.efficiency), p_nom=float(c.p_nom), p_nom_max=float(c.p_nom_max), b2b_following=p["dc_link"], noloss_p_min_pu=float(z.links.at[p["b2b"], "p_min_pu"]),
                         action=f"follows {p['dc_link']}: p_nom - {p['b2b_p_nom_existing']:.0f} = DC p_nom - {p['dc_p_nom_existing']:.0f}; capital cost {p['b2b_capital_cost_before']:.0f} -> 0; extendable"))
    for r in led["reported"]:
        for c in r["b2b"]:
            b = n.links.loc[c]
            rows.append(dict(kind="b2b_reported", name=c, bus0=b.bus0, bus1=b.bus1, border_class=b.border_class, direction_before="bidirectional", direction_after="bidirectional",
                             reversed_copy="", efficiency=float(b.efficiency), p_nom=float(b.p_nom), p_nom_max=float(b.p_nom_max), b2b_following="", noloss_p_min_pu=float(z.links.at[c, "p_min_pu"]),
                             action=f"reported only ({r['reason']}; DC links at {r['dc_bus']}: {', '.join(r['dc_links'])})"))
    T = pd.DataFrame(rows); write_csv(T.to_dict("records"), OUT, list(T.columns))
    mr = model_rows(a.network)
    if mr["b2b_rows"] != len(led["pairs"]):
        raise ValueError("B2B hook rows differ from the pairs")
    js = dict(network=str(a.network), noloss=str(a.noloss), meta=led, model=mr)
    OUT.with_suffix(".json").write_text(json.dumps(js, indent=1, default=str))
    reg = Registry(SCRIPT)
    reg.add("s4j3_dc_bidirectional", "Decision 105 b: one-way DC links made bidirectional (" + ", ".join(led["one_way_made_bidirectional"]) + "; p_min_pu 0 -> -1; with "
            "transmission_losses = pypsa_eur split into a lossy forward / reverse pair, without losses p_min_pu = -1)", "bidirectional", "flag", "B", "S4J instruction S4J-3", LOC,
            INSTRUCTION_SHA, decision_ref="105", status="REFERENCE_ONLY")
    reg.add("s4j3_b2b_follows_dc", "Decision 105 b: converter-station B2B (DC bus with exactly one DC link and one B2B: " + ", ".join(f"{p['b2b']} at {p['dc_bus']}" for p in led["pairs"])
            + ") extendable at no capital cost, B2B p_nom - existing = DC p_nom - existing (hook research_b2b_follows_dc), bidirectional, lossless; the increment form keeps the "
            "existing 2,000 MW because the DC buses carry generation candidates whose only path to the AC grid is the B2B. Other structures reported: "
            + "; ".join(f"{r['dc_bus']} ({r['reason']})" for r in led["reported"]), "table", "flag", "B", "derived (scripts_project/s4j_3_data.py)",
            "research_inputs/corridors/DC_CONVERTERS_S4J3.csv", sha256(OUT), decision_ref="105", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4j_3.csv")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
    print(T[["kind", "name", "bus0", "bus1", "direction_before", "direction_after", "p_nom", "p_nom_max", "action"]].to_string()); print(json.dumps(mr))


if __name__ == "__main__":
    main()
