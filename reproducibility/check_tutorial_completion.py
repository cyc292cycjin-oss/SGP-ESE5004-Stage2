"""Read-only tutorial artifact checks; does not rerun optimization."""
from pathlib import Path
import hashlib, json, math
from datetime import datetime, timezone
import xarray as xr
root=Path(__file__).resolve().parents[1]
rows=[]
for year in (2030,2040,2050):
    name=f"elec_s_50_ec_lv2.0__3h_{year}_0.071"
    path=root/f"results/baseline-aims-3H-tutorial/postnetworks/{name}.nc"
    log=root/f"logs/baseline-aims-3H-tutorial/solve_network/{name}_python.log"
    text=log.read_text()
    with xr.open_dataset(path) as ds:
        objective=float(ds.attrs["network_objective"])
        assert math.isfinite(objective), (year, "nonfinite objective")
        meta=json.loads(ds.attrs["meta"])
        solving=meta["solving"]
        solver=solving["solver"]
        row={"year":year,"file":str(path.relative_to(root)),
             "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
             "bytes":path.stat().st_size,"dimensions":dict(ds.sizes),
             "objective_raw":objective,
             "objective_constant_raw":float(ds.attrs["network_objective_constant"]),
             "solver":solver["name"],
             "solver_options":solving["solver_options"][solver["options"]],
             "optimal_in_log":"Termination condition: optimal" in text,
             "log":str(log.relative_to(root))}
        assert row["optimal_in_log"], (year, "optimal status missing")
        rows.append(row)
report={"checked_at":datetime.now(timezone.utc).isoformat(),
        "status":"TUTORIAL_WORKFLOW_COMPLETE_SCIENTIFIC_VALIDATION_PENDING",
        "scope":"Tutorial: 50 geographical clusters, six days, 3-hour resolution. Not full paper reproduction.",
        "checks":"Files readable, finite objectives, optimal termination in logs, SHA256 recorded. No optimization rerun.",
        "not_checked":"Full physical feasibility, cost accounting, and agreement with paper benchmarks.",
        "known_issues":["Simplification audit: bus 765 load and 1 MW solar lost through mapping to absent bus 766; unresolved.",
          "Code, data, environment and scenario definitions still require alignment with the paper version.",
          "Raw solver objectives are not directly interpreted as paper annual system costs.",
          "2030 used IPM; 2040 and 2050 used simplex."],
        "networks":rows}
output=root/"reproducibility/tutorial_completion_audit.json"
output.write_text(json.dumps(report,indent=2)+"\n")
print(report["status"])
for row in rows:
    print(row["year"], "optimal; readable; finite objective; SHA256 recorded", row["bytes"], "bytes")
print("Report:",output)
