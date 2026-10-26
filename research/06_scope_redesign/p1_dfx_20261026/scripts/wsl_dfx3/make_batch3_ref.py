"""DFX v3 F6: BATCH3_REFERENCE_VALUES.json for the DFX package (RUN_PLAN_DFX 3.4 items 5-6; user amendment 2026-10-27): MAIN reference = the
third-batch R3 / R4 (same profile formal_barrier_1e6_t16, optimal); ALTERNATIVE (listed alongside) = R1 / R2 (profile formal_barrier, the values of
the stage reports). Objectives, B6, labels, Owen dual-form allocation (alpha main) and country ledger totals of all four runs from the third-batch
export (M10P cloud results, light pack), plus the registered first-order prediction (evidence/DFX_FIRST_ORDER.json). Read-only on the sources."""
import hashlib
import json
import sys
import time
from pathlib import Path

WT = Path("/home/jin/wt_dfx_v3_20261026")
sys.path.insert(0, str(WT / "scripts_project"))
from m10_batch3_summary import ledger_totals  # noqa: E402

L = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10_20261022/cloud_results/20261023T174135Z_halted/light_unpacked/export")
FO = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/evidence/DFX_FIRST_ORDER.json")
OUT = WT / "research/06_scope_redesign/p1_dfx_20261026/BATCH3_REFERENCE_VALUES.json"
RIDS = ("R1", "R2", "R3", "R4")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


s = json.load(open(L / "batch/BATCH3_SUMMARY.json")); fo = json.load(open(FO))
runs = s["runs"]
owen = {rid: json.load(open(L / rid / "m12_owen/OWEN.json")) for rid in RIDS}
alloc = {rid: {k: v for k, v in o["allocation_eur"][str(o["alpha_main"])].items() if k != "SHARED"} for rid, o in owen.items()}
led = {rid: ledger_totals(L / rid) for rid in RIDS}
main = fo["pairs"]["main (R1 / R2)"]; rob = fo["pairs"]["robustness (R3 / R4, optimal 1e-6)"]
b6_main = (runs["R4"]["objective"] - runs["R3"]["objective"]) / 1e9; b6_alt = s["B6"]["b6_bn"]
ref = dict(
    source="third batch (M10P, 2026-10-23; light pack 20261023T174135Z_halted/export) + DFX first-order prediction (evidence/DFX_FIRST_ORDER.json, RUN_PLAN_DFX section 4); main reference R3 / R4 per the user amendment of 2026-10-27, R1 / R2 alongside",
    written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    batch3=dict(main_runs=dict(integrated="R3", disconnected="R4"), alternative_runs=dict(integrated="R1", disconnected="R2"),
                profile={rid: runs[rid]["profile"] for rid in RIDS}, objective_eur={rid: runs[rid]["objective"] for rid in RIDS},
                termination={rid: runs[rid]["termination"] for rid in RIDS}, labels={rid: runs[rid]["v6"] for rid in RIDS},
                solve_seconds={rid: runs[rid]["solve_seconds"] for rid in RIDS}, peak_rss_gib={rid: runs[rid]["peak_rss_gib"] for rid in RIDS},
                b6_bn=b6_main, b6_eur=runs["R4"]["objective"] - runs["R3"]["objective"], b6_alternative_bn=b6_alt, b6_alternative_eur=s["B6"]["difference"],
                owen_alpha_main=owen["R3"]["alpha_main"], owen_alpha_main_eur=alloc, owen_usable={rid: owen[rid].get("usable_for_allocation") for rid in RIDS},
                owen_source={rid: f"export/{rid}/m12_owen/OWEN.json sha256 {sha(L / rid / 'm12_owen/OWEN.json')}" for rid in RIDS},
                ledger_total_eur=led, summary_sha256=sha(L / "batch/BATCH3_SUMMARY.json"),
                note="main R3 / R4 = formal_barrier_1e6_t16 (Threads 16, optimal, ACCEPTED_LAYER2) - the DFX V1 / V2 profile; alternative R1 / R2 = formal_barrier (Threads 8, suboptimal, ACCEPTED_LAYER2), the values used in the stage reports; B6 differs by 0.0003 bn between the pairs"),
    first_order=dict(method="DMD dmd_d5_duals.py envelope method: annual load-weighted dual prices of the third-batch 365x24h runs x (v2 - v1) network loads; INFERENCE (large-change extrapolation)",
                     delta_demand_twh=main["totals"]["d_demand_twh"], delta_c_integrated_bn=main["totals"]["d_cost_integrated_bn_eur"], delta_c_disconnected_bn=main["totals"]["d_cost_disconnected_bn_eur"],
                     delta_b6_bn=main["totals"]["d_b6_bn_eur"], delta_b6_bn_usd=main["totals"]["d_b6_bn_usd"],
                     predicted_b6_bn=b6_main + main["totals"]["d_b6_bn_eur"], predicted_b6_alternative_bn=main["totals"]["predicted_b6_bn_eur"],
                     prices="R1 / R2 duals (main pair of the prediction); R3 / R4 duals give the same delta to 3 decimals (robustness)",
                     robustness_r3_r4=dict(delta_b6_bn=rob["totals"]["d_b6_bn_eur"], predicted_b6_bn=b6_main + rob["totals"]["d_b6_bn_eur"]),
                     by_country_bn={c: v["d_benefit_bn"] for c, v in main["by_country"].items()}, by_country_owen_share_bn={c: v["d_owen_share_bn"] for c, v in main["by_country"].items()},
                     by_class={k: dict(d_demand_twh=v["d_demand_twh"], d_b6_bn=v["d_b6_bn"]) for k, v in main["by_class"].items()},
                     source_sha256=sha(FO), note=fo.get("note")))
OUT.write_text(json.dumps(ref, indent=1) + "\n")
print("written", OUT, OUT.stat().st_size, "bytes; B6 main (R4-R3)", b6_main, "alternative (R2-R1)", b6_alt, "dB6 first-order", ref["first_order"]["delta_b6_bn"], "predicted", ref["first_order"]["predicted_b6_bn"])
print("owen usable", ref["batch3"]["owen_usable"]); print("ledger keys", {rid: len(led[rid]) for rid in RIDS})
