set -u
export PYTHONHASHSEED=0 PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
B=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/builds
cd /home/jin/wt_v4_fable/scripts_project || exit 1
grep -n "production_caps\|cap_mwh_per_year\|DOMESTIC_PRODUCTION\|e_sum_max\|p_nom_max" s3_layers.py | head -30
$PY - <<PY
import warnings; warnings.filterwarnings("ignore")
import pypsa, pandas as pd, json
n = pypsa.Network("$B/main/integrated/integrated_2920_3h_unsolved.nc")
print("snapshots", len(n.snapshots), n.snapshots[0], n.snapshots[-1], "weights", n.snapshot_weightings.iloc[0].to_dict())
print("meta keys", sorted(n.meta.keys())[:80])
print("v4_w08 meta", json.dumps(n.meta.get("v4_w08"), default=str)[:1500])
print("loads cols", list(n.loads.columns))
print("n loads", len(n.loads), "time-varying p_set cols", n.loads_t.p_set.shape)
ie = [l for l in n.loads.index if l.endswith("industry electricity demand")]
print("industry electricity loads", len(ie), ie[:3])
tv = [l for l in ie if l in n.loads_t.p_set.columns]
print("of which time-varying", len(tv))
hb = [l for l in n.loads.index if "heat demand" in l and "industry" in l.lower()]
print("industry heat-like loads", len(hb), sorted({l.split(" ",1)[1] for l in hb})[:12])
print("stores cols", [c for c in n.stores.columns if c in ("bus","carrier","e_nom","e_initial","country","research_role","s2_category")])
sb = n.stores[n.stores.carrier=="solid biomass"]
print("solid biomass stores", len(sb)); print(sb.groupby("country").e_nom.sum().round(0).to_dict())
g = n.generators[n.generators.carrier=="gas"]
print("gas generators cols", [c for c in n.generators.columns if "research" in c or c in ("p_nom","p_nom_max","e_sum_max","country","p_nom_extendable")])
print(g.groupby([g.get("research_role", pd.Series("?", index=g.index))]).size())
di = n.meta.get("demand_identity", {}); print("demand_identity entries", len(di)); k0 = list(di)[0] if di else None; print(k0, di.get(k0) if k0 else None)
do = n.meta.get("demand_owners", {}); print("demand_owners entries", len(do)); k1 = list(do)[0] if do else None; print(k1, do.get(k1) if k1 else None)
led = n.meta.get("s2_demand_ledger", {}); print("ledger keys", list(led.keys())); print("params keys", list(led.get("parameters", {}).keys()))
print("industry param", json.dumps(led.get("parameters", {}).get("industry", {}), default=str)[:2500])
PY
