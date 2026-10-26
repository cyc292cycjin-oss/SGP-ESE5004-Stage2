"""DFX v3 phase 1 report facts (read-only): RAS, anchors, ammonia, NEU gas deduction / truncation, registry counts, changelog counts, test counts."""
import csv
import json
from pathlib import Path

import pandas as pd

WT = Path("/home/jin/wt_dfx_v3_20261026"); DEM = WT / "research_inputs/demand_v5"; REG = WT / "research_inputs/registry_v5"
ev = json.loads((DEM / "DEMAND_ANCHOR_M08B_EVIDENCE.json").read_text())
ras = ev.get("ras", {}); print("RAS:", {k: ras.get(k) for k in ("k_scale", "iterations", "row_error", "col_error", "converged", "max_row_rel_error", "max_col_rel_error")})
print("RAS keys:", list(ras.keys())[:20])
print("ammonia:", json.dumps(ev.get("ammonia", {}))[:1200]); print("neu:", json.dumps(ev.get("neu", {}))[:800])
an = pd.read_csv(DEM / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
cols = [c for c in an.columns if any(k in c for k in ("ras_sector_anchor", "ammonia", "neu_", "industry_multiplier", "fuel_zeroed", "neu_multiplier"))]
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print((an[[c for c in cols if "mwh" in c or "_t" in c]] / 1).round(0).to_string())
print(an[[c for c in cols if "mwh" not in c and "_t" not in c]].to_string())
print("sector anchor sums TWh:", {s: round(an[f"ras_sector_anchor_{s}_mwh"].sum() / 1e6, 1) for s in ("Industry", "Transport", "Residential", "Commercial", "AgricultureOthers")})
print("ammonia total t:", an["ammonia_2050_t"].sum(), "deduction TWh:", an["ammonia_feedstock_gas_deduction_mwh"].sum() / 1e6, "truncated TWh:", an["ammonia_feedstock_gas_truncated_mwh"].sum() / 1e6)
reg = list(csv.DictReader(open(REG / "DATA_REGISTRY.csv"))); print("registry rows:", len(reg))
ch = list(csv.DictReader(open(REG / "REGISTRY_CHANGELOG_DFX.csv"))); print("changelog rows:", len(ch), "by reason/kind:", pd.Series([r.get("kind") or r.get("change") or r.get("reason", "")[:20] for r in ch]).value_counts().to_dict())
print("changelog cols:", list(ch[0].keys()))
mp = list(csv.DictReader(open(REG / "REGISTRY_NETWORK_INPUT_MAP.csv"))); print("map rows:", len(mp), "cols:", list(mp[0].keys())[:8])
import subprocess
print("test functions:", subprocess.run(["grep", "-c", "^def test_", str(WT / "tests/research/test_dfx_demand.py")], capture_output=True, text=True).stdout.strip(), "+", subprocess.run(["grep", "-c", "^def test_", str(WT / "tests/research/test_dfx_runner.py")], capture_output=True, text=True).stdout.strip())
print("sha registry:", subprocess.run(["sha256sum", str(REG / "DATA_REGISTRY.csv")], capture_output=True, text=True).stdout.split()[0])
