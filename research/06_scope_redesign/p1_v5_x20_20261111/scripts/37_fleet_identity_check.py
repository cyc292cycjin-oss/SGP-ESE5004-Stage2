"""X20 ②5：只读核对 s4a_2_fleet_data 的"网络已有"身份集合（不加载网络数组，只读 netCDF 的 meta 属性）。
电力底座 existing_unit_components 的身份数与 GEM ID 数；S1 存活 JSON 中地热记录的 AssetID、状态与投运年；二者并集是否等于 S4A 报告的 748 / 745。"""
import json
import sys
from pathlib import Path

import netCDF4

MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
EB = MAIN / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc"
S1 = MAIN / "results_project/s1/S1_SELECTED_ASSET_SURVIVAL_2050.json"
ds = netCDF4.Dataset(EB)
meta = json.loads(ds.getncattr("meta")); ds.close()
ids = meta["existing_unit_components"]
gem = [k for k in ids if k.startswith("GEM:")]
print("electric base", EB.stat().st_size, "B; identities", len(ids), "GEM", len(gem))
S = json.loads(S1.read_text())
rec = [r for r in S["unit_evidence"]["records"] if r.get("Technology") == "Geothermal"]
print("S1 geothermal records", len(rec), "status counts", {s: sum(r["SurvivalStatus"] == s for r in rec) for s in sorted({r["SurvivalStatus"] for r in rec})})
surv = [r for r in rec if r["SurvivalStatus"] == "SURVIVES_2050"]
print("S1 geothermal SURVIVES_2050", len(surv), sum(float(r["OriginalCapacity"]) for r in surv), "MW; AssetID sample", [r["AssetID"] for r in rec[:5]])
print("S1 geothermal AssetIDs in electric base identities:", sum(r["AssetID"] in ids for r in rec))
print("union size (base + surviving S1 geothermal):", len(set(ids) | {r["AssetID"] for r in surv}), "GEM:", len({k for k in set(ids) | {r["AssetID"] for r in surv} if k.startswith("GEM:")}))
# 40 a / inclusive 时存活的 S1 地热（与 s2_layers 的 v5 重判一致）
for life, incl in ((30, False), (40, True)):
    s = [r for r in rec if r.get("CommissioningYear") not in (None, "") and (float(r["CommissioningYear"]) + life >= 2050 if incl else float(r["CommissioningYear"]) + life > 2050)]
    print(f"life {life} inclusive {incl}: S1 geothermal in service", len(s), round(sum(float(r["OriginalCapacity"]) for r in s), 1), "MW",
          "by country", {c: round(sum(float(r["OriginalCapacity"]) for r in s if r["Country"] == c), 1) for c in sorted({r["Country"] for r in s})})
sys.stdout.flush()
