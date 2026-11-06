"""V4 D1 section 4 (decision 212 (a)): scan every in-use registry row (status REGISTERED / SENSITIVITY / DATA_PENDING, W10 definition) that carries a registered
range, against hard physical bounds; write PHYSICS_BOUNDS_FIX.csv (the rows corrected by scripts_project/v4_d1_registry.py PHYSICS_FIXES, old / new range, basis,
derivation) and evidence/PHYSICS_SCAN.json (every check, its rows and result). The scan reads the registry assembled WITHOUT the D1 corrections and asserts that
the violations it finds are exactly PHYSICS_FIXES. Nothing is solved; the repository is read only.

    PYTHONHASHSEED=0 <env python> scripts/d1_physics_scan.py <repo> <delivery dir>
"""
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(sys.argv[1]); OUT = Path(sys.argv[2])
sys.path.insert(0, str(REPO / "scripts_project"))
import d1_registry as DR   # noqa: E402
import v4_d1_registry as V   # noqa: E402

base, _ = DR.assemble([c for c in DR.CORRECTIONS if c != "v4_d1_corrections"])
final = pd.read_csv(REPO / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
use = base[base.status.isin(["REGISTERED", "SENSITIVITY", "DATA_PENDING"])].copy()
rng = use[(use.sensitivity_low != "") | (use.sensitivity_high != "")].copy()
num = lambda s: pd.to_numeric(s, errors="coerce")   # noqa: E731
rng["v"], rng["lo"], rng["hi"] = num(rng.value), num(rng.sensitivity_low), num(rng.sensitivity_high)
L = V.physics_limits(base)
M = dict(V.MOLAR, CH4=V.ATOMIC["C"] + 4 * V.ATOMIC["H"])
smr_nh3_min = 0.375 * M["CH4"] / M["NH3"] * L["lhv_ch4_mwh_t"]   # CH4 + 2 H2O -> CO2 + 4 H2; 1.5 H2 per NH3 -> 0.375 CH4 per NH3 (feed only, no fuel)
checks, viol = [], {}


def check(name, rule, rows, bad):
    rows = list(rows); bad = sorted(set(bad))
    checks.append(dict(check=name, rule=rule, rows_checked=len(rows), param_ids=sorted(rows), violations=bad))
    for b in bad:
        viol.setdefault(b, []).append(name)


ends = lambda z: [(p, lo, hi) for p, lo, hi in zip(z.param_id, z.lo, z.hi)]   # noqa: E731
FRACTION_UNITS = {"fraction", "share", "p.u.", "MWh_useful/MWh_fuel"}
FRACTION_AS_IN_CONFIG = {"share_bev_dsm_restriction_value"}   # PyPSA-Eur bev_dsm_restriction_value: minimum state of charge (share)
z = rng[rng.unit.isin(FRACTION_UNITS) | rng.param_id.isin(FRACTION_AS_IN_CONFIG)]
check("fraction_or_efficiency_in_0_1", "share / efficiency endpoints in [0, 1]", z.param_id,
      [p for p, lo, hi in ends(z) if (pd.notna(lo) and not 0 <= lo <= 1) or (pd.notna(hi) and not 0 <= hi <= 1)])
check("no_negative_endpoint", "energy, mass, emission, capacity, cost, length, time endpoints >= 0 (every in-use range)", rng.param_id,
      [p for p, lo, hi in ends(rng) if (pd.notna(lo) and lo < 0) or (pd.notna(hi) and hi < 0)])
st = {"share_MWh_MeOH_per_tCO2": ("hi", L["meoh_per_tco2_max"]), "share_MWh_MeOH_per_MWh_H2": ("hi", L["meoh_per_mwh_h2_max"]),
      "share_MWh_H2_per_tNH3_electrolysis": ("lo", L["h2_per_tnh3_min"]), "industry_ammonia_feedstock_gas_per_t": ("lo", smr_nh3_min)}
z = rng[rng.param_id.isin(st)]
check("stoichiometry", "MeOH per t CO2 and per MWh H2 <= CO2 + 3 H2 -> CH3OH + H2O; H2 per t NH3 >= N2 + 3 H2 -> 2 NH3; CH4 feed per t NH3 (SMR) >= 0.375 mol CH4 per mol NH3",
      z.param_id, [p for p, lo, hi in ends(z) if (st[p][0] == "hi" and hi > st[p][1] + 1e-9) or (st[p][0] == "lo" and lo < st[p][1] - 1e-9)])
PURE = {"share_MWh_NH3_per_tNH3", "liquid_ship_mwh_per_t_ammonia", "liquid_ship_mwh_per_t_methanol"}
z = rng[rng.unit.isin(["MWh/t", "GJ/t", "MWh/bbl", "as in config"]) & rng.param_id.isin(PURE)]
check("pure_substance_heating_value", "the heating value of a pure substance (ammonia, methanol) has no range", z.param_id, [p for p, lo, hi in ends(z) if lo != hi])
hc = {"liquid_ship_mwh_per_t_oil": L["lhv_ch4_mwh_t"], "conv_gj_per_t_natural_gas_mass": L["lhv_ch4_gj_t"], "conv_gj_per_t_crude_ncv": L["lhv_ch4_gj_t"],
      "fuel_price_mwh_per_bbl_crude_ncv": None, "conv_gj_per_t_msw_biomass_fraction": None}
z = rng[rng.param_id.isin(hc)]
check("hydrocarbon_heating_value_below_methane", "LHV per mass of any hydrocarbon mixture <= LHV of methane (50.04 GJ/t, registry biomass_methane_lhv)",
      z.param_id, [p for p, lo, hi in ends(z) if hc[p] is not None and hi > hc[p] + 1e-9])
z = rng[rng.unit == "h/a"]
check("hours_per_year", "operating hours per year <= 8,760", z.param_id, [p for p, lo, hi in ends(z) if hi > 8760])
z = rng[rng.unit.isin(["%/a", "% capital cost"])]
check("percent_in_0_100", "percentages in [0, 100]", z.param_id, [p for p, lo, hi in ends(z) if not (0 <= lo <= 100 and 0 <= hi <= 100)])
z = rng[rng.unit == "real rate"]
check("real_rate_above_minus_one", "real discount rate > -1", z.param_id, [p for p, lo, hi in ends(z) if lo <= -1])
fixes = {f[0] for f in V.PHYSICS_FIXES}
assert set(viol) == fixes, (sorted(set(viol) - fixes), sorted(fixes - set(viol)))
corr, log = V.physics_corrections(base)
rows = []
for x in log:
    p = x["param_id"]
    der = {"share_MWh_MeOH_per_tCO2": f"32.042 / 44.009 x {L['lhv_meoh_mwh_t']} MWh/t = {L['meoh_per_tco2_max']:.9g}",
           "share_MWh_MeOH_per_MWh_H2": f"32.042 x {L['lhv_meoh_mwh_t']} / (3 x 2.016 x {L['lhv_h2_mwh_t']}) = {L['meoh_per_mwh_h2_max']:.9g}",
           "share_MWh_H2_per_tNH3_electrolysis": f"1.5 x 2.016 / 17.031 x {L['lhv_h2_mwh_t']} = {L['h2_per_tnh3_min']:.9g}",
           "liquid_ship_mwh_per_t_oil": f"{L['lhv_ch4_gj_t']} GJ/t / 3.6 = {L['lhv_ch4_mwh_t']:.9g}", "conv_gj_per_t_natural_gas_mass": f"{L['lhv_ch4_gj_t']} GJ/t"}.get(p, "")
    rows.append(dict(param_id=p, unit=x["unit"], value=x["value"], old_low=x["old_low"], old_high=x["old_high"], new_low=x["new_low"], new_high=x["new_high"],
                     violation_class=x["cls"], basis=x["basis"], derivation=der, main_value_note=x["main_value_note"], checks=";".join(viol[p]),
                     registry_tier=base.set_index("param_id").at[p, "tier"], status="EXACT (bound) / VERIFIED (registry rows)",
                     final_registry_low=final.at[p, "sensitivity_low"], final_registry_high=final.at[p, "sensitivity_high"]))
fix = pd.DataFrame(rows)
assert (fix.final_registry_low == fix.new_low).all() and (fix.final_registry_high == fix.new_high).all(), "DATA_REGISTRY.csv does not carry the corrections"
fix.to_csv(OUT / "PHYSICS_BOUNDS_FIX.csv", index=False, lineterminator="\n")
outside = rng[(rng.lo > rng.v) | (rng.hi < rng.v)]
(OUT / "evidence").mkdir(exist_ok=True)
json.dump(dict(in_use_rows=int(len(use)), rows_with_range=int(len(rng)), units=rng.unit.value_counts().to_dict(), limits={k: v for k, v in L.items()},
               smr_ammonia_ch4_feed_min_mwh_per_t=smr_nh3_min, atomic_weights=V.ATOMIC, checks=checks, violations=viol, corrected=sorted(fixes),
               h2_lhv_sensitivity={str(h): dict(meoh_per_mwh_h2_max=M["MeOH"] * L["lhv_meoh_mwh_t"] / (3 * M["H2"] * h), h2_per_tnh3_min=1.5 * M["H2"] / M["NH3"] * h)
                                   for h in (33.33, 120.0 / 3.6, 119.96 / 3.6)},
               not_physics_value_outside_range=[dict(param_id=r.param_id, unit=r.unit, value=r.value, low=r.sensitivity_low, high=r.sensitivity_high) for r in outside.itertuples()],
               note="value_outside_range rows are alternative-method ranges (demand multipliers, calibration factors, process emissions); not a physical bound; not changed"),
          open(OUT / "evidence/PHYSICS_SCAN.json", "w"), indent=1, default=float)
print(fix[["param_id", "old_low", "old_high", "new_low", "new_high", "violation_class"]].to_string(index=False))
print("checks:", [(c["check"], c["rows_checked"], len(c["violations"])) for c in checks])
print("SMR NH3 CH4 feed minimum", smr_nh3_min, "; value outside range (not physics):", len(outside))
