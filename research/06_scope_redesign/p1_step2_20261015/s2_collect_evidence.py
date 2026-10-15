"""Assemble S2_EVIDENCE.json from the S2 receipts (read-only; run inside WSL from the repo root).

    PYTHONHASHSEED=0 python research/06_scope_redesign/p1_step2_20261015/s2_collect_evidence.py
"""
from pathlib import Path
import hashlib, json, subprocess, time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
S2 = REPO / "results_project" / "s2"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def opt(p):
    return read(p) if Path(p).exists() else None


def git(cmd):
    return subprocess.run(["git"] + cmd, cwd=REPO, capture_output=True, text=True).stdout.strip()


def trim_build(r):
    keep = ["status", "scenario", "gap_diagnostic", "s2_status", "network", "inputs", "research_config_sha256", "cross_border", "transmission_limit", "demand_astar",
            "demand_s2", "geothermal", "co2", "biomass", "heat", "cost_layer", "static_validation", "code_sha", "environment", "build_seconds", "solver_runs"]
    out = {k: r[k] for k in keep if k in r}
    out["cross_border"] = {k: {kk: (len(vv) if isinstance(vv, list) else vv) for kk, vv in v.items() if kk not in ("edges", "pipelines", "removed")} for k, v in r["cross_border"].items()}
    out["cost_layer"] = {k: v for k, v in r["cost_layer"].items() if k != "rows"}
    out["co2"] = {k: v for k, v in r["co2"].items() if k != "pipeline_rows"}
    sv = r["static_validation"]
    out["static_validation"] = {k: (v if k not in ("carbon",) else {kk: vv for kk, vv in v.items() if kk != "registry"}) for k, v in sv.items()}
    out["inventory_counts"] = {typ: len(v) if isinstance(v, (list, dict)) else v for typ, v in r.get("inventory", {}).items()}
    if "daily_network" in r and r["daily_network"]:
        out["daily_network"] = {k: v for k, v in r["daily_network"].items() if k != "aggregation"}
    return out


def trim_solve(r):
    out = {k: v for k, v in r.items() if k not in ("solver_parameters", "emissions_by_country", "co2_flows", "gap_table")}
    if "lp" in out:
        out["lp"] = {k: v for k, v in out["lp"].items() if k != "research_constraints"} | {"research_constraint_groups": sorted({c.split("-")[0] for c in r["lp"].get("research_constraints", [])})}
    return out


