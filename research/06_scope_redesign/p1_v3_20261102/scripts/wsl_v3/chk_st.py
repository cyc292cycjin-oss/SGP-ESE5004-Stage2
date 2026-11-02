import json, re
W = "/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102"
M = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds"
d = json.load(open(f"{W}/evidence/V3_STATIC_CHECK.json"))
print("all_structural_passed", d["all_structural_passed"])
for k in ("gate_b5_no_new_xb", "gate_b5_no_new_xb_365", "scenario_difference_2920", "scenario_difference_365", "structure_vs_v2", "demand_vs_table"):
    print(k, json.dumps(d[k])[:640])
for k in ("integrated_2920", "no_new_xb_2920", "integrated_365", "no_new_xb_365"):
    z = d[k]
    print(k, dict(weights=z["weights"], hours=z["hours"], orphans=z["orphan_count"], dup=sum(z["duplicates"].values()), eff=z["efficiency_range"], p_max=z["p_max_pu_ok"], ships=z["ship_links"], transit=z["transit_links"], nb=z["national_buses"], aseanliq=z["asean_liquid_buses"], meters=z["fossil_oil_meters"], ev=z["ev"], slack=z["slack_generators"]))
for s, r, t in (("integrated", "2920_3h", 56), ("no_new_xb", "2920_3h", 56), ("integrated", "365_24h", 0), ("no_new_xb", "365_24h", 0)):
    e = open(f"{M}/lp_{s}_{r}_t{t}/err.log").read(); o = open(f"{M}/lp_{s}_{r}_t{t}/out.log").read().strip().splitlines()[-1]
    j = json.loads(o)["lp"]
    print(s, r, t, j["num_col"], j["num_row"], j["nnz"], "rss_gib", round(int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", e).group(1)) / 2**20, 2), "secs", re.search(r"Elapsed.*: (\S+)", e).group(1))
