"""S4D deliverable: S4D_EVIDENCE.json - light evidence of S4D-0 .. S4D-6 collected from the receipts, summaries, registry and git (no solve).

    python scripts_project/s4d_6_collect_evidence.py --out /mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4d_20261017/S4D_EVIDENCE.json --dist <cloud_package_dist>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results_project/s4d"
CO2 = ROOT / "research_inputs/co2_v5"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jl(p):
    return json.loads(Path(p).read_text())


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--dist", type=Path, required=True); ap.add_argument("--tests", default="")
    a = ap.parse_args()
    import pandas as pd
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    pick = lambda ks: {k: dict(value=reg.at[k, "value"], unit=reg.at[k, "unit"], tier=reg.at[k, "tier"], status=reg.at[k, "status"]) for k in ks if k in reg.index}
    coast = jl(CO2 / "COASTAL_NODES_S4D1_FINAL.json"); routes = jl(CO2 / "CO2_SHIP_ROUTES_S4D2.json"); lao = jl(CO2 / "LAO_TRANSIT_S4D1.json")
    trial = jl(R / "ledger_trial_s4c/S4D3_LEDGER_TRIAL.json"); coal = jl(R / "s4d4/S4D4_COALITION.json"); smoke = jl(R / "s4d5/analysis/S4D5_SMOKE_SUMMARY.json")
    extrap = jl(R / "s4d6/EXTRAPOLATION_S4D6.json")
    man = jl(a.dist / "PACKAGE_MANIFEST.json") if (a.dist / "PACKAGE_MANIFEST.json").exists() else {}
    ev = dict(
        instruction=dict(file="work/p1_step4d_20261017/S4D_CLAUDE_CODE_INSTRUCTION.md", sha256="a35fa7d52c0d645830562e57fb242563b864994682eeb1ce6a2a8d59f73b2586", verified=True),
        git=dict(branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), base="afec19e61f226652c0ee941a76298d4cbbc64ba8 (PR #27 head)",
                 pr="https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/28 (draft)", log=git("log", "--oneline", "afec19e6..HEAD").splitlines()),
        stops=[dict(id="S4D_STOP_01", step="S4D-1 item 1", reason="coastal-node classification unclear (TH2 2, PH_Luzon9 0; KH2 4 / KH2 3 noted)",
                    resolution="user decision 2026-10-17: option A with the physical coastline (s4d1_coastal_rule_user_decision)")],
        s4d1=dict(coastal=dict(nodes=coast["nodes"], coastal=coast["coastal"], buffered=coast["buffered"], sea_mask=coast["sea_mask"]),
                  export_links=dict(before=97, after=71), lao_transit=dict(summary=lao["summary"], transit=[{k: r[k] for k in ("node", "coast_country", "great_circle_km", "route_km",
                  "land_cost_rail_eur2020_per_t", "transit_unit_cost_eur2020_per_t", "alt_sea_port", "alt_port_land_cost_rail_eur2020_per_t", "land_cost_truck_eur2020_per_t")} for r in lao["transit"]]),
                  inland_reach={r["node"]: r["path_km"] for r in lao["reach"] if r["reaches_coastal_node"]},
                  registry=pick(["co2_land_transport_rail_unit_cost", "co2_land_transport_rail_loading_cost", "co2_land_transport_truck_unit_cost", "conv_usd2018_to_eur2020", "co2_land_route_length_factor"])),
        s4d2=dict(links=504, route_factor=routes["route_factor_median"], quantiles=routes["quantiles"], grid_bias=routes["grid_bias_straight_pairs"],
                  registry=pick(["co2_ship_chain_fixed_cost", "co2_ship_chain_per_km_cost", "co2_ship_route_factor", "co2_intra_vs_extra_asean_cost_note"])),
        s4d3=dict(trial_on_s4c_smokes={s: dict(relative_error=v["identity"]["relative_error"], pool_surplus_eur=-v["identity"]["difference_sources"]["asean_pool_surplus"],
                                               totals_bn_eur=v["totals_bn_eur"]) for s, v in trial.items()}, gate="B16_LEDGER", tolerance=1e-6),
        s4d4=dict(checks=coal["checks"], runs={t: {k: v[k] for k in ("termination", "objective", "b16", "cross_border_pairs", "failed")} for t, v in coal["runs"].items()},
                  corridor_edges=coal["corridor_edges"], isolated=coal["isolated"], connected_coalitions=coal["connected_coalitions_all_countries"]),
        s4d5=dict(runs=smoke["runs"], vs_s4c=smoke["s4c"], b5_passed=smoke["B5"].get("passed"), b6=dict(passed=smoke["B6"].get("passed"), difference=smoke["B6"].get("difference")),
                  disconnected_minus_integrated_bn_eur=smoke.get("disconnected_minus_integrated_bn_eur"),
                  co2={t: dict(extra_asean_mt=v["extra_asean_mt"], transit_mt=v["transit_mt"], shipping_mt=round(sum(x["mt"] for x in v["shipping"].values()), 6)) for t, v in smoke["co2"].items()},
                  ledgers={t: dict(relative_error=v["relative_error"], totals_bn_eur=v["totals_bn_eur"]) for t, v in smoke["ledgers"].items()}),
        s4d6=dict(status=(R / "s4d6/STATUS.txt").read_text().splitlines(), extrapolation={k: {kk: vv for kk, vv in v.items() if kk in ("barrier_iterations", "barrier_seconds", "wall_seconds", "peak_rss_gib", "extrapolation")}
                                                                                       for k, v in extrap["runs"].items()},
                  package=dict(commit=man.get("commit"), upload_total_bytes=man.get("upload_total_bytes_excluding_this_manifest"), files=len(man.get("files", [])),
                               run=man.get("run"), first_batch_sensitivities=man.get("first_batch_sensitivities_registered_not_packaged")),
                  registry=pick(["s4d6_sensitivity_extra_asean_cost", "s4d6_sensitivity_ship_route_factor", "s4d6_sensitivity_lng_cap", "s4d6_cloud_package"])),
        downloads=[dict(file="sources_s4d/co2_land/Stolaroff_2021_FrontEnergyRes_9_639943.pdf", url="https://www.frontiersin.org/articles/10.3389/fenrg.2021.639943/pdf", bytes=873889,
                        sha256="0d42dcaffc052d5b8b634e1885a7db94dd132d4fe7e4cd714100683f87b48082", category="CO2 rail / road transport cost literature")],
        resources=dict(local_max_single_compute_min=5, cloud=False, formal_solves=False),
        tests=a.tests)
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False))
    print("written", a.out, a.out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
