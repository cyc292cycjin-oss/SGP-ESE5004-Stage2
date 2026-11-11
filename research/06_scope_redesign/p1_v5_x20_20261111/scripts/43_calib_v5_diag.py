"""X20 ①1 诊断（不写仓库）：点位系数校准触发 alpha 越界停止（PH 0.699、VN 0.789 < 0.8）后，为决策列出完整数据。
在独立进程内临时放宽 ALPHA_BOUNDS（只影响本诊断进程），输出写 D 盘 cache/calib_v5_diag/{point,cell}：
  point = Q1 (b) 风场点位系数（WIND_GWA_FARM_POINT_FACTOR_V5.csv）；cell = Q1 (a) 对照：风场所在格点的格点系数（WIND_GWA_CELL_FACTOR_V5.nc）。"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

WT = Path("/home/jin/wt_v5_x20")
sys.path.insert(0, str(WT / "scripts_project"))
import s4b_3_wind_calibration as m   # noqa: E402

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/cache/calib_v5_diag")
EMBER = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4b_20261016/sources_s4b/ember/release_generation_yearly_global.csv"
RV = WT / "research_inputs/renewable_v5"
m.ALPHA_BOUNDS = (0.0, 10.0)   # diagnostic only: the committed rule (0.8, 1.6) is unchanged
pf = pd.read_csv(RV / "WIND_GWA_FARM_POINT_FACTOR_V5.csv")
cf = xr.open_dataarray(RV / "WIND_GWA_CELL_FACTOR_V5.nc").values
pc = pf.copy(); pc["factor_point"] = cf[pc.iy.values, pc.ix.values]
(D / "cell").mkdir(parents=True, exist_ok=True); (D / "point").mkdir(parents=True, exist_ok=True)
pc.to_csv(D / "cell" / "FACTOR_CELL_AT_FARMS.csv", index=False)
for k, p in (("point", RV / "WIND_GWA_FARM_POINT_FACTOR_V5.csv"), ("cell", D / "cell" / "FACTOR_CELL_AT_FARMS.csv")):
    sys.argv = ["s4b_3_wind_calibration.py", "--ember", EMBER, "--output", str(D / k), "--point-factor", str(p)]
    m.main()
a4 = pd.read_csv(RV / "WIND_CALIBRATION_ALPHA.csv").set_index("country")
bp = pd.read_csv(D / "point" / "WIND_CALIBRATION_ALPHA_V5.csv").set_index("country")
bc = pd.read_csv(D / "cell" / "WIND_CALIBRATION_ALPHA_V5.csv").set_index("country")
t = pd.DataFrame(dict(farms=a4.farms, farm_mw=a4.farm_capacity_mw, cf_obs=a4.cf_obs, calibrated=a4.calibrated_individually,
                      alpha_v4=a4.alpha_main, alpha_point_q1b=bp.alpha_main, alpha_cell_q1a=bc.alpha_main,
                      fpoint_w=bp.factor_point_capacity_weighted, fcell_w=bc.factor_point_capacity_weighted,
                      cf_alpha1_v4=a4.cf_model_alpha1_nrel_atb2020_4mw, cf_alpha1_point=bp.cf_model_alpha1_nrel_atb2020_4mw, cf_alpha1_cell=bc.cf_model_alpha1_nrel_atb2020_4mw))
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(t.round(4).to_string())
t.to_csv(D / "ALPHA_DIAG_V4_POINT_CELL.csv")
fp = pf.groupby("iso").factor_point.describe()[["count", "min", "50%", "max"]]
print("farm-point factor by country:"); print(fp.round(3).to_string())
for c in ("PH", "VN", "TH"):
    d = pf[pf.iso == c].sort_values("Capacity (MW)", ascending=False).head(6)
    print(c, d[["Plant / Project name", "Capacity (MW)", "gwa_point_ws100", "era5_cell_mean_ws100", "factor_point"]].round(3).to_string(index=False))
