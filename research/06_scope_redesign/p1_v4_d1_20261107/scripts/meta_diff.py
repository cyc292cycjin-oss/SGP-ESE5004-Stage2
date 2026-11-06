"""D1: which leaves of n.meta differ between the W08 and D1 2920x3h integrated networks (read only)."""
import json
import pypsa

a = pypsa.Network("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/builds/main/integrated/integrated_2920_3h_unsolved.nc").meta
b = pypsa.Network("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d1/builds/main/integrated/integrated_2920_3h_unsolved.nc").meta
out = []


def walk(x, y, p):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            walk(x.get(k), y.get(k), p + [str(k)])
    elif json.dumps(x, sort_keys=True, default=str) != json.dumps(y, sort_keys=True, default=str):
        out.append(("/".join(p), str(x)[:90], str(y)[:90]))


for k in ("research_biomass", "s2_layers", "s2_demand_ledger", "v4_w08"):
    walk(a.get(k), b.get(k), [k])
for r in out[:40]:
    print(r)
print(len(out), "leaves differ")
d = json.load(open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d1_20261107/evidence/D1_NETWORK_DIFF.json"))
print({k: v["C8_diff"]["snapshots_and_weightings_equal"] for k, v in d.items()})
