"""S4J-0 data: registry fragment s4j_0 - the user answers (2026-10-18 19:44 SGT) to the S4I report section 5 (pre-cloud static audit, PR #33):
K1 -> decision 104; U1, U2 -> decision 105; K2, U3 -> decision 106 a, b; R1-R11 registered at the time S4I suggested (decision 106 c); the
coalition compute estimate as the basis of item 14 (decision 106 d); and the S4J scope rule (only decisions 104-106).

    python scripts_project/s4j_0_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4j_0_data.py"
INSTRUCTION_SHA = "c20957448c69128c05eaf4e271bcca7f98eecc7ccd3121cd37f3581daff3348f"
SRC = "S4J instruction v1 2026-10-18 19:50 SGT, section S4J-0 (user decisions 104-106 confirmed 2026-10-18 19:44 SGT)"
LOC = "work/p1_step4j_20261018/S4J_CLAUDE_CODE_INSTRUCTION.md"
S4I = "research/06_scope_redesign/p1_step4i_20261018/S4I_REPORT.md"
S4I_SRC = "S4I report section 5 (pre-cloud static audit of the S4H package, PR #33)"
ANSWERS = [
    ("s4j_answer_k1_nonindustrial", "S4I K1 (Viet Nam non-industrial electricity load 30.0 TWh: Astar minus the ratio-method industrial electricity) -> decision 104: "
     "the 2050 non-industrial electricity load of every country = the sum of the demand-table sectors that are not modelled separately (residential, commercial, "
     "agriculture and other ...); the Astar curve only gives the hourly shape (normalised to the annual total, then scaled); switch "
     "research.demand.nonindustrial_electricity: table_sectors | astar_residual (S4J-1)", "table_sectors", "104"),
    ("s4j_answer_u1_losses", "S4I U1 (no transmission losses) -> decision 105 a: PyPSA-Eur v2025.07.0 defaults - AC lines transmission_losses: 2 (piecewise linear), "
     "DC links 0.98 x 0.977^(L/1000) as lossy bidirectional link pairs, H2 / gas pipelines with compression electricity per 1000 km, CO2 pipelines without loss, "
     "distribution-grid efficiency 0.97 not used (S4I R10); domestic and cross-border, both scenarios, stock and candidates alike; switch "
     "research.network.transmission_losses: pypsa_eur | none (S4J-2)", "pypsa_eur", "105"),
    ("s4j_answer_u2_th_my_dc", "S4I U2 (TH-MY DC Khlong Ngae - Gurun one-way, fixed 2,000 MW B2B converters at both ends) -> decision 105 b: the link becomes "
     "bidirectional (lossy bidirectional with S4J-2; p_min_pu = -1 without losses); the fixed B2B converters follow the DC link extension at no extra cost "
     "(the DC link cost includes the converter pair), same direction as the link; other DC links with the same structure handled alike, others reported (S4J-3)",
     "bidirectional;b2b_follows_link", "105"),
    ("s4j_answer_k2_licence", "S4I K2 (academic WLS licence: at most 2 sessions, tokens kept >= 5 min) -> decision 106 a: run_365x24h.sh drops lanes3 (refused with the "
     "reason), lanes2 waits >= 5 min at start and >= 5 min before the next run in a lane; serial recommended for the first batch; deploy steps, resource estimate "
     "and pre-cloud checklist without the three-lane mode (S4J-4)", "drop_lanes3;lanes2_5min_gaps;serial_first", "106"),
    ("s4j_answer_u3_gnu_time", "S4I U3 (run_365x24h.sh needs /usr/bin/time, the preflight does not check it) -> decision 106 b: preflight.sh checks /usr/bin/time and "
     "fails with the install command (apt-get install -y time) when it is missing (S4J-4)", "preflight_checks_time", "106"),
    ("s4j_answer_coalition_estimate", "S4I section 4 (D) -> decision 106 d: the connected-coalition compute estimate is the basis of item 14 - 383 connected coalitions "
     "(members >= 2); 365x24h serial 235-332 h (9.8-13.8 days, pessimistic 20.2 days), two lanes 6.1-9.0 days; 2920x3h serial 139-297 days; at most two lanes "
     "with the academic licence; the coalition scope stays with item 14 (decision 97 f)", "basis_item_14", "106,14"),
    ("s4j_scope_rule", "S4J scope: only decisions 104-106 are implemented; other findings go to the report section 'found but not handled' (symptom, countries and "
     "magnitude, feasibility / numerical impact, recommended time) without model change unless a stop condition is met; after S4J the model state is the version "
     "of the first formal runs unless the user decides otherwise", "only_104_106", "104,105,106"),
]
REGISTERED = [   # S4I report section 5 'registration' table: (id, finding, suggested time)
    ("R1", "128 coal / lignite / oil buses with one connection only (supply, no consumption, flow 0)", "before_delivery_cleanup"),
    ("R2", "10 pairs 'stock line + S4H2 reference candidate' in parallel on the same bus pair, both extendable (2 x 20 GW); stock num_parallel 0.018-0.18, "
     "reactance 6-57 times the candidate", "after_first_results"),
    ("R3", "94 identical biomass-to-methanol links (country biomass bus -> regional methanol bus): LP degeneracy, not an error", "before_delivery_cleanup"),
    ("R4", "zero-cap candidates with old parameters (61 pumping hydro, 86 PHS at 0.75, 71 ror without profile, geothermal p_max_pu 1), all p_nom_max = 0", "before_delivery_cleanup"),
    ("R5", "38 all-zero domestic-shipping methanol loads, 3 all-zero offwind-dc profiles (cap 0)", "before_delivery_cleanup"),
    ("R6", "existing onshore wind (2,267 MW) capacity factor 0.009-0.12 vs Ember 0.24-0.36 (about 3.5 TWh/a less)", "sensitivity"),
    ("R7", "nuclear and SMR p_max_pu 1.0; PyPSA-Eur uses data/nuclear_p_max_pu.csv (not in the repository)", "sensitivity"),
    ("R8", "carbon-balance exceptions by design: 218 feedstock links on the territorial basis (decision 56), 19 gas-field venting links (S2-0)", "method_note_before_delivery"),
    ("R9", "after scaling the largest right-hand side 6.1e8 (annual domestic gas cap in MWh), span 3e12; matrix, objective and bounds within the warning limits",
     "after_first_results_rhs_range"),
    ("R10", "distribution-grid efficiency 1.0 (PyPSA-Eur 0.97); no low-voltage load, affects rooftop PV / home battery only", "sensitivity"),
    ("R11", "5 existing cross-border gas pipelines one-way (export direction); existing GEM pipelines extendable at their real length, dearer than parallel candidates",
     "after_first_results"),
]


def main():
    reg = Registry(SCRIPT)
    for pid, desc, val, dec in ANSWERS:
        reg.add(pid, desc, val, "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref=dec, status="REFERENCE_ONLY")
    s4i_sha = sha256(ROOT / S4I)
    for rid, finding, when in REGISTERED:
        reg.add(f"s4j_registered_{rid.lower()}", f"Decision 106 c: S4I {rid} registered at the time S4I suggested - {finding}", when, "flag", "B", S4I_SRC, S4I, s4i_sha,
                decision_ref="106", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4j_0.csv")
    print("registry fragment s4j_0 written:", len(ANSWERS) + len(REGISTERED), "rows")


if __name__ == "__main__":
    main()
