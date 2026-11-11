"""X20 §3 第 6 步的内存门估计（只读，不加载网络）：估计峰值 = D2c 同构 56 时段冒烟实测峰值 x（v5 主集 / v5off 的随时段组件数之比，取 >= 1），
组件 = Generator + Link + Line + StorageUnit + Store + Load（56 时段的 LP 列与行近似与其成正比；v5off = W14 数据 = D2c 网络数据，evidence/V5OFF_VS_W14_*.json）。
用法：python 69a_peak_estimate.py   输出 evidence/SMOKE56_PEAK_ESTIMATE.json"""
import json
import math
from pathlib import Path

import netCDF4

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
RP = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d2c/smoke56")
DIMS = ("generators_i", "links_i", "lines_i", "storage_units_i", "stores_i", "loads_i")
out = {}
for tag, sub in (("F1", "integrated/integrated_2920_3h_unsolved.nc"), ("F2", "no_new_xb/no_new_xb_2920_3h_unsolved.nc")):
    cnt = {}
    for lab in ("v5main", "v5off"):
        ds = netCDF4.Dataset(str(D / "builds" / lab / sub)); cnt[lab] = {d: (len(ds.dimensions[d]) if d in ds.dimensions else 0) for d in DIMS}; ds.close()
    t5, t0 = sum(cnt["v5main"].values()), sum(cnt["v5off"].values())
    peak = json.loads((RP / f"v4d2c_{tag}" / "SOLVE_RECEIPT.json").read_text())["peak_rss_bytes"]
    ratio = max(1.0, t5 / t0)
    out[tag] = dict(counts=cnt, total_v5main=t5, total_v5off=t0, ratio=t5 / t0, ratio_used=ratio, d2c_peak_rss_bytes=peak, d2c_peak_mib=peak / 2**20,
                    estimated_peak_mib=math.ceil(peak * ratio / 2**20), gate_needs_available_mib=math.ceil(peak * ratio / 2**20) + 2048)
(D / "evidence/SMOKE56_PEAK_ESTIMATE.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps({k: {kk: v[kk] for kk in ("total_v5main", "total_v5off", "ratio", "d2c_peak_mib", "estimated_peak_mib", "gate_needs_available_mib")} for k, v in out.items()}, indent=1))
