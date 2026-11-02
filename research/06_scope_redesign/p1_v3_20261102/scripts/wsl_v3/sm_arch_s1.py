"""Supplement 01: archive the small results of the four smoke runs in the deliverable folder (no logs, no LP or solution arrays) and write the derived evidence tables of the report."""
import json, shutil
from pathlib import Path
import netCDF4 as nc
import pandas as pd
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
W = Path("/home/jin/wt_v3_20261102"); D = W / "research/06_scope_redesign/p1_v3_20261102"; E = D / "evidence/smoke_s1"; R = M / "v3/smoke_s1"
RUNS = ["integrated", "no_new_xb", "integrated_flat", "no_new_xb_flat"]
for s in RUNS:
    (E / s).mkdir(exist_ok=True)
    for f in ("SOLVE_RECEIPT.json", "V5_GATES.json", "V6_ACCEPTANCE.json", "PRECISION.json", "LEDGER_IDENTITY.json", "STOP_CLASS.json", "COUNTRY_COST_LEDGER.csv", "ALLOCATION.csv"):
        if (R / s / f).exists():
            shutil.copy2(R / s / f, E / s / f)
for f in ("STATUS.txt", "BATCH_REFERENCE.json", "BATCH_REFERENCE_FLAT.json"):
    shutil.copy2(R / f, E / f)
shutil.copy2(R / "M12_BENEFIT/BENEFIT.csv", E / "BENEFIT.csv"); shutil.copy2(R / "M12_BENEFIT_FLAT/BENEFIT.csv", E / "BENEFIT_FLAT.csv")
T = pd.read_csv(E / "COST_BY_CARRIER_V2_FLAT_E2.csv", index_col=0)
G = {"solar": ["G solar"], "wind": ["G offwind-dc", "G onwind", "G offwind-float", "G offwind-ac"], "gas power and gas fuels": ["L CCGT CC", "L CCGT", "L OCGT", "L CCGT existing", "L OCGT existing", "G LNG import", "G gas production"],
     "co2 sequestration": ["S co2 sequestered"], "electrolysis": ["L H2 Electrolysis"], "hydro": ["U hydro", "G ror"], "DAC": ["L DAC"]}
used = sum(G.values(), [])
rows = {k: T.reindex(v).fillna(0.0)[["ev_int", "ev_nnx", "rest"]].sum() for k, v in G.items()}; rows["other"] = T.drop(index=[x for x in used if x in T.index])[["ev_int", "ev_nnx", "rest"]].sum()
g = pd.DataFrame(rows).T; g.loc["total"] = g.sum(); g.round(6).rename_axis("group").to_csv(E / "EV_EFFECT_GROUPED_BN.csv")
d = pd.read_csv(D / "DEMAND_DIFF_V3_V2.csv"); vn = d[(d.country == "VN") & (d.sector == "Industry")]
c = vn.groupby("carrier")[["twh_v2", "twh_v3", "delta_twh"]].sum()
with nc.Dataset(R / "integrated/integrated_SMOKE_TEST_ONLY_solved.nc") as ds:
    led = json.loads(ds.getncattr("meta"))["s2_demand_ledger"]["industry"]["biomass_overflow"]["VN"]
uh = led["useful_heat_mwh"]; add = {"industry heat high": uh["high"], "industry heat medium A": uh["medium_a"], "industry heat medium B": uh["medium_b"], "biomass final energy": -led["overflow_industry_mwh"]}
c["twh_v3_network"] = c.twh_v3 + pd.Series(add).div(1e6).reindex(c.index).fillna(0.0)
c.round(4).to_csv(E / "VN_INDUSTRY_CARRIERS_V2_V3.csv")
vn.groupby("subsector")[["twh_v2", "twh_v3", "delta_twh"]].sum().round(4).to_csv(E / "VN_INDUSTRY_SUBSECTORS_V2_V3.csv")
pot = pd.read_csv(W / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv"); pot = pot[pot.country == "VN"]
res = dict(overflow_ledger=led, registered_potential_twh=(pot.groupby("feedstock_group").potential_main_mwh.sum() / 1e6).to_dict(), runs={})
for s in RUNS:
    b = json.loads((R / s / "V5_GATES.json").read_text())["B3"]; r = pd.DataFrame(b["rows"]); x = r[r.country == "VN"]
    res["runs"][s] = dict(b3_passed=b["passed"], failed_stores=r[~r.within | r.refilled].store.tolist(), vn_potential_twh=x.potential_mwh.sum() / 1e6, vn_used_twh=x.used_mwh.sum() / 1e6, vn_max_excess_mwh=float((x.used_mwh - x.potential_mwh).max()), all_max_excess_mwh=float((r.used_mwh - r.potential_mwh).max()))
(E / "VN_BIOMASS_BALANCE.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + "\n")
print(c.round(2).to_string()); print(c.sum().round(2).to_dict()); print(json.dumps(res["runs"], indent=0)[:1100]); print(g.round(3).to_string())
print(sorted(p.name for p in E.iterdir()))
