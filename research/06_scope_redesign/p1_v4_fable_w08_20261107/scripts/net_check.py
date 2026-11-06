"""Fable W08 review, dimension 6: the built v4 networks (read-only) against the v4 tables.

usage: net_check.py <network.nc> <repo> <out_dir name: out_ras|out_iid> <OUT.json>
Loads: annual energy per country x account x carrier (static p_set x 8760; time-varying sum x weighting) against INDUSTRY_2050_SUMMARY_V4 /
ATS table / PROCESS_EMISSIONS_2050_V4; curve statistics of the time-varying industrial loads; gas production annual caps (meta external_annual_caps)
against GAS_PRODUCTION_CAPS_2050_V4; solid-biomass pools against BIOMASS_POTENTIAL_2050_V4 and the 0.99 cap; rail parent absence; v4 meta.
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
import pypsa  # noqa: E402

NET, REPO, OD, OUT = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
V4 = REPO / "research_inputs/industry_v4" / OD
n = pypsa.Network(str(NET))
w = float(n.snapshot_weightings.generators.iloc[0])
res = dict(network=str(NET), snapshots=len(n.snapshots), weighting=w)
rec = json.loads((V4 / "V4_SWITCHES.json").read_text())
m = n.meta.get("v4_w08", {})
res["meta_switch_sha_equals_table_set"] = (m.get("switch_sha256") == rec["switch_sha256"])
res["meta_files_equal_table_set"] = (m.get("files") == rec["files"])
res["meta_asean_T"] = m.get("asean_T_v2_TWh")
# ---- loads: annual energy
L = n.loads.copy()
tv = set(n.loads_t.p_set.columns)
L["annual_mwh"] = [float((n.loads_t.p_set[l] * w).sum()) if l in tv else float(L.at[l, "p_set"]) * 8760.0 for l in L.index]
L["time_varying"] = [l in tv for l in L.index]
agg = L.groupby(["country", "account", "carrier"]).annual_mwh.sum()
res["loads_by_country_account_carrier_twh"] = {f"{k[0]}|{k[1]}|{k[2]}": v / 1e6 for k, v in agg.items()}
S = pd.read_csv(V4 / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
ats = pd.read_csv(V4 / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False, dtype=str)
ats["v"] = pd.to_numeric(ats.value_2050_mwh, errors="coerce").fillna(0.0)
P = pd.read_csv(V4 / "PROCESS_EMISSIONS_2050_V4.csv")
ev_factor = float(n.meta["s2_demand_ledger"]["parameters"]["ev_share"]) * float(n.meta["s2_demand_ledger"]["parameters"]["oil_to_electricity"])
res["ev_factor"] = ev_factor
cmp = []
def g(c, acc, car=None):
    z = agg.loc[c] if c in agg.index.get_level_values(0) else None
    if z is None:
        return 0.0
    z = z.loc[acc] if acc in z.index.get_level_values(0) else None
    if z is None:
        return 0.0
    return float(z.sum()) if car is None else float(z.get(car, 0.0))
for c in S.index:
    if float(S.at[c, "pe_electricity_mwh"]) == 0 and c not in set(L.country):
        continue
    ov = float(S.at[c, "biomass_overflow_industry_mwh"]) if "biomass_overflow_industry_mwh" in S.columns else 0.0
    row = dict(country=c,
               el_net=g(c, "IndustryElectricityRoutes"), el_tab=float(S.at[c, "pe_electricity_mwh"]),
               heat_net=g(c, "IndustryLowTemperatureHeat"), heat_tab=float(S.at[c, "pe_heat_mwh"]),
               heat_ma_net=g(c, "IndustryHeatMediumA"), heat_ma_tab=float(S.at[c, "pe_heat_medium_a_mwh"]),
               heat_mb_net=g(c, "IndustryHeatMediumB"), heat_mb_tab=float(S.at[c, "pe_heat_medium_b_mwh"]),
               heat_hi_net=g(c, "IndustryHeatHigh"), heat_hi_tab=float(S.at[c, "pe_heat_high_mwh"]),
               coal_net=g(c, "IndustryFinalEnergy", "coal"), coal_tab=float(S.at[c, "pe_coal_mwh"]),
               oil_net=g(c, "IndustryFinalEnergy", "oil"), oil_tab=float(S.at[c, "pe_oil_mwh"]),
               gas_net=g(c, "IndustryFinalEnergy", "gas"), gas_tab=float(S.at[c, "pe_gas_mwh"]),
               bio_net=g(c, "IndustryFinalEnergy", "biomass"), bio_tab_after_overflow=float(S.at[c, "pe_biomass_mwh"]) - ov, bio_tab_before=float(S.at[c, "pe_biomass_mwh"]), overflow_tab=ov,
               overflow_heat_net=g(c, "IndustryBiomassOverflowUsefulHeat"),
               h2_net=g(c, "IndustryHydrogenDRI"), h2_tab=float(S.at[c, "pe_hydrogen_mwh"]),
               nh3_net=g(c, "IndustryAmmonia"), nh3_tab=float(S.at[c, "pe_ammonia_mwh"]), meoh_net=g(c, "IndustryMethanol"), meoh_tab=float(S.at[c, "pe_methanol_mwh"]))
    land = ats[(ats.country == c) & (ats.sector == "Transport") & ats.account.isin(["RoadResidualFuel", "TransportNEC"]) & (ats.carrier != "electricity")].v.sum()
    row.update(ev_net=g(c, "LandTransportEV"), ev_expected=float(land) * ev_factor, rail_net=g(c, "RailNonElectric"),
               rail_tab=float(ats[(ats.country == c) & (ats.account == "RailNonElectric")].v.sum()),
               rail_parent_tab=float(ats[(ats.country == c) & (ats.account == "TransportEmbeddedFuelParent")].v.sum()),
               proc_net=float(L[(L.country == c) & (L.carrier == "process emissions")].annual_mwh.sum()), proc_tab=float(P[P.country == c].tco2_2050.sum()))
    cmp.append(row)
res["compare"] = cmp
res["loads_with_rail_parent_source"] = [l for l in L.index if "TransportEmbeddedFuelParent" in str(L.at[l, "source_account_id"])]
# ---- curves
cur = []
for acc in ("IndustryElectricityRoutes", "IndustryLowTemperatureHeat", "IndustryHeatMediumA", "IndustryHeatMediumB", "IndustryHeatHigh"):
    z = L[(L.account == acc)]
    for c, zz in z.groupby("country"):
        names = [l for l in zz.index if l in tv]
        if not names:
            cur.append(dict(account=acc, country=c, loads=len(zz), time_varying=0)); continue
        M = n.loads_t.p_set[names]
        tot = M.sum(axis=1)
        shape = tot / tot.mean()
        e_tv = float((tot * w).sum()); e_static = float(zz.loc[names, "p_set"].sum() * 8760.0)
        # same shape at every node of the country? (zones differ in ID)
        shapes = M / M.mean()
        corr_min = float(np.nanmin(np.corrcoef(shapes.T.values))) if len(names) > 1 else 1.0
        cur.append(dict(account=acc, country=c, loads=len(zz), time_varying=len(names), energy_tv_mwh=e_tv, energy_static_x8760_mwh=e_static, energy_rel_diff=(e_tv - e_static) / e_static if e_static else None,
                        peak_to_mean=float(shape.max()), min_to_mean=float(shape.min()), neg_values=int((M.values < 0).sum()), min_corr_between_nodes=corr_min))
res["curves"] = cur
led = n.meta["s2_demand_ledger"].get("industry", {})
res["industry_ledger_v4"] = led.get("v4_w08")
res["biomass_overflow_ledger"] = led.get("biomass_overflow")
# ---- gas caps
caps = pd.read_csv(REPO / "research_inputs/gas_v5/GAS_PRODUCTION_CAPS_2050_V4.csv", keep_default_na=False).set_index("country")
ext = n.meta.get("external_annual_caps", {})
gc = {}
for gname, cap in ext.items():
    if gname in n.generators.index and n.generators.at[gname, "carrier"] == "gas production":
        c = n.generators.at[gname, "country"]; gc[c] = gc.get(c, 0.0) + float(cap)
res["gas_caps_network_vs_table"] = {c: dict(network=gc.get(c, 0.0), table=float(caps.at[c, "cap_mwh_per_year"]), diff=gc.get(c, 0.0) - float(caps.at[c, "cap_mwh_per_year"])) for c in caps.index}
res["gas_caps_table_used"] = n.meta.get("research_gas_network", {}).get("production_caps_table") if isinstance(n.meta.get("research_gas_network"), dict) else None
# fugitive factors on the delivery links
fl = n.links[n.links.carrier == "gas production delivery"]
res["fugitive_links"] = {c: float(fl[fl.country == c].efficiency2.iloc[0]) for c in sorted(set(fl.country))} if "efficiency2" in fl.columns and len(fl) else None
# ---- biomass pools
bp = pd.read_csv(REPO / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv", keep_default_na=False)
bp["p"] = pd.to_numeric(bp.potential_main_mwh, errors="coerce").fillna(0.0)
solid = bp[bp.feedstock_group != "biogas"]
sb = n.stores[n.stores.carrier == "solid biomass"]
pools = {}
for c in sorted(set(solid.country)):
    pot_all = float(solid[solid.country == c].p.sum())
    pot_ok = float(solid[(solid.country == c) & ~solid.status.isin(["DATA_PENDING", "ZERO_BY_DECISION"])].p.sum())
    e = float(sb[sb.country == c].e_nom.sum())
    fixed = g(c, "IndustryFinalEnergy", "biomass") + sum(v for (cc, acc, car), v in agg.items() if cc == c and car == "biomass" and acc != "IndustryFinalEnergy")
    pools[c] = dict(store_e_nom=e, table_all_rows=pot_all, table_without_pending=pot_ok, fixed_biomass_loads=fixed, cap_099_of_store=0.99 * e, margin_vs_099=0.99 * e - fixed,
                    margin_share=(0.99 * e - fixed) / e if e else None, s30_cap_in_summary=float(S.at[c, "solid_biomass_potential_main_mwh"]) if c in S.index else None)
res["biomass_pools"] = pools
res["ev_meta"] = n.meta.get("research_ev")
json.dump(res, open(OUT, "w"), indent=1, default=float)
pd.set_option("display.width", 300)
df = pd.DataFrame(cmp).set_index("country")
for a, b in (("el_net", "el_tab"), ("heat_net", "heat_tab"), ("heat_ma_net", "heat_ma_tab"), ("heat_mb_net", "heat_mb_tab"), ("heat_hi_net", "heat_hi_tab"), ("coal_net", "coal_tab"), ("oil_net", "oil_tab"), ("gas_net", "gas_tab"),
             ("bio_net", "bio_tab_after_overflow"), ("h2_net", "h2_tab"), ("nh3_net", "nh3_tab"), ("meoh_net", "meoh_tab"), ("ev_net", "ev_expected"), ("rail_net", "rail_tab"), ("proc_net", "proc_tab")):
    d = (df[a] - df[b]); print(f"{a:12s} vs {b:22s} max|diff| MWh {d.abs().max():.6g}  ({d.abs().idxmax()})")
print("rail parent in tables (TWh):", {c: v / 1e6 for c, v in df.rail_parent_tab.items() if v}); print("loads with rail parent source:", res["loads_with_rail_parent_source"][:5])
print("overflow heat loads (MWh):", {c: round(v, 1) for c, v in df.overflow_heat_net.items() if v}); print("overflow table (MWh):", {c: round(v, 1) for c, v in df.overflow_tab.items() if v})
print(pd.DataFrame(cur).round(4).to_string())
print("gas caps:", {c: round(v["diff"], 3) for c, v in res["gas_caps_network_vs_table"].items()}, "table used:", res["gas_caps_table_used"])
print("fugitive:", res["fugitive_links"])
print(pd.DataFrame(pools).T.round(1).to_string())
print("meta sha ok", res["meta_switch_sha_equals_table_set"], "files ok", res["meta_files_equal_table_set"])
print("curves ledger", json.dumps(res["industry_ledger_v4"], default=str)[:1500])
