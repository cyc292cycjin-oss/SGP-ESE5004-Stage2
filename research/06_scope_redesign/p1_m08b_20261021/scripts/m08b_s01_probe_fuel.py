"""M08b supplement 01 probe (read-only): residential / commercial / agriculture fuel anchors = ATS sector TFEC anchor - sector electricity anchor."""
import sys
import pandas as pd

sys.path.insert(0, "/home/jin/wt_m08b_20261021/scripts_project")
from m08b_demand import RATIO_TABLE, SECTORS, RES_ELEC_ATS_MTOE, aeo8_country, c3_ats   # noqa: E402
from d1_common import ASEAN   # noqa: E402

pd.set_option("display.width", 260); pd.set_option("display.max_rows", 400)
dem = pd.read_csv(RATIO_TABLE, dtype=str, keep_default_na=False)
base = pd.to_numeric(dem.base_2019_mwh, errors="coerce").fillna(0.0)
v50 = pd.to_numeric(dem.value_2050_mwh, errors="coerce").fillna(0.0)
a8 = aeo8_country(); c3 = c3_ats()
g_el = {s: c3[s][1] / c3[s][0] for s in SECTORS}; g_el["Residential"] = RES_ELEC_ATS_MTOE[1] / RES_ELEC_ATS_MTOE[0]
g_t = {s: c3[s][1] / c3[s][0] for s in SECTORS}
print("g_el", {k: round(v, 4) for k, v in g_el.items()}); print("g_tfec", {k: round(v, 4) for k, v in g_t.items()})
is_el = dem.carrier == "electricity"
rows = []
for c in ASEAN:
    m = dem.country == c
    A_el = a8[c]["elec_pc_kwh"] * a8[c]["pop_2050_million"] * 1e3
    A_t = a8[c]["tfec_pc_kgoe"] * a8[c]["pop_2050_million"] * 1e3 * 11.63
    el19 = {s: float(base[m & is_el & (dem.sector == s)].sum()) for s in SECTORS}
    w = {s: el19[s] * g_el[s] for s in SECTORS}; W = sum(w.values())
    t19 = {s: float(base[m & (dem.sector == s)].sum()) for s in SECTORS}; t19["Industry"] += float(base[m & (dem.sector == "NonEnergyUse")].sum())
    wt = {s: t19[s] * g_t[s] for s in SECTORS}; WT = sum(wt.values())
    for s in ("Residential", "Commercial", "AgricultureOthers"):
        tf = A_t * wt[s] / WT; el = A_el * w[s] / W
        fb = float(base[m & (dem.sector == s) & ~is_el].sum()); fr = float(v50[m & (dem.sector == s) & ~is_el].sum())
        mult = dem[m & (dem.sector == s) & ~is_el].multiplier_total.unique()
        rows.append(dict(country=c, sector=s, tfec_anchor_twh=tf / 1e6, elec_anchor_twh=el / 1e6, fuel_anchor_twh=(tf - el) / 1e6, fuel_2019_twh=fb / 1e6,
                         fuel_ratio_2050_twh=fr / 1e6, mult_anchor=(tf - el) / fb if fb > 0 else float("nan"), n_mult_ratio=len(mult)))
r = pd.DataFrame(rows)
print(r.round(3).to_string(index=False))
print("negatives:", r[r.fuel_anchor_twh < 0][["country", "sector", "fuel_anchor_twh"]].to_string(index=False))
print(r.groupby("sector")[["tfec_anchor_twh", "elec_anchor_twh", "fuel_anchor_twh", "fuel_2019_twh", "fuel_ratio_2050_twh"]].sum().round(1).to_string())
sub = dem[dem.sector.isin(["Residential", "Commercial", "AgricultureOthers"]) & ~is_el]
print(sub.groupby(["sector", "carrier", "account"]).size().to_string())
print(sub[sub.country == "VN"][["sector", "carrier", "account", "base_2019_mwh", "value_2050_mwh", "multiplier_total", "country_multiplier", "sector_calibration_k"]].to_string())
tr = dem[(dem.sector == "Transport") & is_el]
print(tr.groupby(["account"]).size().to_string(), float(pd.to_numeric(tr.base_2019_mwh, errors="coerce").fillna(0).sum()) / 1e6)
