"""S4H-0 data: registry fragment s4h_0 - the user answers (2026-10-17 21:29 SGT) to the four decision items of the S4G report section 7, and the
scope rule of S4H (only decisions 100 and 101; other findings recorded, not changed).

    python scripts_project/s4h_0_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, Registry

SCRIPT = "scripts_project/s4h_0_data.py"
INSTRUCTION_SHA = "a029bd64cef2ae1b84aec4ebc186ede21630283d17153df9aed4ae32d1fd33bd"
SRC = "S4H instruction v1 2026-10-17 21:40 SGT, section 'answers to S4G report section 7' (user decisions 2026-10-17 21:29 SGT)"
LOC = "work/p1_step4h_20261017/S4H_CLAUDE_CODE_INSTRUCTION.md"
ANSWERS = [
    ("s4h_answer_la_vn_stock", "S4G section 7 item 1: LA-VN stock = 0 by the AIMS grid-to-grid basis; the four clustered lines become zero-capacity candidate lines; "
     "dedicated IPP export lines not modelled and not downloaded - grade C limitation with an order-of-magnitude estimate (decision 100, S4H-1)", "aims_zero", "100,98"),
    ("s4h_answer_candidate_reactance", "S4G section 7 item 2: reference num_parallel of the zero-capacity AC candidate lines = 1; APG17 corrected by the decision-98 "
     "line-type relation; every adjacent country pair with an AC stock line gets at least one reference-reactance candidate line (decision 101, S4H-2)",
     "one_circuit;apg17_line_type;complete_pairs", "101,98,94"),
    ("s4h_answer_numerical_risk", "S4G section 7 item 3: the extreme LA-VN reactance is removed by decision 100; reviewed in the S4H smoke", "by_decision_100", "100"),
    ("s4h_answer_cloud_package", "S4G section 7 item 4: the S4G cloud package is void; the package rebuilt in S4H is the one to use", "s4g_package_void_use_s4h", "100,101"),
    ("s4h_scope_rule", "S4H scope (user note 2026-10-17): only decisions 100 and 101 are implemented; other findings go to the report section 'found but not handled' "
     "(symptom, countries and magnitude, feasibility / numerical impact, recommendation) without model change unless a stop condition is met; after S4H the "
     "model state is the version of the first formal runs unless the user decides otherwise", "only_100_101", "100,101"),
]


def main():
    reg = Registry(SCRIPT)
    for pid, desc, val, dec in ANSWERS:
        reg.add(pid, desc, val, "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref=dec, status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4h_0.csv")


if __name__ == "__main__":
    main()
