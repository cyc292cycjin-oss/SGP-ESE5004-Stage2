"""S4G-0 data: registry fragment s4g_0 - the user answers (2026-10-17 18:47 / 18:49 SGT) to the four decision items of the S4F report section 7.

    python scripts_project/s4g_0_data.py
"""
from __future__ import annotations

from d1_common import REG_DIR, Registry

SCRIPT = "scripts_project/s4g_0_data.py"
INSTRUCTION_SHA = "2fd959e9134804a51aecc68b252b2ebe966813e65ed7dabd945ad3953a0d915c"
SRC = "S4G instruction v1 2026-10-17 18:55 SGT, section 'answers to S4F report section 7' (user decisions 2026-10-17 18:47 / 18:49 SGT)"
LOC = "work/p1_step4g_20261017/S4G_CLAUDE_CODE_INSTRUCTION.md"
ANSWERS = [
    ("s4g_answer_readjust_lines", "S4F section 7 item 1: all 19 cross-border AC lines changed by the author's readjust_existing_interconnections get electrical "
     "parameters consistent with their capacity through the line-type relation (decision 98, S4G-1): num_parallel = s_nom / (sqrt3 x v_nom x i_nom), x / r / b "
     "recomputed from the line type; not only the 16 lines in AC loops; no re-clustering - the cluster-member issue is a registered limitation (grade C)",
     "all_19_line_type_relation", "98,97"),
    ("s4g_answer_apg_plans_rule", "S4F section 7 item 2: apg_plans rule confirmed - plan cap = larger of total_MW and the 2040 projection, #16 incl. merged #5, projects "
     "without a number keep the PyPSA-Eur limit (decision 99 a)", "confirmed", "99,96"),
    ("s4g_answer_lao_th_store", "S4F section 7 item 3: in the Lao transit existing_port sensitivity, LA nodes whose transit ends at a Thai port get a link into the Thai "
     "national store by the same rule as decision 97 c (decision 99 b, S4G-2); main run unchanged", "existing_port_only", "99,97"),
    ("s4g_answer_cloud_package", "S4F section 7 item 4: the S4F cloud package is void; the package rebuilt in S4G is the one to use (decision 99 c)",
     "s4f_package_void_use_s4g", "99"),
]


def main():
    reg = Registry(SCRIPT)
    for pid, desc, val, dec in ANSWERS:
        reg.add(pid, desc, val, "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref=dec, status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4g_0.csv")


if __name__ == "__main__":
    main()