def main():
    ev = dict(schema="s2-evidence-v1", generated_epoch=time.time(), branch=git(["rev-parse", "--abbrev-ref", "HEAD"]), head=git(["rev-parse", "HEAD"]),
              status="S2_SECTOR_COUPLED_SMOKE", formal_solves=0, smoke_label="SMOKE_TEST_ONLY", diagnostic_label="GAP_DIAGNOSTIC_NOT_FOR_INTERCONNECTION_VALUE")
    ev["s2_0"] = dict(report="S2_0_DATA_TOPUP.md", commits=["f0ad4070", "f64e1fd0"], registry=dict(file="research_inputs/registry_v5/DATA_REGISTRY.csv", sha256=sha(REPO / "research_inputs/registry_v5/DATA_REGISTRY.csv")),
                      pending_list=dict(file="DATA_PENDING_LIST.csv", sha256=sha(HERE / "DATA_PENDING_LIST.csv")),
                      cost_layer_manifest=opt(REPO / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/LAYER_MANIFEST.json"))
    ev["builds"] = {}
    for sc in ["integrated", "disconnected"]:
        r = opt(S2 / sc / f"{sc}_BUILD_RECEIPT.json")
        if r:
            ev["builds"][sc] = trim_build(r)
        g = opt(S2 / f"{sc}_gap2" / f"{sc}_gap_diagnostic_BUILD_RECEIPT.json")
        if g:
            ev["builds"][sc + "_gap_diagnostic"] = dict(network=g["network"], status=g["status"], code_sha=g["code_sha"], gap_diagnostic=g["gap_diagnostic"])
    ev["smoke_run1"] = {}
    for sc in ["integrated", "disconnected"]:
        d = S2 / "smoke" / f"{sc}_run1_infeasible_postprocess_crash"
        if (d / "SOLVE_RECEIPT.json").exists():
            r = read(d / "SOLVE_RECEIPT.json")
            ev["smoke_run1"][sc] = dict(receipt=trim_solve(r), posthoc_structural_diagnosis=opt(d / "POSTHOC_STRUCTURAL_DIAGNOSIS.json"), lp=opt(d / "lp" / "MATH_PROBLEM.json"))
    ev["gap_diagnostic_run1"] = {sc: trim_solve(read(S2 / "gap_diagnostic_run1_infeasible_no_biomass_slack" / sc / "SOLVE_RECEIPT.json")) for sc in ["integrated", "disconnected"]
                                 if (S2 / "gap_diagnostic_run1_infeasible_no_biomass_slack" / sc / "SOLVE_RECEIPT.json").exists()}
    ev["gap_diagnostic"] = {}
    for sc in ["integrated", "disconnected"]:
        d = S2 / "gap_diagnostic" / sc
        if (d / "SOLVE_RECEIPT.json").exists():
            r = read(d / "SOLVE_RECEIPT.json"); gates = opt(d / "V5_GATES.json")
            ev["gap_diagnostic"][sc] = dict(receipt=trim_solve(r), gap_table=opt(d / "GAP_TABLE.json"), co2_flows=opt(d / "CO2_FLOWS.json"),
                                            emissions_by_country=(lambda e: {k: v for k, v in e.items() if k != "ports"})(read(d / "EMISSIONS_BY_COUNTRY.json")),
                                            gates={k: ({kk: vv for kk, vv in v.items() if kk not in ("rows", "stores", "countries", "details")} if isinstance(v, dict) else v) for k, v in gates.items()} if gates else None,
                                            gate_b11_rows=gates["B11"]["rows"] if gates else None, gate_a3_failed=gates["A3"].get("failed") if gates else None,
                                            lp=opt(d / "lp" / "MATH_PROBLEM.json"), files={p.name: sha(p) for p in d.glob("*.csv")})
            co2_gap_total = sum((row.get("co2_gap_t") or 0.0) for row in ev["gap_diagnostic"][sc]["gap_table"]["rows"])
            resid = gates["A3"]["details"]["objective_reconciliation"] if gates else None
            if resid:
                unexplained = resid["actual"] - resid["capital"] - resid["variable"] - resid["known_fixed_once"]
                ev["gap_diagnostic"][sc]["objective_reconciliation_check"] = dict(unexplained_residual=unexplained, co2_slack_penalty=co2_gap_total * 10000.0,
                                                                                   relative_difference=(unexplained - co2_gap_total * 10000.0) / max(abs(unexplained), 1.0),
                                                                                   reading="the A3/A5 reconciliation residual equals the CO2 slack penalty term (added to the objective by the gap hook, not a component cost)")
    ev["structural_gap_annual"] = opt(S2 / "S2_STRUCTURAL_GAP_ANNUAL.json")
    ev["costs_active"] = dict(file="results_project/s2/integrated/costs_active_research.csv", sha256=sha(S2 / "integrated" / "costs_active_research.csv"), ledger=opt(S2 / "integrated" / "costs_active_research_ledger.json"))
    if ev["costs_active"]["ledger"]:
        ev["costs_active"]["ledger"] = {k: v for k, v in ev["costs_active"]["ledger"].items() if k != "rows"}
    ev["configs"] = {f: sha(REPO / "configs/research" / f) for f in ["baseline.yaml", "integrated.yaml", "disconnected.yaml"]}
    ev["inputs"] = {f: sha(REPO / f) for f in ["research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv",
                                                "research_inputs/registry_v5/PROCESS_EMISSIONS_2019_2050.csv", "research_inputs/registry_v5/FEEDSTOCK_CARBON_BOUNDARY_2019.csv",
                                                "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020_prepared.csv", "results_project/s1/S1_SELECTED_ASSET_SURVIVAL_2050.json"]
                    if (REPO / f).exists()}
    ev["scripts"] = {f: sha(REPO / "scripts_project" / f) for f in ["s2_costs.py", "s2_layers.py", "s2_network.py", "s2_solve.py", "s2_structural_gap.py", "v5/v5_gates.py", "assembly_components.py"]}
    ev["tests"] = opt(HERE / "S2_TEST_RUN.json")
    out = HERE / "S2_EVIDENCE.json"
    out.write_text(json.dumps(ev, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print("written", out, sha(out), f"{out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
