import glob, json, re, subprocess
M = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"
for p in sorted(glob.glob(f"{M}/results_project/dfx_v3/**/SOLVE_RECEIPT.json", recursive=True))[:30]:
    try:
        r = json.load(open(p))
    except Exception as e:
        continue
    l = r.get("lp") or r.get("lp_size") or {}
    i = r.get("input_network") or {}
    print(p.replace(M, ""), r.get("scenario"), r.get("label"), i.get("snapshots"), i.get("truncated_to"), {k: l.get(k) for k in ("num_col", "num_row", "nnz")}, r.get("solve_seconds"), r.get("objective"))
print(subprocess.run(f"grep -rln 'num_row' {M}/results_project/dfx_v3 --include=*.json | head -12", shell=True, capture_output=True, text=True).stdout)
