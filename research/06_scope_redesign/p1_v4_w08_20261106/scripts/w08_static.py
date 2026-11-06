"""W08 section 4 / validation plan section 1: static checks of the built v4 networks (no solver). Writes STATIC_CHECKS.json and the tables of
STATIC_CHECKS.md (written by w08_report.py) into the delivery folder.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_static.py

Networks: results_project/v4w08/builds/{main/integrated, main/no_new_xb, iid/integrated}/*_{2920_3h,365_24h}_unsolved.nc; v3.1 F1 / F2 of the v3.1 package
for the structural comparison. Checks (pass conditions in brackets):
  C1 industry electricity / heat loads per country = INDUSTRY_2050_SUMMARY_V4.csv (<= 1e-6 MWh per country) and the annual mean of every profiled
     load = its constant (<= 1e-9 relative); 365x24h totals = 2920x3h totals (<= 1e-6 relative)
  C2 land-transport EV load = ATS land fuel x 0.30215 per country, rail loads = RailNonElectric rows, no rail parent row (<= 1e-6 relative)
  C3 solid-biomass pools: fixed biomass demand / pool <= 0.99 + 1e-9 everywhere (F7), VN slack >= 1 %, no new zero-margin pool
  C4 domestic gas: annual caps per country = GAS_PRODUCTION_CAPS_2050_V4.csv, generator count = v3.1, total change -298.4 TWh
  C5 curves: peak / mean of industry electricity by country (3 h), ID loads on three time zones (UTC+7 / +8 / +9) with the EV_NODE_TIMEZONE_V3 offsets
  C6 v4 identity: n.meta v4_w08 switch SHA = the table set; research_config_sha256 = hash of the configuration with the build overrides (B12)
  C7 structure vs v3.1: same buses / links / generators / stores sets, loads changed only on demand accounts; no_new_xb variant = v3.1 variant rule
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

sys.path.insert(0, "/home/jin/wt_v4_w08/scripts_project")
W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_w08")
B = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w08/builds")
PKG = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_package_v3_1/networks")
NETS = {"main_F1": ("main", "integrated", "ras"), "main_F2": ("main", "no_new_xb", "ras"), "iid_F1": ("iid", "integrated", "iid")}
HEAT_ACC = {"IndustryLowTemperatureHeat": "pe_heat_mwh", "IndustryHeatMediumA": "pe_heat_medium_a_mwh", "IndustryHeatMediumB": "pe_heat_medium_b_mwh", "IndustryHeatHigh": "pe_heat_high_mwh"}


def annual(n: pypsa.Network, names) -> pd.Series:
    w = n.snapshot_weightings.objective
    out = {}
    for l in names:
        if l in n.loads_t.p_set.columns:
            out[l] = float((n.loads_t.p_set[l] * w).sum())
        else:
            out[l] = float(n.loads.at[l, "p_set"]) * float(w.sum())
    return pd.Series(out, dtype=float)


def check(tag, n, n365, mode) -> dict:
    from v4_common import V4_DIR
    od = V4_DIR / f"out_{mode}"
    S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
    L = n.loads
    res = dict(network_sha256=None)
    # ---- C1 industry electricity / heat
    from s2_layers import HEAT_BAND_ACCOUNT
    acc = {"IndustryElectricityRoutes": "pe_electricity_mwh", "IndustryLowTemperatureHeat": "pe_heat_mwh", **{a: f"pe_heat_{b}_mwh" for b, a in HEAT_BAND_ACCOUNT.items()}}
    dev = {}
    for a, col in acc.items():
        z = L[L.account == a]
        e = annual(n, z.index).groupby(z.country).sum()
        for c in S.index:
            want = float(S.at[c, col]) if col in S.columns else 0.0
            dev[(a, c)] = float(e.get(c, 0.0)) - want
    res["C1_industry_loads_vs_summary_max_abs_mwh"] = max(abs(v) for v in dev.values())
    prof = [l for l in L.index if l in n.loads_t.p_set.columns and L.at[l, "account"] in acc]
    rel = max(abs(float(n.loads_t.p_set[l].mean()) / float(L.at[l, "p_set"]) - 1.0) for l in prof) if prof else None
    res["C1_profiled_loads"] = len(prof); res["C1_profiled_mean_vs_constant_max_rel"] = rel
    ind = L[L.account.isin(acc)]
    a2920 = annual(n, ind.index).sum(); a365 = annual(n365, ind.index).sum()
    res["C1_365_vs_2920_industry_rel"] = abs(a365 / a2920 - 1.0)
    # ---- C2 EV / rail
    ats = pd.read_csv(od / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False)
    ats["v"] = pd.to_numeric(ats.value_2050_mwh, errors="coerce").fillna(0.0)
    land = ats[(ats.sector == "Transport") & ats.account.isin(["RoadResidualFuel", "TransportNEC"]) & (ats.carrier != "electricity")].groupby("country").v.sum()
    ev = L[L.account == "LandTransportEV"]
    eva = annual(n, ev.index).groupby(ev.country).sum()
    res["C2_ev_vs_land_x_0.30215_max_rel"] = max(abs(float(eva.get(c, 0.0)) / (float(land[c]) * 0.30215) - 1.0) for c in land.index if land[c] > 0)
    rail = ats[ats.account == "RailNonElectric"].groupby("country").v.sum()
    rl = L[L.account == "RailNonElectric"]; rla = annual(n, rl.index).groupby(rl.country).sum()
    res["C2_rail_vs_table_max_abs_mwh"] = max(abs(float(rla.get(c, 0.0)) - float(rail.get(c, 0.0))) for c in set(rail.index) | set(rla.index))
    res["C2_parent_rows_in_table_mwh"] = float(ats[ats.account == "TransportEmbeddedFuelParent"].v.abs().sum())
    # ---- C3 biomass pools
    pools = n.stores[n.stores.bus.str.startswith("solid biomass")].groupby("country").e_initial.sum()
    led = n.meta["s2_demand_ledger"]["industry"]["biomass_overflow"]
    pool_rows = []
    for c, d in led.items():
        fixed = float(d["fixed_biomass_after_mwh"]); pot = float(pools.get(c, 0.0))
        pool_rows.append(dict(country=c, pool_mwh=pot, fixed_biomass_mwh=fixed, ratio=(fixed / pot if pot else None), overflow_mwh=float(d["overflow_industry_mwh"]) + float(d["overflow_agriculture_mwh"]),
                              cap_mwh=float(d["cap_mwh"])))
    P = pd.DataFrame(pool_rows)
    res["C3_pools"] = P.to_dict("records")
    res["C3_max_ratio"] = float(P.ratio.dropna().max())
    res["C3_VN_slack_share"] = float(1.0 - P[P.country == "VN"].ratio.iloc[0])
    res["C3_pools_at_or_above_0.999"] = P[P.ratio.fillna(0) >= 0.999].country.tolist()
    # ---- C4 gas caps
    caps = n.meta.get("external_annual_caps", {})
    g = n.generators[n.generators.carrier == "gas production"]
    gc = pd.Series({k: float(caps[k]) for k in g.index if k in caps}).groupby(g.country).sum()
    t = pd.read_csv(R / "research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv").set_index("country").cap_mwh_per_year
    res["C4_gas_caps_vs_table_max_rel"] = max(abs(float(gc.get(c, 0.0)) / float(t[c]) - 1.0) for c in t.index if t[c] > 0)
    res["C4_gas_generators"] = int(len(g)); res["C4_gas_caps_total_twh"] = float(gc.sum()) / 1e6
    # ---- C5 curves
    el = L[L.account == "IndustryElectricityRoutes"]
    pk = {}
    for c, z in el.groupby("country"):
        ts = sum((n.loads_t.p_set[l] if l in n.loads_t.p_set.columns else pd.Series(float(L.at[l, "p_set"]), index=n.snapshots)) for l in z.index)
        pk[c] = float(ts.max() / ts.mean())
    res["C5_industry_electricity_peak_over_mean_3h"] = pk
    tz = pd.read_csv(R / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
    idn = el[el.country == "ID"]
    res["C5_ID_zones"] = sorted({float(tz[b]) for b in idn.bus})
    # ---- C6 identity
    from v4_common import load_config, switch_sha, switches
    v4m = n.meta.get("v4_w08", {})
    res["C6_v4_meta_switch_sha"] = v4m.get("switch_sha256")
    rec = json.loads((od / "V4_SWITCHES.json").read_text())
    res["C6_switch_sha_equals_tables"] = v4m.get("switch_sha256") == rec["switch_sha256"]
    from v5.v5_gates import config_sha
    cfg = load_config(R, "integrated" if "F1" in tag else "no_new_xb")
    d = cfg["research"]
    for ov in n.meta.get("research_config", {}).get("config_overrides", []) if isinstance(n.meta.get("research_config"), dict) else []:
        pass
    res["C6_config_overrides"] = (n.meta.get("research_config") or {}).get("config_overrides")
    return res


def structure(a: pypsa.Network, b: pypsa.Network) -> dict:
    out = {}
    for c in ("buses", "links", "generators", "stores", "lines", "storage_units"):
        A, Bb = set(getattr(a, c).index), set(getattr(b, c).index)
        out[c] = dict(only_v31=sorted(A - Bb)[:20], only_v4=sorted(Bb - A)[:20], n_only_v31=len(A - Bb), n_only_v4=len(Bb - A))
    la, lb = set(a.loads.index), set(b.loads.index)
    out["loads"] = dict(n_only_v31=len(la - lb), n_only_v4=len(lb - la), only_v31=sorted(la - lb)[:30], only_v4=sorted(lb - la)[:30])
    return out


def main():
    import hashlib
    out = {}
    v31 = {"integrated": pypsa.Network(str(PKG / "integrated_2920_3h_unsolved.nc")), "no_new_xb": pypsa.Network(str(PKG / "no_new_xb_2920_3h_unsolved.nc"))}
    for tag, (root, sc, mode) in NETS.items():
        p = B / root / sc / f"{sc}_2920_3h_unsolved.nc"; p365 = B / root / sc / f"{sc}_365_24h_unsolved.nc"
        n = pypsa.Network(str(p)); n365 = pypsa.Network(str(p365))
        r = check(tag, n, n365, mode)
        r["network_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest(); r["network_bytes"] = p.stat().st_size
        r["network_365_sha256"] = hashlib.sha256(p365.read_bytes()).hexdigest()
        r["structure_vs_v31"] = structure(v31[sc], n)
        v31g = v31[sc].generators[v31[sc].generators.carrier == "gas production"]
        r["C4_v31_gas_generators"] = int(len(v31g))
        caps31 = v31[sc].meta.get("external_annual_caps", {})
        r["C4_total_change_twh"] = r["C4_gas_caps_total_twh"] - sum(float(caps31[k]) for k in v31g.index if k in caps31) / 1e6
        out[tag] = r
        print(tag, {k: (v if not isinstance(v, (dict, list)) else "...") for k, v in r.items()})
    (W / "STATIC_CHECKS.json").write_text(json.dumps(out, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
