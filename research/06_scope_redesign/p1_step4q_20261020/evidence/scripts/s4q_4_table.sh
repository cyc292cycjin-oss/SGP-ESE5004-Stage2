#!/bin/bash
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; D=/home/jin/wt_s4q_20261020/research/06_scope_redesign/p1_step4q_20261020
$PY - $D <<'P'
import json, sys, re
D = sys.argv[1]; J = json.load(open(f"{D}/evidence/s4q_3/S4Q3_JUDGE.json"))
for t in ("t8", "t16"):
    C = json.load(open(f"{D}/evidence/s4q_3/COMPARE_{t}_VS_S4M2.json")); st = open(f"{D}/evidence/s4q_2/{t}/STATUS.txt").read()
    for sc in ("integrated", "disconnected", "integrated_nze"):
        r, a = C["runs"][f"cal_{sc}"], C["runs"][f"ref_{sc}"]; e = J["paths"][t]["efficiency_information"][sc]
        wall = re.search(rf"^RUN_{sc}:\w+:(\d+)s", st, re.M).group(1); c1 = re.search(rf"^PRECISION_{sc}:(.*?):exit", st, re.M).group(1)
        print(f"{t} {sc}: obj {r['objective']:.4f} A {a['objective']:.4f} diff_eur {r['objective']-a['objective']:.1f} rel {r['objective']/a['objective']-1:.3e} | it {r['barrier_iterations']}/{a['barrier_iterations']} bs {r['barrier_seconds']}/{a['barrier_seconds']} wu {r['barrier_work_units']}/{a['barrier_work_units']} ratio_it {e['ratio_iterations']:.3f} ratio_bs {e['ratio_barrier_seconds']:.3f} ratio_wu {e['ratio_work_units']:.3f} | solve_s {r['solve_seconds']:.1f}/{a['solve_seconds']:.1f} wall {wall} rss {r['peak_rss_gib']:.2f}/{a['peak_rss_gib']:.2f} | B16 {r['B16_relative_error']:.2e} | kkt {e['kkt_relative_gap']:.2e} | pipeC1 {c1}")
    k3 = J["paths"][t]["criterion_3"]; k4 = J["paths"][t]["criterion_4"]
    w3 = max(k3.items(), key=lambda kv: abs(kv[1]["change_bn"]) / kv[1]["tolerance_bn"]); w4 = max(k4.items(), key=lambda kv: abs(kv[1]["change_bn"]) / kv[1]["tolerance_bn"])
    print(f"{t} worst c3 {w3[0]} {w3[1]['change_bn']:.2e} / {w3[1]['tolerance_bn']:.4f} = {abs(w3[1]['change_bn'])/w3[1]['tolerance_bn']:.2%}; worst c4 {w4[0]} {w4[1]['change_bn']:.2e} / {w4[1]['tolerance_bn']:.4f} = {abs(w4[1]['change_bn'])/w4[1]['tolerance_bn']:.2%}; maxabs c3 {max(abs(v['change_bn']) for v in k3.values()):.2e} c4 {max(abs(v['change_bn']) for v in k4.values()):.2e}")
    for sc, v in J["paths"][t]["c1_s4m2_reference"].items():
        print(f"   C1 {sc}: a {v['a_returned_difference_bn']*1e9:.0f} EUR rel {v['a_returned_relative']:.2e}; b rows_over {v['b_rows_over_budget']} foc {v['b_first_order_cost_eur']:.0f} EUR worst {v['b_worst_country'][0]} {v['b_worst_country'][1]:.2e}; c worst {v['c_worst_country_S_plus_R'][0]} {v['c_worst_country_S_plus_R'][1]:.2e}; grade {v['grade']['grade']}; accepted {v['acceptance']['accepted']}")
bp = J["between_paths"]
print("between", {sc: (f"{v['rel_diff_t16_vs_t8']:.2e}", f"{v['abs_diff_bn']*1e9:.0f} EUR") for sc, v in bp["objective"].items()}, "max country diff", max(abs(v["diff"]) for v in bp["country_difference_t16_minus_t8_bn"].values()), "max nze", max(abs(v) for v in bp["nze_entity_total_t16_minus_t8_bn"].values()))
P
