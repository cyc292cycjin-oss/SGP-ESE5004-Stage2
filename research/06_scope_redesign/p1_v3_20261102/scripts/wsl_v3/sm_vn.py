"""VN industry carriers v2 -> v3 (review decisions, "另"): table by carrier, the biomass overflow ledger, the biomass pool against its registered potential. Read-only, no solver."""
import json, sys
from pathlib import Path
import netCDF4 as nc
import pandas as pd
pd.set_option("display.width", 220, "display.max_columns", 40)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
W = Path("/home/jin/wt_v3_20261102"); D = W / "research/06_scope_redesign/p1_v3_20261102"
RUN = sys.argv[1] if len(sys.argv) > 1 else "v3/smoke_r2"
R = M / RUN; V2 = M / "dfx_v3/smoke_v2"


def meta(f):
    with nc.Dataset(f) as d:
        return json.loads(d.getncattr("meta"))


d = pd.read_csv(D / "DEMAND_DIFF_V3_V2.csv")
vn = d[(d.country == "VN") & (d.sector == "Industry")]
t = vn.groupby("carrier")[["twh_v2", "twh_v3", "delta_twh"]].sum()
print("VN industry table by carrier, TWh (before overflow, DEMAND_DIFF_V3_V2.csv)"); print(t.round(2).to_string()); print("sum", t.sum().round(2).to_dict())
s = vn.groupby("subsector")[["twh_v2", "twh_v3", "delta_twh"]].sum().sort_values("delta_twh"); print(s.round(2).to_string())
print("biomass final energy all sectors VN", d[(d.country == "VN") & (d.carrier == "biomass final energy")].groupby("sector")[["twh_v2", "twh_v3"]].sum().round(3).to_dict("index"))
for tag, f in (("v2", V2 / "integrated/integrated_SMOKE_TEST_ONLY_solved.nc"), ("v3", R / "integrated/integrated_SMOKE_TEST_ONLY_solved.nc")):
    m = meta(f); L = m.get("s2_demand_ledger", {}); o = (L.get("industry") or {}).get("biomass_overflow", {}).get("VN")
    print(tag, "overflow ledger VN", json.dumps(o, default=str))
for sc in ("integrated", "no_new_xb", "integrated_flat", "no_new_xb_flat"):
    p = R / sc / "V5_GATES.json"
    if not p.exists():
        continue
    g = json.loads(p.read_text())["B3"]; rows = pd.DataFrame(g["rows"])
    x = rows[rows.country == "VN"]; print(sc, "B3 passed", g["passed"], "stores", g["stores"], "failed stores", int((~rows.within | rows.refilled).sum()), "by_country VN", {k: round(v / 1e6, 4) for k, v in g["by_country"]["VN"].items()})
    print(x[["store", "category", "potential_mwh", "used_mwh", "share_used", "within", "refilled"]].round(6).to_string(index=False))
    bad = rows[~rows.within | rows.refilled]
    if len(bad):
        print("  failed:", bad[["store", "country", "potential_mwh", "used_mwh", "share_used", "within", "refilled"]].head(12).round(4).to_string(index=False))
sc = pd.read_csv(W / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv"); print(list(sc.columns)); print(sc.head(3).to_string()[:600])
v = sc[sc.country == "VN"]
print(sorted(v.columns.tolist())[:30], len(v))
for tag, f in (("v3", R / "integrated/integrated_SMOKE_TEST_ONLY_solved.nc"),):
    o = meta(f)["s2_demand_ledger"]["industry"]["biomass_overflow"]["VN"]
    print({k: o[k] for k in ("overflow_industry_mwh", "overflow_agriculture_mwh", "useful_heat_mwh", "useful_heat_efficiency", "source_band_shares", "solid_biomass_potential_mwh", "cap_mwh", "fixed_biomass_after_mwh")})
    print({c: round(x["overflow_industry_mwh"] / 1e6, 3) for c, x in meta(f)["s2_demand_ledger"]["industry"]["biomass_overflow"].items() if x.get("overflow_industry_mwh", 0) or x.get("overflow_agriculture_mwh", 0)})
