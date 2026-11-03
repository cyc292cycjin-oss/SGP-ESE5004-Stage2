"""V3 HPC package step 3, AFTER the S-A smoke (read-only, no solver): the local 56-snapshot smoke of F1 / F2 (S-A) beside the supplement 05 smoke (S-B):
objectives, B6, Owen dual-form benefit per participant (alpha main), ship freight and volumes, failed gates against the pre-announcement, barrier iterations,
solve seconds, peak memory, ship capacity duals. usage: python sa_effect_post.py <smoke_hpc> <smoke_s5> <evidence dir of smoke_hpc> <out json>"""
import csv, json, re, sys
from pathlib import Path

sys.path.insert(0, "/home/jin/wt_v3_hpc/scripts_project")
from m10_batch3_summary import owen_main   # noqa: E402

A, S, EVA, OUT = map(Path, sys.argv[1:5])
PRE = {"A1_A2", "A1_A2_S4B", "A3", "A3_S4B", "B1", "B3", "B8"}   # RUN_PLAN_V3.md 24.2 (union rule)


def jl(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return {}


def run(d: Path):
    r = jl(d / "SOLVE_RECEIPT.json"); g = jl(d / "V5_GATES.json"); log = (d / "gurobi.linopy.log").read_text(errors="ignore") if (d / "gurobi.linopy.log").exists() else ""
    it = re.findall(r"Barrier (?:performed|solved model in) (\d+) iterations(?: and| in) ([\d.]+) seconds", log)
    failed = sorted(k for k, v in g.items() if isinstance(v, dict) and v.get("passed") is False)
    fr = {}
    p = d / "COUNTRY_COST_LEDGER.csv"
    if p.exists():
        for row in csv.DictReader(open(p)):
            if row.get("subject") in ("liquid_ship_freight", "liquid_transit_freight"):
                fr[row["subject"]] = fr.get(row["subject"], 0.0) + float(row["eur"])
    peak = None
    e = d / "solve.err"
    if e.exists():
        m = re.findall(r"Maximum resident set size \(kbytes\): (\d+)", e.read_text(errors="ignore")); peak = int(m[-1]) / 1048576 if m else None
    return dict(termination=r.get("termination_condition"), objective_bn=(r.get("objective") or 0) / 1e9, solve_seconds=r.get("solve_seconds"), barrier=(int(it[-1][0]), float(it[-1][1])) if it else None,
                failed_gates=failed, failed_outside_preannouncement=sorted(set(failed) - PRE), freight_bn={k: v / 1e9 for k, v in fr.items()}, peak_gib=peak, owen=owen_main(d))


res = {}
for lab, base in (("sa", A), ("sb", S)):
    res[lab] = {rid: run(base / rid) for rid in ("integrated", "no_new_xb")}
    i, n = res[lab]["integrated"], res[lab]["no_new_xb"]
    res[lab]["b6_bn"] = n["objective_bn"] - i["objective_bn"]
    res[lab]["owen_benefit_bn"] = {p: (n["owen"].get(p, 0.0) - i["owen"].get(p, 0.0)) / 1e9 for p in sorted(set(i["owen"]) | set(n["owen"]))}
d = res["sa"]; s = res["sb"]
res["sa_minus_sb"] = dict(objective_bn={r: d[r]["objective_bn"] - s[r]["objective_bn"] for r in ("integrated", "no_new_xb")}, b6_bn=d["b6_bn"] - s["b6_bn"],
                          owen_benefit_bn={p: d["owen_benefit_bn"][p] - s["owen_benefit_bn"].get(p, 0.0) for p in d["owen_benefit_bn"]},
                          owen_sign_same={p: (d["owen_benefit_bn"][p] > 0) == (s["owen_benefit_bn"].get(p, 0.0) > 0) for p in d["owen_benefit_bn"]},
                          freight_bn={r: {k: d[r]["freight_bn"].get(k, 0.0) - s[r]["freight_bn"].get(k, 0.0) for k in set(d[r]["freight_bn"]) | set(s[r]["freight_bn"])} for r in ("integrated", "no_new_xb")})
duals = list(csv.DictReader(open(EVA / "V3_SHIP_CAPACITY_DUALS.csv"))) if (EVA / "V3_SHIP_CAPACITY_DUALS.csv").exists() else []
if duals:
    keys = duals[0].keys(); res["ship_capacity_duals"] = dict(columns=list(keys), rows=len(duals))
    num = lambda r, k: float(r[k]) if r.get(k) not in (None, "") else 0.0
    for k in keys:
        try:
            res["ship_capacity_duals"][f"max_{k}"] = max(num(r, k) for r in duals)
        except ValueError:
            pass
OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps(dict(sa={r: (d[r]["objective_bn"], d[r]["barrier"], d[r]["failed_gates"], d[r]["failed_outside_preannouncement"], d[r]["peak_gib"]) for r in ("integrated", "no_new_xb")}, b6=(d["b6_bn"], s["b6_bn"]),
                      diff=res["sa_minus_sb"]["objective_bn"], db6=res["sa_minus_sb"]["b6_bn"], owen_sa=d["owen_benefit_bn"], owen_sb=s["owen_benefit_bn"], sign_same=res["sa_minus_sb"]["owen_sign_same"],
                      freight=res["sa_minus_sb"]["freight_bn"], sb_barrier={r: s[r]["barrier"] for r in ("integrated", "no_new_xb")}, duals=res.get("ship_capacity_duals")), default=str))
