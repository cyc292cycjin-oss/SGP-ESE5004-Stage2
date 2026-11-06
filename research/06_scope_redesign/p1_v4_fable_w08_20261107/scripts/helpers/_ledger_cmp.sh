set -u
export PROJ_DATA=/home/jin/miniforge3/envs/pypsa-earth/share/proj PROJ_LIB=/home/jin/miniforge3/envs/pypsa-earth/share/proj
RUN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/smoke56
PY=/home/jin/miniforge3/envs/pypsa-earth/bin/python
head -3 $RUN/v4_F1/COUNTRY_COST_LEDGER.csv | cut -c1-700
echo "--- detail header"; head -2 $RUN/v4_F1/COUNTRY_COST_LEDGER_DETAIL.csv | cut -c1-500
$PY - <<PY
import pandas as pd, json, xarray as xr
pd.set_option("display.width", 260)
R = "$RUN"; OUT = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_fable_w08_20261107/evidence/SMOKE_LEDGER_CMP.json"
L = {r: pd.read_csv(f"{R}/{r}/COUNTRY_COST_LEDGER.csv") for r in ("v31_F1", "v4_F1", "v4iid_F1")}
t = L["v31_F1"]; num = [c for c in t.columns if t[c].dtype != object]
print("numeric cols:", num[:30])
idx = "country" if "country" in t.columns else t.columns[0]
res = {}
for r, d in L.items():
    g = d.groupby(idx)[num].sum(); res[r] = g
tot = pd.DataFrame({r: res[r][num].sum(axis=1) for r in res}) if len(num) > 1 else None
# pick the column that looks like the total cost
cand = [c for c in num if "total" in c.lower()] or num[:1]
col = cand[0]; print("using column:", col)
T = pd.DataFrame({r: res[r][col] for r in res}); T["d_v4_bn"] = (T["v4_F1"] - T["v31_F1"]) / 1e9; T["d_iid_bn"] = (T["v4iid_F1"] - T["v31_F1"]) / 1e9
print(T.assign(v31_bn=T["v31_F1"]/1e9, v4_bn=T["v4_F1"]/1e9)[["v31_bn", "v4_bn", "d_v4_bn", "d_iid_bn"]].round(3).to_string()); print("sum d_v4", round(T.d_v4_bn.sum(), 3), "sum d_iid", round(T.d_iid_bn.sum(), 3))
# by category columns (all numeric columns, ASEAN total)
C = pd.DataFrame({r: res[r][num].sum() for r in res}); C["d_v4_bn"] = (C["v4_F1"] - C["v31_F1"]) / 1e9; C["d_iid_bn"] = (C["v4iid_F1"] - C["v31_F1"]) / 1e9
print(C[["d_v4_bn", "d_iid_bn"]].round(3).sort_values("d_v4_bn", key=abs, ascending=False).head(25).to_string())
# detail: by category/carrier if available
D = {r: pd.read_csv(f"{R}/{r}/COUNTRY_COST_LEDGER_DETAIL.csv") for r in ("v31_F1", "v4_F1")}
d0 = D["v31_F1"]; keys = [c for c in ("category", "cost_type", "carrier", "component", "item") if c in d0.columns]; vals = [c for c in d0.columns if d0[c].dtype != object and ("eur" in c.lower() or "cost" in c.lower())]
print("detail keys", keys, "vals", vals[:6])
if keys and vals:
    k = keys[:2]; v = vals[0]
    a = D["v31_F1"].groupby(k)[v].sum(); b = D["v4_F1"].groupby(k)[v].sum()
    dd = (b - a).fillna(b).fillna(-a).dropna(); dd = pd.concat([a.rename("v31"), b.rename("v4"), dd.rename("d")], axis=1).fillna(0.0)
    dd = dd[dd.d.abs() > 2e7].sort_values("d", key=abs, ascending=False)
    print((dd / 1e9).round(3).head(40).to_string())
    res_detail = (dd / 1e9).round(4).reset_index().to_dict("records")
else:
    res_detail = None
json.dump(dict(total_col=col, by_country={r: res[r][col].to_dict() for r in res}, by_column_asean={c: dict(v31=float(C.at[c, "v31_F1"]), v4=float(C.at[c, "v4_F1"]), iid=float(C.at[c, "v4iid_F1"])) for c in C.index}, detail_top=res_detail), open(OUT, "w"), indent=1, default=str)
# CO2 constraint duals
for r in ("v31_F1", "v4_F1"):
    ds = xr.open_dataset(f"{R}/{r}/DUALS_BY_CONSTRAINT.nc")
    co2 = [v for v in ds.data_vars if "co2" in v.lower() or "carbon" in v.lower() or "emission" in v.lower()]
    print(r, "co2-like dual vars:", co2[:12])
    for v in co2[:6]:
        x = ds[v]
        print("  ", v, dict(x.sizes), "mean|dual|", float(abs(x).mean()), "max", float(abs(x).max()))
PY
