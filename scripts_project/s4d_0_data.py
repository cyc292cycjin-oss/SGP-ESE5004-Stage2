"""S4D-0 data: registry fragment s4d_0 - the user answers (2026-10-17) to the ten decision items of the S4C report section 8, working principle 8, and
the CO2 chain inventory of the S4C-6 integrated build (capture buffers, national sequestration, extra-ASEAN export, CO2 pipelines per node / country).

    python scripts_project/s4d_0_data.py --network <S4C-6 integrated_2920_3h_unsolved.nc> --coastal research_inputs/co2_v5/COASTAL_NODES_S4D1.csv
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4d_0_data.py"
INSTRUCTION_SHA = "a35fa7d52c0d645830562e57fb242563b864994682eeb1ce6a2a8d59f73b2586"
SRC = "S4D instruction v1 2026-10-17 10:35 SGT, section 'answers to S4C report section 8' (user decisions 2026-10-17 09:45-10:26 SGT)"
ANSWERS = [
    ("s4d_answer_cloud_solver_profile", "S4C section 8 item 1: cloud solver profile A formal_barrier (with Kirchhoff row normalisation); deploy documents and run commands state "
     "--solver-profile formal_barrier; the run script keeps the required / no-default check", "formal_barrier", "84"),
    ("s4d_answer_extra_asean_cost", "S4C section 8 item 2: extra-ASEAN CO2 storage keeps 40.75 EUR2020/t in the main run; +-50 % is a first-batch sensitivity after the first cloud run, "
     "both scenarios; registered, not run in S4D", "40.75_main;pm50_first_batch", "89"),
    ("s4d_answer_items_3_4", "S4C section 8 items 3 and 4 (extra-ASEAN storage replacing cross-border CO2 pipelines; Lao landlocked transit) superseded by decisions 92 and 93", "superseded", "92,93"),
    ("s4d_answer_line_s_residual", "S4C section 8 item 5: the Line-s stationarity residual is accepted and registered as a limitation; its effect on the country ledgers is quantified "
     "in the S4D-3 identity check", "accepted_limitation", "84,91"),
    ("s4d_answer_discount_rate", "S4C section 8 item 6: uniform discount rate 0.07 kept; country_specific implemented only", "uniform_0.07", "90"),
    ("s4d_answer_bunker_fossil_zero", "S4C section 8 item 7: fossil jet fuel 0 in the bunker account accepted (decision 88)", "accepted", "88"),
    ("s4d_answer_lng", "S4C section 8 item 8: regasification adder stays DATA_PENDING; the LNG terminal cap (2.5 x) still binds and is a first-batch sensitivity (registered, not run)",
     "data_pending;first_batch_sensitivity", "17,72"),
    ("s4d_answer_hydro_b_limitation", "S4C section 8 item 9: hydro option B limitations accepted (one annual CF per country; Ember total only)", "accepted", "83"),
    ("s4d_answer_cloud_mode", "S4C section 8 item 10: cloud run mode and authorisation decided after S4D and its review", "deferred", "87"),
    ("working_principle_8", "Working principle 8 'the model is built to answer the question': every modelling decision is checked for whether it systematically shifts costs to or "
     "away from particular countries, and whether the outputs suffice to support the allocation of cost responsibility among countries", "principle_8", "91"),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--coastal", type=Path, required=True); a = ap.parse_args()
    reg = Registry(SCRIPT)
    for pid, desc, val, dec in ANSWERS:
        reg.add(pid, desc, val, "flag", "B", SRC, "work/p1_step4d_20261017/S4D_CLAUDE_CODE_INSTRUCTION.md", INSTRUCTION_SHA, decision_ref=dec, status="REFERENCE_ONLY")
    # CO2 chain inventory (S4D-0 item 2)
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(a.network)); t = pd.read_csv(a.coastal)
    caps = n.meta["research_co2_storage"]["caps_t_per_year"]
    inv = {}
    for c, x in t.groupby("country"):
        inv[c] = dict(nodes=int(len(x)), capture_buffers=int(x.co2_buffer.sum()), national_sequestration_cap_mt_per_year=float(caps.get(c, 0.0)) / 1e6,
                      sequestration_links=int(x.domestic_sequestration_link.sum()), extra_asean_export_links=int(x.extra_asean_export_link.sum()),
                      co2_pipeline_candidate_ends=int(x.co2_pipeline_candidates.sum()), cross_border_co2_pipeline_ends=int(x.co2_pipeline_cross_border.sum()),
                      coastal_by_rule=int(x.coastal.sum()))
    out = ROOT / "research_inputs/co2_v5/CO2_CHAIN_INVENTORY_S4D0.json"
    out.write_text(json.dumps(dict(network=str(a.network), network_sha256=sha256(a.network), coastal_table_sha256=sha256(a.coastal), by_country=inv,
                                   totals=dict(buffers=int(t.co2_buffer.sum()), cross_border_co2_pipelines=int((n.links.carrier.eq("CO2 pipeline") & n.links.border_class.eq("cross_border")).sum()),
                                               domestic_co2_pipelines=int((n.links.carrier.eq("CO2 pipeline") & n.links.border_class.eq("domestic")).sum()),
                                               extra_asean_links=int((n.links.carrier == "CO2 export extra-ASEAN").sum()), sequestration_stores=int((n.stores.carrier == "co2 sequestered").sum()))),
                              indent=1))
    reg.add("co2_chain_inventory_s4d0", "S4D-0 item 2: CO2 chain inventory of the S4C-6 integrated build per country (capture buffers, national sequestration caps and links, extra-ASEAN export "
            "links, CO2 pipeline candidates incl. cross-border) - research_inputs/co2_v5/CO2_CHAIN_INVENTORY_S4D0.json", "inventory", "flag", "B", "S4C-6 integrated build",
            str(out.relative_to(ROOT)), sha256(out), decision_ref="92,93", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4d_0.csv")
    print(json.dumps(inv, indent=0)[:2500])


if __name__ == "__main__":
    main()
