"""M10R B4.3: compare the v6 BUILD_ONLY dry run with the v5 dry run (M10A supplement 01) run by run: LP dimensions, solver parameters incl. TimeLimit,
input network SHA256, registered SHA256, LP array bytes, BUILD_CHECK passed, wall cap - everything must be equal (the batch mode is unchanged).
    python buildcmp.py <v6 build_only dir> <v5 build_only dir> <out json>"""
import json
import sys
from pathlib import Path

new, old, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
rows, all_ok = {}, True
for rid in [f"R{i}" for i in range(1, 12)]:
    a, b = new / rid, old / rid
    bc_a, bc_b = json.loads((a / "BUILD_CHECK.json").read_text()), json.loads((b / "BUILD_CHECK.json").read_text())
    run_a, run_b = json.loads((a / "RUN.json").read_text()), json.loads((b / "RUN.json").read_text())
    lp_bytes = [(p / "lp_bytes.txt").read_text().strip() if (p / "lp_bytes.txt").exists() else None for p in (a, b)]
    dims = ("num_row", "num_col", "nnz")
    r = dict(lp_equal=all(bc_a["lp"][k] == bc_b["lp"][k] for k in dims), lp={k: bc_a["lp"][k] for k in dims}, parameters_equal=bc_a["parameters"] == bc_b["parameters"], parameters=bc_a["parameters"],
             network_sha256_equal=bc_a["network_sha256"] == bc_b["network_sha256"], network_sha256=bc_a["network_sha256"],
             registered_sha256_equal=run_a["registered_sha256"] == run_b["registered_sha256"], lp_bytes=lp_bytes, lp_bytes_equal=lp_bytes[0] == lp_bytes[1],
             passed=[bc_a["passed"], bc_b["passed"]], wall_cap=[run_a.get("wall_cap_s"), run_b.get("wall_cap_s")], time_limit=[run_a.get("time_limit"), run_b.get("time_limit")],
             peak_rss_gib=[round(bc_a["peak_rss_gib"], 2), round(bc_b["peak_rss_gib"], 2)], build_seconds=[bc_a["lp"]["build_seconds"], bc_b["lp"]["build_seconds"]])
    ok = r["lp_equal"] and r["parameters_equal"] and r["network_sha256_equal"] and r["registered_sha256_equal"] and r["lp_bytes_equal"] and all(r["passed"]) \
        and r["wall_cap"] == [30000, 30000] and r["time_limit"] == [28800.0, 28800.0]
    r["all_equal"] = ok; all_ok &= ok
    rows[rid] = r
res = dict(note="v6 BUILD_ONLY (M10R) vs v5 BUILD_ONLY (M10A supplement 01): the batch mode must be unchanged run by run", all_equal=all_ok, runs=rows)
out.write_text(json.dumps(res, indent=1))
print(json.dumps(dict(all_equal=all_ok, runs={k: dict(lp=v["lp_equal"], par=v["parameters_equal"], sha=v["network_sha256_equal"], bytes=v["lp_bytes_equal"], passed=v["passed"]) for k, v in rows.items()})))
sys.exit(0 if all_ok else 1)
