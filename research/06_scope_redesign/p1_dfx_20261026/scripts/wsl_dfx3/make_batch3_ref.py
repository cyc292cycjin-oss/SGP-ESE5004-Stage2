"""DFX v3 F6: BATCH3_REFERENCE_VALUES.json for the DFX package (RUN_PLAN_DFX 3.4 items 5-6): the third-batch R1 / R2 (and R3 / R4) objectives,
B6, labels, Owen dual-form allocation (alpha main) and country ledger totals from the third-batch export (M10P cloud results, light pack), plus
the registered first-order prediction (evidence/DFX_FIRST_ORDER.json). Read-only on the sources; writes one JSON into the deliverable folder."""
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


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


s = json.load(open(L / "batch/BATCH3_SUMMARY.json")); fo = json.load(open(FO))
runs = s["runs"]
owen = {rid: json.load(open(L / rid / "m12_owen/OWEN.json")) for rid in ("R1", "R2")}
alloc = {rid: {k: v for k, v in o["allocation_eur"][str(o["alpha_main"])].items() if k != "SHARED"} for rid, o in owen.items()}
led = {rid: ledger_totals(L / rid) for rid in ("R1", "R2")}
main = fo["pairs"]["main (R1 / R2)"]; rob = fo["pairs"]["robustness (R3 / R4, optimal 1e-6)"]
ref = dict(
    source="third batch (M10P, 2026-10-23; light pack 20261023T174135Z_halted/export) + DFX first-order prediction (evidence/DFX_FIRST_ORDER.json, RUN_PLAN_DFX section 4)",
    written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    batch3=dict(runs=dict(integrated="R1", disconnected="R2"), profile={rid: runs[rid]["profile"] for rid in ("R1", "R2", "R3", "R4")},
                objective_eur={rid: runs[rid]["objective"] for rid in ("R1", "R2", "R3", "R4")},
                termination={rid: runs[rid]["termination"] for rid in ("R1", "R2", "R3", "R4")}, labels={rid: runs[rid]["v6"] for rid in ("R1", "R2", "R3", "R4")},
                solve_seconds={rid: runs[rid]["solve_seconds"] for rid in ("R1", "R2", "R3", "R4")}, peak_rss_gib={rid: runs[rid]["peak_rss_gib"] for rid in ("R1", "R2", "R3", "R4")},
                b6_bn=s["B6"]["b6_bn"], b6_eur=s["B6"]["difference"], b6_t16_bn=(runs["R4"]["objective"] - runs["R3"]["objective"]) / 1e9,
                owen_alpha_main=owen["R1"]["alpha_main"], owen_alpha_main_eur=alloc, owen_source={rid: f"export/{rid}/m12_owen/OWEN.json sha256 {sha(L / rid / 'm12_owen/OWEN.json')}" for rid in ("R1", "R2")},
                ledger_total_eur=led, summary_sha256=sha(L / "batch/BATCH3_SUMMARY.json"),
                note="R1 / R2 = profile formal_barrier (Threads 8, suboptimal, ACCEPTED_LAYER2); R3 / R4 = formal_barrier_1e6_t16 (Threads 16, optimal) - the DFX V1 / V2 profile; B6 differs by 0.0001 bn between the pairs"),
    first_order=dict(method="DMD dmd_d5_duals.py envelope method: annual load-weighted dual prices of the third-batch 365x24h runs x (v2 - v1) network loads; INFERENCE (large-change extrapolation)",
                     delta_demand_twh=main["totals"]["d_demand_twh"], delta_c_integrated_bn=main["totals"]["d_cost_integrated_bn_eur"], delta_c_disconnected_bn=main["totals"]["d_cost_disconnected_bn_eur"],
                     delta_b6_bn=main["totals"]["d_b6_bn_eur"], delta_b6_bn_usd=main["totals"]["d_b6_bn_usd"], predicted_b6_bn=main["totals"]["predicted_b6_bn_eur"],
                     robustness_r3_r4=dict(delta_b6_bn=rob["totals"]["d_b6_bn_eur"], predicted_b6_bn=rob["totals"]["predicted_b6_bn_eur"]),
                     by_country_bn={c: v["d_benefit_bn"] for c, v in main["by_country"].items()}, by_country_owen_share_bn={c: v["d_owen_share_bn"] for c, v in main["by_country"].items()},
                     by_class={k: dict(d_demand_twh=v["d_demand_twh"], d_b6_bn=v["d_b6_bn"]) for k, v in main["by_class"].items()},
                     source_sha256=sha(FO), note=fo.get("note")))
OUT.write_text(json.dumps(ref, indent=1) + "\n")
print("written", OUT, OUT.stat().st_size, "bytes; B6", ref["batch3"]["b6_bn"], "b6_t16", ref["batch3"]["b6_t16_bn"], "dB6 first-order", ref["first_order"]["delta_b6_bn"])
print("owen R1 countries", list(alloc["R1"].keys())); print("ledger R1 keys", sorted(led["R1"].keys()))
