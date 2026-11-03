"""V3 supplement 07 (review EVDIAG section 2.1 item 6): registered definition of the three-run rerun (V1 -> V2 -> V3) on the networks of results_project/v3/builds_dmax.
Writes batch_def/BATCH_DEF_365x24h_dmax.json; BATCH_DEF_365x24h.json (five runs of the first screening) and BATCH_DEF_2920x3h.json are not touched (the 2920x3h networks are byte-identical).
Run table, roles, profile, limits as RUN_PLAN_SCREEN_V3.md sections 1 and 3; schedule: phase 1 V1 | V2, phase 2 V3 (one lane below 33 cores: V1 -> V2 -> V3).
The revision bridge of the runner keeps only the step v2 -> all; the full bridge v2 -> V4 -> V5 -> new V1 is computed locally with V4 / V5 of the first screening (review section 2.1 item 6)."""
import hashlib, json
from pathlib import Path
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_dmax")
D = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/batch_def")
T16 = "formal_barrier_1e6_t16"; BUILD = json.loads((M / "integrated/integrated_BUILD_RECEIPT.json").read_text())["code_sha"]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
first = json.loads((D / "BATCH_DEF_365x24h.json").read_text(encoding="utf-8"))   # v2 objectives (DFX_REPORT_PHASE4.md) and the registered limits of the first screening
files = {"integrated_365_24h_unsolved.nc": M / "integrated/integrated_365_24h_unsolved.nc", "no_new_xb_365_24h_unsolved.nc": M / "no_new_xb/no_new_xb_365_24h_unsolved.nc", "disconnected_365_24h_unsolved.nc": M / "disconnected/disconnected_365_24h_unsolved.nc"}
runs = {k: first["runs"][k] for k in ("V1", "V2", "V3")}
d = dict(note="V3 365x24h screening rerun after decision 182 (supplement 07, daily max of the Store e_min_pu): V1 -> V2 -> V3 (RUN_PLAN_SCREEN_V3.md section 10); copied into the package as BATCH_DEF.json",
         build_commit=BUILD, registered_sha={k: sha(f) for k, f in files.items()}, registered_bytes={k: f.stat().st_size for k, f in files.items()}, runs=runs,
         schedule=[["1", ["V1"], ["V2"]], ["2", ["V3"], []]], time_limit_s={k: first["time_limit_s"][k] for k in runs}, need_disk_gb=first["need_disk_gb"],
         bridge=dict(v2_integrated_objective_eur=first["bridge"]["v2_integrated_objective_eur"], v2_disconnected_objective_eur=first["bridge"]["v2_disconnected_objective_eur"], steps=[["V1", "all"]]))
assert all(r["base"] + "_unsolved.nc" in files for r in runs.values()) and d["time_limit_s"] == {"V1": 21600, "V2": 21600, "V3": 10800}
(D / "BATCH_DEF_365x24h_dmax.json").write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: (v, d["registered_bytes"][k]) for k, v in d["registered_sha"].items()}, indent=0), BUILD)
for k in ("integrated", "disconnected"):
    r = json.loads((M / k / f"{k}_BUILD_RECEIPT.json").read_text()); print(k, r["code_sha"][:8], r["daily_network"]["sha256"][:8], r["daily_network"]["snapshots"], r.get("config_overrides"))
v = json.loads((M / "no_new_xb/no_new_xb_365_24h_VARIANT_RECEIPT.json").read_text()); print("variant", v["base"]["sha256"][:8], v["output"]["sha256"][:8])
