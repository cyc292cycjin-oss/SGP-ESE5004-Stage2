set -u
RUN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/smoke56
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
head -2 $RUN/v4_F1/COMPONENT_COST_BREAKDOWN.csv | cut -c1-600
echo "--- CO2_FLOWS keys"; $PY -c "import json; d=json.load(open('$RUN/v4_F1/CO2_FLOWS.json')); print(list(d.keys())[:30]); import itertools; print({k:(str(v)[:200]) for k,v in itertools.islice(d.items(),0,6)})"
echo "--- EMISSIONS keys"; $PY -c "import json; d=json.load(open('$RUN/v4_F1/EMISSIONS_BY_COUNTRY.json')); print(list(d.keys())[:20]); print(str(d)[:600])"
$PY - <<PY
import pandas as pd, json
pd.set_option("display.width", 250)
R = "$RUN"
out = {}
for r in ("v31_F1", "v4_F1", "v4iid_F1"):
    t = pd.read_csv(f"{R}/{r}/COMPONENT_COST_BREAKDOWN.csv")
    if r == "v31_F1": print("columns:", list(t.columns)); print(t.head(3).to_string())
    num = [c for c in t.columns if t[c].dtype != object]
    key = [c for c in ("component", "carrier", "country", "cost_type", "category") if c in t.columns]
    out[r] = t
cols = [c for c in out["v31_F1"].columns if out["v31_F1"][c].dtype != object]
print("numeric columns:", cols)
# aggregate by carrier if present
kc = "carrier" if "carrier" in out["v31_F1"].columns else None
if kc:
    vals = [c for c in cols if "cost" in c.lower() or "eur" in c.lower()] or cols[:3]
    agg = {r: out[r].groupby(kc)[vals].sum() for r in out}
    d = (agg["v4_F1"] - agg["v31_F1"]).fillna(0.0); d2 = (agg["v4iid_F1"] - agg["v31_F1"]).fillna(0.0)
    tot = d.sum(axis=1)
    print("TOTAL v31", agg["v31_F1"][vals].sum().sum()/1e9, "v4", agg["v4_F1"][vals].sum().sum()/1e9, "diff", (agg["v4_F1"][vals].sum().sum()-agg["v31_F1"][vals].sum().sum())/1e9)
    big = tot.abs().sort_values(ascending=False).head(30).index
    print((pd.DataFrame({"v31_bn": agg["v31_F1"].loc[big, vals].sum(axis=1)/1e9, "v4_bn": agg["v4_F1"].loc[big, vals].sum(axis=1)/1e9, "d_v4_bn": tot[big]/1e9, "d_iid_bn": d2.sum(axis=1)[big]/1e9})).round(3).to_string())
    json.dump({r: (agg[r][vals].sum(axis=1)/1e9).to_dict() for r in agg}, open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107/evidence/SMOKE_COST_BY_CARRIER_bn.json", "w"), indent=1)
PY
echo "--- CO2 price (global constraint duals) and captured CO2"
$PY - <<PY
import warnings; warnings.filterwarnings("ignore")
import pypsa
R = "$RUN"
for r, sc in (("v31_F1", "integrated"), ("v4_F1", "integrated"), ("v4iid_F1", "integrated")):
    n = pypsa.Network(f"{R}/{r}/{sc}_SMOKE_TEST_ONLY_solved.nc")
    gc = n.global_constraints
    print(r, "global constraints:", {k: (round(float(gc.at[k, "constant"]), 1), round(float(gc.at[k, "mu"]), 3)) for k in gc.index[:8]})
    w = n.snapshot_weightings.generators
    cc = n.links[n.links.carrier.str.endswith("CC") | n.links.carrier.str.contains("capture")]
    caps = {}
    for k in cc.index:
        c = n.links.at[k, "country"] if "country" in n.links.columns else "?"
        if "bus3" in n.links.columns and isinstance(n.links.at[k, "bus3"], str) and "co2 stored" in n.links.at[k, "bus3"]:
            caps[c] = caps.get(c, 0.0) + float((-n.links_t.p3[k] * w).sum())
    print(r, "CO2 captured to storage via CC links (Mt, annualised 56->8760 weights):", {k: round(v/1e6, 2) for k, v in sorted(caps.items())}, "total", round(sum(caps.values())/1e6, 2))
PY
