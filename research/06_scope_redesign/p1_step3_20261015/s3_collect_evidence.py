"""Assemble S3_EVIDENCE.json from the S3 receipts (read-only; run inside WSL from the repo root).

    PYTHONHASHSEED=0 python research/06_scope_redesign/p1_step3_20261015/s3_collect_evidence.py
"""
from pathlib import Path
import hashlib, json, subprocess, time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RES = REPO / "results_project"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def opt(p):
    return read(p) if Path(p).exists() else None


def git(cmd):
    return subprocess.run(["git"] + cmd, cwd=REPO, capture_output=True, text=True).stdout.strip()


def trim_build(r):
    keep = ["status", "scenario", "gap_diagnostic", "network", "inputs", "research_config_sha256", "cross_border", "static_validation", "code_sha", "environment", "build_seconds", "solver_runs"]
    out = {k: r[k] for k in keep if k in r}
    out["cross_border"] = {k: {kk: (len(vv) if isinstance(vv, list) else vv) for kk, vv in v.items() if kk not in ("edges", "pipelines", "removed", "components")} for k, v in r["cross_border"].items()}
    sv = r["static_validation"]
    out["static_validation"] = {k: (v if k != "carbon" else {kk: vv for kk, vv in v.items() if kk != "registry"}) for k, v in sv.items()}
    out["inventory_counts"] = {typ: (len(v) if isinstance(v, (list, dict)) else v) for typ, v in r.get("inventory", {}).items()}
    out["s3_layers"] = {k: ({kk: vv for kk, vv in v.items() if kk not in ("terminals",)} if isinstance(v, dict) else v) for k, v in (r.get("s3_layers") or {}).items()}
    if out["s3_layers"].get("gas"):
        out["s3_layers"]["gas"] = {k: v for k, v in out["s3_layers"]["gas"].items() if k != "lng"} | {"lng": {k: v for k, v in out["s3_layers"]["gas"]["lng"].items() if k != "terminals"}}
    out["config_overrides"] = r.get("research_config", {}).get("config_overrides") if isinstance(r.get("research_config"), dict) else None
    out["pipelines"] = {k: v for k, v in r.get("pipelines", {}).items() if k != "table"}
    return out


def trim_solve(r):
    out = {k: v for k, v in r.items() if k not in ("solver_parameters", "emissions_by_country", "co2_flows", "gap_table")}
    if "lp" in out:
        out["lp"] = {k: v for k, v in out["lp"].items() if k != "research_constraints"} | {"research_constraint_groups": sorted({c.split("-")[0] for c in r["lp"].get("research_constraints", [])})}
    return out


def solve_dir(d):
    if not (d / "SOLVE_RECEIPT.json").exists():
        return None
    r = read(d / "SOLVE_RECEIPT.json"); gates = opt(d / "V5_GATES.json")
    out = dict(receipt=trim_solve(r), gap_table=opt(d / "GAP_TABLE.json"), co2_flows=opt(d / "CO2_FLOWS.json"), infeasibility=opt(d / "INFEASIBILITY_DIAGNOSIS.json"),
               emissions_by_country=(lambda e: {k: v for k, v in e.items() if k != "ports"})(read(d / "EMISSIONS_BY_COUNTRY.json")) if (d / "EMISSIONS_BY_COUNTRY.json").exists() else None,
               gates={k: ({kk: vv for kk, vv in v.items() if kk not in ("rows", "stores", "countries", "details", "terminals", "generators", "by_country")} if isinstance(v, dict) else v) for k, v in gates.items()} if gates else None,
               gate_b11_rows=gates["B11"]["rows"] if gates else None, gate_b14_terminals=gates["B14"]["terminals"] if gates and "B14" in gates else None,
               gate_b15_by_country=gates["B15"]["by_country"] if gates and "B15" in gates else None, gate_b1_scope=gates["B1"].get("s3_scope") if gates and "B1" in gates else None,
               lp=opt(d / "lp" / "MATH_PROBLEM.json"), files={p.name: sha(p) for p in d.glob("*.csv")}, highs_log_tail=(d / "highs.linopy.log").read_text().splitlines()[-8:] if (d / "highs.linopy.log").exists() else None)
    return out


