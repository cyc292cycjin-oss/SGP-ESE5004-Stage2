"""V3 supplement 02: registered batch definitions after X1b, from the builds of results_project/v3/builds_x1b. Run table, schedule, limits (RUN_PLAN_SCREEN_V3.md). Writes batch_def/BATCH_DEF_365x24h.json (five runs) and BATCH_DEF_2920x3h.json."""
import hashlib, json
from pathlib import Path
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_x1b")
D = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/batch_def")
T16 = "formal_barrier_1e6_t16"; BUILD = "4df45b569ff314e710a75ed70c4d1e381474844e"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
# v2 screening, DFX_REPORT_PHASE4.md: objectives of V1 and V2
V2_I, V2_D = 270785244510.0, 285400557543.0


def reg(files):
    return {k: sha(f) for k, f in files.items()}, {k: f.stat().st_size for k, f in files.items()}


f365 = {"integrated_365_24h_unsolved.nc": M / "integrated/integrated_365_24h_unsolved.nc", "no_new_xb_365_24h_unsolved.nc": M / "no_new_xb/no_new_xb_365_24h_unsolved.nc", "disconnected_365_24h_unsolved.nc": M / "disconnected/disconnected_365_24h_unsolved.nc",
        "bridge_160_162_365_24h_unsolved.nc": M / "bridge_160_162/integrated_365_24h_unsolved.nc", "bridge_160_164_365_24h_unsolved.nc": M / "bridge_160_164/integrated_365_24h_unsolved.nc"}
s, b = reg(f365)
run = lambda sc, base, costs, role: dict(scenario=sc, base=base, set="", profile=T16, costs=costs, role=role)
d = dict(note="V3 365x24h screening after X1b (RUN_PLAN_SCREEN_V3.md); copied into the package as BATCH_DEF.json", build_commit=BUILD, registered_sha=s, registered_bytes=b,
         runs=dict(V1=run("integrated", "integrated_365_24h", "integrated", "本批参照（v3 一体化）、Owen 分摊"), V2=run("no_new_xb", "no_new_xb_365_24h", "integrated", "本批参照（v3 no_new_xb）、B6 = V2 − V1"),
                   V3=run("disconnected", "disconnected_365_24h", "disconnected", "存量与专线的价值 = V3 − V2（第 174 项）"), V4=run("integrated", "bridge_160_162_365_24h", "integrated", "修订桥：第 160–162 项"), V5=run("integrated", "bridge_160_164_365_24h", "integrated", "修订桥：第 160–164 项")),
         schedule=[["1", ["V1"], ["V2"]], ["2", ["V4"], ["V5"]], ["3", ["V3"], []]], time_limit_s=dict(V1=21600, V2=21600, V3=10800, V4=21600, V5=21600), need_disk_gb=90,
         bridge=dict(v2_integrated_objective_eur=V2_I, v2_disconnected_objective_eur=V2_D, steps=[["V4", "160-162"], ["V5", "160-164"], ["V1", "all"]]))
(D / "BATCH_DEF_365x24h.json").write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
f2920 = {"integrated_2920_3h_unsolved.nc": M / "integrated/integrated_2920_3h_unsolved.nc", "no_new_xb_2920_3h_unsolved.nc": M / "no_new_xb/no_new_xb_2920_3h_unsolved.nc"}
s, b = reg(f2920)
old = json.loads((D / "BATCH_DEF_2920x3h.json").read_text(encoding="utf-8")); old.update(build_commit=BUILD, registered_sha=s, registered_bytes=b)
(D / "BATCH_DEF_2920x3h.json").write_text(json.dumps(old, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: (v[:8], d["registered_bytes"][k]) for k, v in d["registered_sha"].items()}, indent=0)); print(old["registered_bytes"], old["registered_sha"])
for k in ("integrated", "disconnected", "bridge_160_162", "bridge_160_164"):
    r = json.loads((M / k / f"{'disconnected' if k == 'disconnected' else 'integrated'}_BUILD_RECEIPT.json").read_text()); print(k, r["code_sha"][:8], r["daily_network"]["sha256"][:8], r["daily_network"]["snapshots"], r.get("config_overrides"))
print(len({sha(M / k / "costs_active_research.csv") for k in ("integrated", "bridge_160_162", "bridge_160_164")}), "distinct cost tables of the integrated builds", sha(M / "disconnected/costs_active_research.csv")[:8], sha(M / "integrated/costs_active_research.csv")[:8])
v = json.loads((M / "no_new_xb/no_new_xb_365_24h_VARIANT_RECEIPT.json").read_text()); print("variant", v["base"]["sha256"][:8], v["output"]["sha256"][:8])
