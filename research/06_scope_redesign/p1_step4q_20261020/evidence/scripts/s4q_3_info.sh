#!/bin/bash
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python; E=/home/jin/wt_s4q_20261020/research/06_scope_redesign/p1_step4q_20261020/evidence/s4q_3
$PY - $E <<'P'
import json, sys, glob
E = sys.argv[1]
for t in ("t8", "t16"):
    p = json.load(open(f"/home/jin/s4q_local/judge_shadow/{t}/integrated/PRECISION.json"))
    print(t, "shadow ref:", p["reference"]["source"][:70], "| VN thr", p["c_prices"]["country_check"]["VN"]["threshold_bn"], "| history", [h["reference_source"][:30] for h in p.get("grade_history", [])])
    J = json.load(open(f"{E}/S4Q3_JUDGE.json"))["paths"][t]
    for sc, v in J["c1_s4m2_reference"].items():
        print("  C1", sc, "a", v["a_returned_difference_bn"], v["a_returned_relative"], "b rows_over", v["b_rows_over_budget"], "foc_eur", round(v["b_first_order_cost_eur"] or 0, 1), "b worst", v["b_worst_country"], "c worst", v["c_worst_country_S_plus_R"], "dominant", v["b_biomass_BN_SG_VN_dominant"], "gates_fail", (v["gates_information"] or {}).get("failing"))
    C = json.load(open(f"{E}/COMPARE_{t}_VS_S4M2.json"))
    for sc, inf in C["information"].items():
        print("  ", sc, {car: (round(v["mean_abs_diff"], 6), round(v["max_abs_diff"], 6), v["buses"]) for car, v in inf["nodal_price_bus_mean_differences"].items()})
        print("     bio", {c: (v["ref"], v["cal"], v["diff"]) for c, v in inf["solid_biomass_shadow_price_eur_per_mwh"].items()})
        cd = {c: v["diff"] for c, v in inf["country_co2_shadow_price_raw_dual"].items() if v["diff"] is not None}
        print("     co2 src:", inf["co2_reference_source"][:90], "| max|diff|", max((abs(x) for x in cd.values()), default=None), "| n", len(cd), "| ref sample", {c: v["ref"] for c, v in list(inf["country_co2_shadow_price_raw_dual"].items())[:3]})
    print("   B6", C["B6_bn_eur"], "NZE-int", C["nze_minus_integrated_bn_eur"])
    print("   gates excl B12", {sc: (C["runs"][f"cal_{sc}"]["all_passed_solver_tolerances_excl_B12"], C["runs"][f"cal_{sc}"]["failed_gates_excluding_B12"], C["runs"][f"ref_{sc}"]["failed_gates_excluding_B12"]) for sc in ("integrated","disconnected","integrated_nze")})
cons = json.load(open(f"{E}/S4Q3_JUDGE.json"))["consistency"]
for t, v in cons.items():
    print("consistency", t, {sc: (x["same_network_as_S4M2"], x["truncated_to"], x["parameters_equal_profile"], x["time_limit"], x["s4m2_time_limit"], x["retry"], x["optimize_calls"]) for sc, x in v.items()})
P
