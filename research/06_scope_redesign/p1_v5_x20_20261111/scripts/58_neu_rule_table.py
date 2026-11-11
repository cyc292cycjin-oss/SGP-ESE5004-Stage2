"""X20 ②4：逐国对照表 NEU_GAS_PRODUCT_RULE_V5.csv（规格 §1.11 第 4 条）：m08b 产品规则记录（D 盘 v4work/v5 的 m08b 证据）+ out_ras / out_ras_v5 的 NEU 天然气 2050 值。"""
import glob
import json
from pathlib import Path

import pandas as pd

R = Path("/home/jin/wt_v5_x20/research_inputs/industry_v4")
D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
ev = [json.loads(Path(p).read_text()) for p in glob.glob(str(D / "v4work/v5/m08b_*/DEMAND_ANCHOR_M08B_EVIDENCE.json"))]
ev = [e for e in ev if "v5_x20_neu_gas_product" in e]
assert len(ev) == 1, len(ev)
rule = pd.DataFrame(ev[0]["v5_x20_neu_gas_product"]["countries"]).set_index("country")
acc = "NonEnergy:Natural gas (including LNG)"
def neu(folder):
    d = pd.read_csv(R / folder / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv")
    g = d[(d.sector == "NonEnergyUse") & (d.carrier == "gas") & (d.account == acc)]
    return pd.to_numeric(g.value_2050_mwh, errors="coerce").fillna(0).groupby(g.country).sum()
t = rule[["neu_gas_2019_mwh", "ammonia_2019_t", "ammonia_part_2019_mwh", "methanol_part_2019_mwh", "residual_2019_mwh", "ammonia_growth", "neu_multiplier",
          "neu_gas_2050_product_rule_mwh"]].copy()
t["neu_gas_2050_v4_mwh"] = neu("out_ras").reindex(t.index).fillna(0); t["neu_gas_2050_v5_mwh"] = neu("out_ras_v5").reindex(t.index).fillna(0)
t["change_twh"] = (t.neu_gas_2050_v5_mwh - t.neu_gas_2050_v4_mwh) / 1e6
t = t[(t.neu_gas_2019_mwh > 0) | (t.neu_gas_2050_v4_mwh > 0)]
t.reset_index().to_csv(D / "evidence/NEU_GAS_PRODUCT_RULE_V5.csv", index=False, lineterminator="\n")
pd.set_option("display.width", 250)
print((t.drop(columns=["ammonia_growth", "neu_multiplier", "ammonia_2019_t"]) / 1e6).round(3).join(t[["ammonia_growth", "neu_multiplier"]].round(4)).to_string())