def main():
    ev = dict(schema="s3-evidence-v1", generated_epoch=time.time(), branch=git(["rev-parse", "--abbrev-ref", "HEAD"]), head=git(["rev-parse", "HEAD"]),
              status="S3_GAS_IMPORTS_SHIPPING_SMOKE", formal_solves=0, smoke_label="SMOKE_TEST_ONLY", diagnostic_label="GAP_DIAGNOSTIC_NOT_FOR_INTERCONNECTION_VALUE",
              commits=dict(s3_0="9a6f9e20", s3_1="ca4657b6", s3_2="b0c6b068", s3_3="e18ccd46+077028c8", s3_4="cfa53849", s3_5="ededdc9e", s3_6="b8ac3ed9"))
    ev["registry"] = dict(file="research_inputs/registry_v5/DATA_REGISTRY.csv", sha256=sha(REPO / "research_inputs/registry_v5/DATA_REGISTRY.csv"), d1_evidence_summary=(opt(REPO / "research_inputs/registry_v5/D1_EVIDENCE.json") or {}).get("summary"))
    ev["steps"] = {}
    for step, base in [("s3_0", RES / "s3"), ("s3_1", RES / "s3_1"), ("s3_2", RES / "s3_2"), ("s3_3", RES / "s3_3"), ("s3_4", RES / "s3_4"), ("s3_5", RES / "s3_5"), ("s3_7", RES / "s3_7")]:
        if not base.exists():
            continue
        s = dict(status_file=(base / "STATUS.txt").read_text().split() if (base / "STATUS.txt").exists() else None, builds={}, smoke={}, smoke_simplex={}, gap_diagnostic={})
        for sc in ["integrated", "disconnected", "pc_integrated", "pc_disconnected"]:
            nm = sc.replace("pc_", "")
            r = opt(base / sc / f"{nm}_BUILD_RECEIPT.json")
            if r:
                s["builds"][sc] = trim_build(r); s["builds"][sc]["memory_estimate"] = opt(base / f"{nm}_MEMORY_ESTIMATE.json")
            g = opt(base / f"{sc}_gap" / f"{nm}_gap_diagnostic_BUILD_RECEIPT.json")
            if g:
                s["builds"][sc + "_gap_diagnostic"] = dict(network=g["network"], status=g["status"], code_sha=g["code_sha"], gap_diagnostic=g["gap_diagnostic"])
            for kind in ["smoke", "smoke_simplex", "gap_diagnostic"]:
                d = solve_dir(base / kind / sc)
                if d:
                    s[kind][sc] = d
        gb = base / "gurobi"
        if gb.exists():   # S3-7 decision 65: Gurobi runs (scrubbed logs only)
            s["gurobi"] = {f"{kind}/{tag}": solve_dir(gb / kind / tag) for kind in ["smoke", "gap_diagnostic"] for tag in ["integrated", "disconnected", "pc_integrated", "pc_disconnected"] if (gb / kind / tag / "SOLVE_RECEIPT.json").exists()}
            s["gurobi_status"] = (gb / "STATUS.txt").read_text().splitlines() if (gb / "STATUS.txt").exists() else None
            for k, v in s["gurobi"].items():
                v["gurobi_log_stats"] = (v["receipt"].get("gurobi_log_stats") if v and v.get("receipt") else None)
        for f in base.glob("S3_*_STRUCTURAL_GAP_ANNUAL.json"):
            s["structural_gap_annual"] = read(f)
        ev["steps"][step] = s
    ev["s3_5_pc_build"] = (lambda r: trim_build(r) if r else None)(opt(RES / "s3_5_pc" / "integrated" / "integrated_BUILD_RECEIPT.json"))
    ev["gates_static_s3_6"] = opt(HERE / "evidence" / "s3_6" / "S3_6_GATES_STATIC.json")
    ev["lp_ranges"] = {p.name: read(p) for p in (HERE / "evidence" / "s3_7").glob("S3_7_LP_RANGES_*.json")}
    for k, v in ev["lp_ranges"].items():
        for sec in ["matrix", "rhs", "objective"]:
            v[sec] = {kk: vv for kk, vv in v[sec].items() if kk not in ("smallest", "largest")}
    ev["smoke_check_s3_0"] = opt(HERE / "S3_0_SMOKE_CHECK.json")
    ev["kh_check"] = opt(HERE / "KH_TRANSPORT_CHAIN_CHECK.json")
    ev["data"] = {}
    for key, f in [("industry", "research_inputs/demand_v5/INDUSTRY_2050_EVIDENCE.json"), ("industry_ratios", "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_EVIDENCE.json"), ("corridors", "research_inputs/corridors/CORRIDOR_APG_EVIDENCE.json"),
                   ("feedstock", "research_inputs/registry_v5/FEEDSTOCK_CARBON_TERRITORIAL_EVIDENCE.json"), ("gas", "research_inputs/gas_v5/GAS_NETWORK_EVIDENCE.json"), ("imports", "research_inputs/imports_v5/IMPORT_PRICES_EVIDENCE.json"),
                   ("import_price_decline", "research_inputs/imports_v5/IMPORT_PRICE_DECLINE_EVIDENCE.json"), ("shipping", "research_inputs/shipping_v5/SHIPPING_EVIDENCE.json"), ("ammonia_methanol", "research_inputs/registry_v5/AMMONIA_METHANOL_EVIDENCE.json"),
                   ("fuel_carbon", "research_inputs/registry_v5/FUEL_CARBON_EVIDENCE.json")]:
        e = opt(REPO / f)
        if e:
            if key == "industry":
                e = {k: v for k, v in e.items() if k not in ("gaps", "summary_main")}
            if key == "industry_ratios":
                e = {k: v for k, v in e.items() if k not in ("ratios", "today")}
            if key == "imports":
                e = {k: v for k, v in e.items() if k != "rows"} | {"prices": [{kk: r[kk] for kk in ("esc", "carrier", "base_eur2020_per_mwh", "applied_eur2020_per_mwh", "cheapest_exporter", "status")} for r in e["rows"]]}
            ev["data"][key] = dict(file=f, sha256=sha(REPO / f), content=e)
    ev["inputs"] = {f: sha(REPO / f) for f in ["research_inputs/corridors/cross_border_corridors.csv", "research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv", "research_inputs/demand_v5/INDUSTRY_2050_COMPARISON_BAS_S2B_S3.csv",
                                                "research_inputs/gas_v5/GAS_PIPELINES_EXISTING_CROSS_BORDER_2025.csv", "research_inputs/imports_v5/IMPORT_PRICES_2050.csv", "research_inputs/shipping_v5/SHIPPING_DEMAND_2050.csv",
                                                "research_inputs/registry_v5/INDUSTRY_SECTOR_RATIOS_PYPSA_EUR_2050.csv", "research_inputs/registry_v5/DOWNLOAD_LIST.csv", "research_inputs/registry_v5/DATA_PENDING_LIST.csv"] if (REPO / f).exists()}
    ev["scripts"] = {f: sha(REPO / "scripts_project" / f) for f in ["s3_0_industry_ratios.py", "s3_0_industry.py", "s3_0_corridors.py", "s3_0_kh_check.py", "s3_1_gas_data.py", "s3_2_imports_data.py", "s3_3_ammonia_methanol_data.py", "s3_4_shipping_data.py",
                                                                      "s3_5_fuel_carbon_data.py", "s3_6_gates_check.py", "s3_7_lp_ranges.py", "s3_7_import_price_decline.py", "s3_layers.py", "s2_layers.py", "s2_network.py", "s2_solve.py", "s2_structural_gap.py",
                                                                      "v5/v5_gates.py", "scenario_network.py", "country_carbon.py", "d1_registry.py"] if (REPO / "scripts_project" / f).exists()}
    ev["configs"] = {f: sha(REPO / "configs/research" / f) for f in ["baseline.yaml", "integrated.yaml", "disconnected.yaml"] if (REPO / "configs/research" / f).exists()}
    ev["tests"] = opt(HERE / "S3_TEST_RUN.json")
    (HERE / "S3_EVIDENCE.json").write_text(json.dumps(ev, indent=1, default=str))
    print("S3_EVIDENCE.json written:", round((HERE / "S3_EVIDENCE.json").stat().st_size / 1e6, 2), "MB; steps:", list(ev["steps"]))


if __name__ == "__main__":
    main()
