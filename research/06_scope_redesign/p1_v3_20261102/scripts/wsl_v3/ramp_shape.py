"""V3 1.2 item 6 / design 165: RAMP EV - DST check, seasonality, weekday pattern, weekly local-time shape, energy per plugged capacity. Read only."""
import pandas as pd, numpy as np, json
from pathlib import Path
SRC = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102/04_ev")
OUT = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/phase1")
c = pd.read_csv(SRC / "ramp-ev-consumption-profiles.csv.gz"); c = c[c.year == 2013]; c["t"] = pd.to_datetime(c.datetime, utc=True)
p = pd.read_csv(SRC / "ramp-ev-plugin-profiles.csv.gz"); p = p[p.year == 2013]; p["t"] = pd.to_datetime(p.datetime, utc=True)
C = c.pivot(index="t", columns="country_code", values="demand"); P = p.pivot(index="t", columns="country_code", values="plugin")
print(C.shape, C.index[0], C.index[-1], C.isna().sum().sum())
for k in ["DEU", "ESP", "GBR", "ITA", "PRT", "NOR"]:
    ja = C[k][C.index.month == 1]; ju = C[k][C.index.month == 7]
    print(k, "peak UTC Jan", int(ja.groupby(ja.index.hour).mean().idxmax()), "Jul", int(ju.groupby(ju.index.hour).mean().idxmax()), "trough Jan", int(ja.groupby(ja.index.hour).mean().idxmin()), "Jul", int(ju.groupby(ju.index.hour).mean().idxmin()))
m = C.resample("MS").sum(); m = m / m.mean(); print("monthly/mean range", m.min().round(3).to_dict()); print(m.max().round(3).to_dict())
print("annual sum", (C.sum() / 1e6).round(1).to_dict())
print("weekday energy ratio (Mon..Sun, mean of 26 countries)", (C.groupby(C.index.dayofweek).mean().div(C.mean()).mean(axis=1)).round(3).to_dict())
print("plug mean", P.mean().round(3).to_dict())
print("peak/mean consumption (hourly)", (C.max() / C.mean()).round(2).to_dict())
dm = C.groupby(C.index.hour).mean(); print("diurnal peak/mean", (dm.max() / dm.mean()).round(2).to_dict())
# 3h average peak / mean of the mean diurnal curve, 26-country average in UTC
print("corr of diurnal shape with DEU", dm.corrwith(dm["DEU"]).round(3).to_dict())
